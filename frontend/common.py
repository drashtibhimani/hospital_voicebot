import base64
import os
from uuid import uuid4

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


def apply_shared_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000")


def get_language_label(code: str) -> str:
    labels = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}
    return labels.get(code, "English")


def ensure_chat_state(prefix: str) -> None:
    if f"{prefix}_messages" not in st.session_state:
        st.session_state[f"{prefix}_messages"] = []
    if f"{prefix}_session_id" not in st.session_state:
        st.session_state[f"{prefix}_session_id"] = str(uuid4())
    if f"{prefix}_language" not in st.session_state:
        st.session_state[f"{prefix}_language"] = "en"
    if f"{prefix}_last_audio_id" not in st.session_state:
        st.session_state[f"{prefix}_last_audio_id"] = ""
    if f"{prefix}_voice_status" not in st.session_state:
        st.session_state[f"{prefix}_voice_status"] = ""


def clear_chat_state(prefix: str) -> None:
    st.session_state[f"{prefix}_messages"] = []
    st.session_state[f"{prefix}_language"] = "en"
    st.session_state[f"{prefix}_last_audio_id"] = ""
    st.session_state[f"{prefix}_voice_status"] = ""


def add_message(prefix: str, role: str, content: str, audio_base64: str = "") -> None:
    st.session_state[f"{prefix}_messages"].append(
        {"role": role, "content": content, "audio_base64": audio_base64}
    )


def call_chat_api(session_id: str, text: str, language: str = "auto") -> dict:
    payload = {
        "session_id": session_id,
        "text": text,
        "language": language,
    }
    try:
        response = requests.post(f"{get_backend_url()}/chat", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        print(f"Chat API request failed: {error}")
        st.error("Could not get a response from the backend.")
        return {}


def call_stt_api(audio_file) -> dict:
    files = {"audio": (audio_file.name, audio_file.getvalue(), audio_file.type)}
    try:
        response = requests.post(f"{get_backend_url()}/stt", files=files, timeout=90)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        print(f"STT API request failed: {error}")
        st.error("Could not convert audio to text.")
        return {}


def play_audio(audio_base64: str) -> None:
    if not audio_base64:
        return
    try:
        st.audio(base64.b64decode(audio_base64), format="audio/mp3")
    except Exception as error:
        print(f"Audio playback failed: {error}")
        st.error("Audio could not be played.")


def render_sidebar(mode_label: str, clear_prefix: str | None = None) -> None:
    apply_shared_styles()
    with st.sidebar:
        st.title("Hospital Voicebot")
        st.caption(mode_label)
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/text_chat.py", label="💬 Quick Chat")
        st.page_link("pages/voice_chat.py", label="🎙️ Voice Assistant")
        st.page_link("pages/dashboard.py", label="📊 Insights")
        if clear_prefix and st.button("Clear Chat"):
            clear_chat_state(clear_prefix)
            st.rerun()
        st.divider()
        st.markdown("### ✨ Care Modes")
        st.write("Switch between text and voice without mixing conversations.")
