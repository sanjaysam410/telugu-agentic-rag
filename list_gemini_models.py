
import google.generativeai as genai
import os

api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAuNLT8ZhTIhok-b-rJlHboYP3FOKAmzNE")
genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
