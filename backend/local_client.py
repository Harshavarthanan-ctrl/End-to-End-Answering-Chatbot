import ollama
import json
import datetime
import os
import shutil
from huggingface_hub import InferenceClient
from typing import Optional

# Create a log file to store data for "Self-Learning"
LOG_FILE = "training_data.jsonl"

def log_interaction(prompt, response, model_name, image_path=None):
    """Saves the conversation for future fine-tuning/learning."""
    data = {
        "timestamp": str(datetime.datetime.now()),
        "model": model_name,
        "prompt": prompt,
        "response": response,
        "has_image": bool(image_path)
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

def generate_image(prompt: str) -> str:
    """
    Generates an image using Hugging Face InferenceClient (Tongyi-MAI/Z-Image-Turbo).
    Returns the path to the saved image.
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        return "Error: HF_TOKEN not found in environment variables."

    try:
        client = InferenceClient(
            api_key=hf_token,
        )
        
        print(f"--- Generating Image for: '{prompt}' ---")
        
        # output is a PIL.Image object
        image = client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
        )
        
        # Ensure static/generated_images exists
        # Assuming we are in backend/, let's put it in a known accessible place
        # Ideally, main.py should mount this directory. For now, we save it locally.
        output_dir = os.path.join(os.getcwd(), "generated_images")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"gen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = os.path.join(output_dir, filename)
        
        image.save(file_path)
        return file_path
    
    except Exception as e:
        return f"Error generating image: {str(e)}"

def generate_response(prompt: str, image_path: str = None, model_type: str = "general"):
    """
    Selects the best model based on the task:
    - Vision: 'qwen2.5-vl:7b' (if image_path provided)
    - Logic: 'deepseek-r1'
    - Code: 'qwen3'
    - General: 'mistral'
    """
    
    # 1. Image Generation Check (Simple heuristic)
    # If the user explicitly asks to generate an image, we should probably handle it or let the caller handle it.
    # For now, we assume the caller might intercept or we treat it as text unless we implement a router.
    # But since the user instructions separated them, we'll focus on Text/Vision here.
    
    if image_path:
        selected_model = "qwen2.5vl:7b"
        print(f"--- Analyzing Image with {selected_model} ---")
        try:
            # Prepare message for Vision model
            message = {
                'role': 'user',
                'content': prompt,
                'images': [image_path]
            }
            
            response = ollama.chat(
                model=selected_model,
                messages=[message]
            )
            reply = response['message']['content']
            log_interaction(prompt, reply, selected_model, image_path)
            return reply
            
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    # 2. Text Logic
    model_map = {
        "logic": "deepseek-r1:7b", # Assuming standard tag
        "code": "qwen3:8b",        # Assuming standard tag
        "general": "mistral:latest"
    }
    
    # Fallback to mistral if type not found
    selected_model = model_map.get(model_type, "mistral:latest")
    
    try:
        print(f"--- Thinking with {selected_model} ---")
        response = ollama.chat(
            model=selected_model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        reply = response['message']['content']
        log_interaction(prompt, reply, selected_model)
        return reply
        
    except Exception as e:
        return f"Error generating response: {str(e)}"

if __name__ == "__main__":
    # Test
    print(generate_response("Hello, who are you?", model_type="general"))
