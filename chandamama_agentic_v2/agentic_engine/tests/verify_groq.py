import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentic_engine import config
from agentic_engine.llm_client import generate_response_multi

def verify_groq():
    print(f"Checking Groq Configuration...")
    print(f"Default Model: {config.DEFAULT_AGENT_MODEL}")

    api_key_var = config.MODEL_API_KEY_MAP.get(config.DEFAULT_AGENT_MODEL)
    api_key = os.getenv(api_key_var)

    if not api_key:
        print(f"❌ Error: {api_key_var} is not set in environment.")
        print("Please set it in your .env file or terminal.")
        return

    print(f"✅ API Key found in {api_key_var}")

    print("\nAttempting to call Groq API...")
    try:
        response = generate_response_multi(
            model_id=config.DEFAULT_AGENT_MODEL,
            prompt="Hello, are you working? Reply with 'Yes, I am Groq'.",
            max_tokens=200
        )
        print(f"Raw Response Content: '{response}'")

        if "Groq" in response or len(response) > 0:
             print("✅ Groq Integration Successful!")
        else:
             print("⚠️  Response received but unexpected content. Check llm_client.py handling.")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_groq()
