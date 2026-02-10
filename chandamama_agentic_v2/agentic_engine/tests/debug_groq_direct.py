import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key present: {bool(api_key)}")

client = Groq(api_key=api_key)

try:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
          {
            "role": "user",
            "content": "Hello, verify yourself."
          }
        ],
        temperature=1,
        max_tokens=100, # Testing max_tokens instead of max_completion_tokens
        top_p=1,
        # reasoning_effort="medium",
        stream=False,
        stop=None
    )
    print("Response object:", completion)
    print("Content:", completion.choices[0].message.content)

except Exception as e:
    print(f"Error: {e}")

print("\nAttempting with 'reasoning_effort' param...")
try:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
          {
            "role": "user",
            "content": "Hello, verify yourself."
          }
        ],
        reasoning_effort="medium",
        stream=False
    )
    print("Response (with reasoning_effort):", completion.choices[0].message.content)
except Exception as e:
    print(f"Error with reasoning_effort: {e}")
