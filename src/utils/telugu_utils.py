
import re
from typing import Dict, Any

def script_validation(story_text: str) -> Dict[str, Any]:
    """
    Validates if the text is primarily Telugu and meets basic length requirements.
    """
    if not story_text or not story_text.strip():
        return {"valid": False, "code": "EMPTY_CONTENT", "reason": "Content is empty"}

    # Telugu Unicode Range: \u0C00-\u0C7F
    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]')
    telugu_chars = telugu_pattern.findall(story_text)
    total_chars = len(story_text)

    if len(telugu_chars) == 0:
        return {"valid": False, "code": "NOT_TELUGU", "reason": "No Telugu characters found"}

    telugu_ratio = (len(telugu_chars) / total_chars) * 100

    # 1. Length Check
    if total_chars < 50:
        return {"valid": False, "code": "TOO_SHORT", "reason": "Story must be at least 50 characters"}

    # 2. Ratio Check (Allow for some English loan words/punctuation)
    if telugu_ratio < 40.0:
        return {"valid": False, "code": "LOW_TELUGU_RATIO", "reason": f" Telugu content ratio too low ({telugu_ratio:.2f}%)"}

    return {"valid": True, "telugu_ratio": telugu_ratio}


def script_extraction(text: str) -> Dict[str, Any]:
    """
    Extracts basic statistics from the text without LLM.
    """
    words = text.split()
    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]')
    telugu_chars = telugu_pattern.findall(text)

    # Simple sentence count estimation
    sentence_count = text.count('.') + text.count('?') + text.count('!') + text.count('।')

    return {
        "word_count": len(words),
        "char_count": len(text),
        "sentence_count": sentence_count,
        "paragraph_count": text.count('\n\n') + 1,
        "telugu_ratio": (len(telugu_chars) / len(text) * 100) if len(text) > 0 else 0
    }
