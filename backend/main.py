from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:5173",  # React default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure generated_images directory exists
generated_images_dir = os.path.join(os.getcwd(), "generated_images")
os.makedirs(generated_images_dir, exist_ok=True)

# Mount the directory to serve images statically
app.mount("/images", StaticFiles(directory=generated_images_dir), name="images")

class ChatRequest(BaseModel):
    message: str
    session_id: str
    image: Optional[str] = None # Base64 string or file path reference
    context_files: Optional[List[str]] = []

class SessionRequest(BaseModel):
    title: Optional[str] = "New Chat"

class LoginRequest(BaseModel):
    username: str
    password: str

from database import init_db, add_message, get_messages, create_session, get_sessions, delete_session, delete_message, get_last_message_id, create_user, get_user_by_username
from document_processor import extract_text_from_file
from local_client import generate_response, generate_image
import hashlib

# Initialize DB
init_db()

@app.post("/register")
async def register(request: LoginRequest):
    # Simple hash for demo purposes (production should use bcrypt/argon2)
    hashed_pw = hashlib.sha256(request.password.encode()).hexdigest()
    user_id = str(uuid.uuid4())
    success = create_user(user_id, request.username, hashed_pw)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User created successfully", "username": request.username}

@app.post("/login")
async def login(request: LoginRequest):
    user = get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    hashed_pw = hashlib.sha256(request.password.encode()).hexdigest()
    if user['password_hash'] != hashed_pw:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {"message": "Login successful", "username": user['username'], "user_id": user['id']}

@app.get("/")
def read_root():
    return {"message": "Chatbot Backend is running!"}

@app.post("/sessions")
async def create_new_session(request: SessionRequest):
    session_id = str(uuid.uuid4())
    create_session(session_id, request.title)
    return {"id": session_id, "title": request.title}

@app.get("/sessions")
async def get_all_sessions():
    return get_sessions()

@app.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return {"message": "Session deleted"}

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    return get_messages(session_id)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    
    # 1. Save user message
    user_msg_content = request.message
    if request.image:
        user_msg_content += " [Image Attached]"
    if request.context_files:
        user_msg_content += f" [{len(request.context_files)} Files Attached]"
        
    add_message(session_id, "user", user_msg_content, "text")

    # 2. Process context files
    context_text = ""
    for file_path in request.context_files:
        if os.path.exists(file_path):
            extracted = extract_text_from_file(file_path)
            context_text += f"\n--- Content of {os.path.basename(file_path)} ---\n{extracted}\n"
    
    # 3. Construct Prompt
    full_prompt = request.message
    if context_text:
        full_prompt += f"\n\nContext from uploaded files:\n{context_text}"
        
    # 4. Generate Response
    # Check for Image Generation Request
    if "/image" in request.message.lower() or "generate image" in request.message.lower():
        # Strip command from prompt to get clean description if needed, or pass full prompt
        image_path = generate_image(request.message)
        if "Error" in image_path:
             bot_response = image_path
        else:
             # Convert local path to URL
             filename = os.path.basename(image_path)
             image_url = f"http://localhost:8000/images/{filename}"
             bot_response = f"![Generated Image]({image_url})"
    
    else:
        # Handle image path safely (Vision)
        image_path = None
        if request.image and os.path.exists(request.image):
            image_path = request.image
            
        # Determine model type (logic/code/general) based on keywords or default
        model_type = "general"
        if "code" in request.message.lower() or "script" in request.message.lower() or "function" in request.message.lower():
            model_type = "code"
        elif "think" in request.message.lower() or "logic" in request.message.lower() or "reason" in request.message.lower():
            model_type = "logic"
            
        bot_response = generate_response(full_prompt, image_path, model_type)
    
    # 5. Save bot response
    add_message(session_id, "model", bot_response, "text")
    
    return {"response": bot_response}

@app.post("/undo")
async def undo_last_message(body: dict = Body(...)):
    session_id = body.get("session_id")
    # Delete last bot message (if any) and last user message
    # Ideally should use IDs, but simplified:
    # 1. Get last message. If bot, delete it.
    # 2. Get last message. If user, delete it.
    # A bit complex logic for "undo", usually means separate "delete last turn".
    
    # Implementation: Find last user message ID. Delete it and everything after it.
    last_user_msg_id = get_last_message_id(session_id, "user")
    if last_user_msg_id:
        # Delete this user msg and subsequent matches (cascading delete logically)
        # For simplicity, we just delete the last user message and the last bot message if it exists after it.
        # But SQL delete by ID is safer.
        delete_message(last_user_msg_id)
        
        # Also try to find if there was a bot response after it (id > last_user_msg_id)
        # OR just rely on UI to refresh.
        # Let's simple delete the last user message. The bot response might remain "orphaned" or we delete both.
        # Better: Delete allow messages > last_user_msg_id - 1? No.
        
        # Proper Undo:
        # Fetch status. Delete last user message + last bot message.
        pass

    # A simpler approach: Clear history is already there. Undo specific is tricky without precise targeting.
    # Let's assume the user wants to remove their last mistake.
    # We will find the very last 2 messages (likely User + Bot) and delete them.
    
    all_msgs = get_messages(session_id)
    if not all_msgs:
        return {"message": "Nothing to undo"}
    
    to_delete = []
    # If last is bot, mark for delete
    if all_msgs[-1]['role'] == 'model':
        to_delete.append(all_msgs[-1]['id'])
        # If second last is user, mark for delete
        if len(all_msgs) > 1 and all_msgs[-2]['role'] == 'user':
            to_delete.append(all_msgs[-2]['id'])
    elif all_msgs[-1]['role'] == 'user':
        to_delete.append(all_msgs[-1]['id'])
        
    for mid in to_delete:
        delete_message(mid)
        
    return {"message": "Undo successful", "deleted_count": len(to_delete)}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "path": file_path}

