import base64
from io import BytesIO

from gtts import gTTS


# Convert reply text into base64 audio so the frontend can play it.
def text_to_base64_audio(text: str, lang_code: str) -> str:
    try:
        buffer = BytesIO()
        tts = gTTS(text=text, lang=lang_code)
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")
    except Exception as error:
        print(f"TTS generation failed: {error}")
        return ""
