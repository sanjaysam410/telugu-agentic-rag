import os
import json
from typing import Optional
from agentic_engine import config

try:
    from openai import OpenAI
    from huggingface_hub import InferenceClient
    from groq import Groq
except ImportError:
    pass # Handle missing deps gracefully or assume installed

# Singleton to hold client instances
_client_instances = {}

def get_client(model_id: str):
    """
    Returns an authenticated client for the specified model_id.
    """
    global _client_instances

    if model_id in _client_instances:
        return _client_instances[model_id]

    config_value = config.MODEL_API_KEY_MAP.get(model_id, "HF_TOKEN")
    api_key = os.getenv(config_value)

    if not api_key:
        if config_value.isupper():
             # Soft warning, but don't crash yet until usage
             print(f"WARNING: Environment variable '{config_value}' is missing.", flush=True)
        api_key = config_value

    # Groq Models
    if config_value == "GROQ_API_KEY":
        client = Groq(api_key=api_key)
        _client_instances[model_id] = ("groq", client)

    # OpenAI Models
    elif "gpt" in model_id.lower():
        client = OpenAI(api_key=api_key)
        _client_instances[model_id] = ("openai", client)

    # Hugging Face Models
    else:
        client = InferenceClient(model=model_id, token=api_key)
        _client_instances[model_id] = ("hf", client)

    return _client_instances[model_id]

def generate_response_multi(
    model_id: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = config.LLM_MAX_TOKENS,
    temperature: float = config.LLM_TEMPERATURE
) -> str:
    """
    Generates response using the specified model.
    """
    try:
        client_type, client = get_client(model_id)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if client_type == "openai":
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content

        elif client_type == "groq":
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content or ""

        elif client_type == "hf":
            response = client.chat_completion(
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            return ""

    except Exception as e:
        return f"Error ({model_id}): {str(e)}"

def generate_json_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = config.DEFAULT_AGENT_MODEL,
    max_tokens: int = 500,
    temperature: float = 0.1
) -> dict:
    """
    Generates a JSON response from the LLM.
    """
    # Force JSON instruction
    json_prompt = prompt + "\n\nRETURN ONLY VALID JSON."

    response_text = generate_response_multi(
        model_id=model,
        prompt=json_prompt,
        system_prompt=system_prompt + " You output strictly valid JSON.",
        max_tokens=max_tokens,
        temperature=temperature
    )

    # Strip markdown code blocks
    clean_text = response_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse JSON",
            "raw_text": clean_text
        }
