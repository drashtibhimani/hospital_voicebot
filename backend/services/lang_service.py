import re

from langdetect import detect


LANG_TO_GTTS = {"en": "en", "hi": "hi", "gu": "gu"}
LANG_TO_STT = {"en": "en-US", "hi": "hi-IN", "gu": "gu-IN"}


# Detect the user's language and map it to en, hi, or gu.
def detect_language(text: str) -> str:
    content = text.strip()
    if not content:
        return "en"

    if re.search(r"[\u0A80-\u0AFF]", content):
        return "gu"
    if re.search(r"[\u0900-\u097F]", content):
        return "hi"
    if re.search(r"[A-Za-z]", content):
        return "en"

    try:
        detected = detect(content)
        if detected in {"en", "hi", "gu"}:
            return detected
        if detected == "mr":
            return "hi"
        return "en"
    except Exception as error:
        print(f"Language detection failed: {error}")
        return "en"


# Convert a language code into a friendly display name.
def get_lang_name(code: str) -> str:
    names = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}
    return names.get(code, "English")
