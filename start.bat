@echo off
echo Starting Chatbot System...

REM Start Backend
start "Backend" cmd /k "cd backend && python -m uvicorn main:app --reload --port 8000"

REM Start Frontend
start "Frontend" cmd /k "cd frontend && npm run dev"

echo System started. Please ensure .env has your GEMINI_API_KEY.
echo Frontend running at http://localhost:5173
echo Backend running at http://localhost:8000
