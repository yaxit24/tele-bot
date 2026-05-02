import re
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_bad_words: set = set()
_spam_patterns: list = []


def load_filters():
    global _bad_words, _spam_patterns

    bad_words_file = DATA_DIR / "bad_words.txt"
    if bad_words_file.exists():
        _bad_words = {
            word.strip().lower()
            for word in bad_words_file.read_text().splitlines()
            if word.strip() and not word.startswith("#")
        }

    spam_file = DATA_DIR / "spam_patterns.txt"
    if spam_file.exists():
        _spam_patterns = [
            re.compile(pattern.strip(), re.IGNORECASE)
            for pattern in spam_file.read_text().splitlines()
            if pattern.strip() and not pattern.startswith("#")
        ]


def check_profanity(text: str) -> bool:
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in _bad_words:
            return True
        # Check if word starts with any bad word (e.g. "fucking" matches "fuck")
        # Require min 3 chars to avoid false positives on short words like "a", "s", "as"
        if len(word) >= 3:
            for bad in _bad_words:
                if len(bad) >= 3 and (word.startswith(bad) or bad.startswith(word)):
                    return True
    return False


def check_spam(text: str) -> bool:
    for pattern in _spam_patterns:
        if pattern.search(text):
            return True
    # Check for excessive links
    links = re.findall(r'https?://\S+', text)
    if len(links) >= 3:
        return True
    return False


def check_sexual_content(text: str) -> bool:
    # Basic keyword check — will be enhanced with AI in Phase 3
    sexual_keywords = {
        "porn", "xxx", "nude", "nudes", "sex video", "onlyfans",
        "sexual", "naked", "nsfw", "dick pic", "send nudes",
    }
    text_lower = text.lower()
    for keyword in sexual_keywords:
        if keyword in text_lower:
            return True
    return False


def detect_violation(text: str) -> Optional[str]:
    """Returns violation type or None if clean."""
    if check_profanity(text):
        return "profanity"
    if check_sexual_content(text):
        return "sexual_content"
    if check_spam(text):
        return "spam"
    return None
