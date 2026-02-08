Callisto 🚀

Callisto is an end-to-end multimodal answering chatbot built to deliver accurate, context-aware responses across text and image inputs using a multi-LLM orchestration approach.

✨ Features

Multimodal Q&A (Text + Image)

Dynamic LLM routing based on task complexity

Strong reasoning and instruction-following

Modular and production-ready architecture

Designed for scalability and experimentation

🚀 Core Architecture
The chatbot operates as a "Cognitive Router," automatically sending tasks to the most efficient model:

Logic & Reasoning: deepseek-r1 (Ollama)

Coding & Technical Tasks: qwen3 (Ollama)

General Conversation: mistral (Ollama)

Vision (Image Analysis): qwen2.5-vl (Ollama)

Professional Image Generation: Z-Image-Turbo (Hugging Face API)

🛠️ Tech Stack
Backend: Python 3.10+

Local Inference: Ollama (Managing 7B-parameter models)

Cloud Inference: Hugging Face Inference API (InferenceClient)

Data Format: JSONL (for self-learning logs)

Hardware Optimization: FP16 Quantization and CPU Offloading

📥 Installation & Setup
Clone the Repository

Bash

git clone https://Harshavarthanan-ctrl/End-to-End-Answering-Chatbot.git
cd end-to-end-chatbot
Pull Local Models (Ollama)

Bash

ollama pull deepseek-r1:7b
ollama pull mistral
ollama pull qwen2.5vl:7b
Environment Setup Create a .env file and add your Hugging Face Access Token:

Plaintext

HF_TOKEN=hf_your_token_here
Install Dependencies

Bash

pip install ollama huggingface_hub pillow python-dotenv
🧠 The Self-Learning Loop
Every interaction is captured in training_data.jsonl. This allows the chatbot to "learn" from its history.

Goal: Use this data for Supervised Fine-Tuning (SFT).

Format:

JSON

{"timestamp": "2026-02-08", "task": "vision", "prompt": "Analyze this soil", "response": "High risk of erosion"}
🔧 Usage
Run the main script:

Bash

python main.py
Text Chat: Just type your message.

Vision: Upload an image when prompted.

Image Gen: Start your prompt with /image.
