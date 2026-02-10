
import re

def is_telugu(text: str) -> bool:
    """
    Check if the text contains Telugu characters.
    """
    # Telugu Unicode Range: \u0C00-\u0C7F
    telugu_pattern = re.compile(r'[\u0C00-\u0C7F]+')
    return bool(telugu_pattern.search(text))

def count_telugu_chars(text: str) -> int:
    """
    Count the number of Telugu characters in the text.
    """
    # Telugu Unicode Range: \u0C00-\u0C7F
    telugu_chars = [char for char in text if '\u0C00' <= char <= '\u0C7F']
    return len(telugu_chars)

def extract_keywords(text: str) -> list[str]:
    """
    Extract keywords from the text.
    Currently, this is a placeholder implementation that splits by whitespace
    and filters for Telugu words of significant length.
    """
    words = text.split()
    # simple heuristic: keep words that are Telugu and > 2 chars
    keywords = [word.strip('.,!?') for word in words if is_telugu(word) and len(word) > 2]
    return list(set(keywords))  # unique keywords
