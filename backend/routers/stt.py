import os
import tempfile

import speech_recognition as sr
from fastapi import APIRouter, File, UploadFile

from backend.services.lang_service import detect_language


router = APIRouter()


# Convert uploaded audio into text and detect the spoken language.
@router.post("")
async def speech_to_text(audio: UploadFile = File(...)) -> dict[str, str]:
    temp_path = ""
    try:
        audio_bytes = await audio.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)

        recognized_text = ""
        for stt_lang in ["en-US", "hi-IN", "gu-IN"]:
            try:
                recognized_text = recognizer.recognize_google(audio_data, language=stt_lang)
                if recognized_text:
                    break
            except Exception:
                continue

        language = detect_language(recognized_text)
        return {"text": recognized_text, "language": language}
    except Exception as error:
        print(f"STT failed: {error}")
        return {"text": "", "language": "en"}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
