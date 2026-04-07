import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common import (
    add_message,
    call_chat_api,
    call_stt_api,
    ensure_chat_state,
    get_language_label,
    play_audio,
    render_sidebar,
)


st.set_page_config(page_title="Voice Assistant", page_icon="🎙️", layout="centered")

PAGE_PREFIX = "voice"


def handle_voice_input(recorded_audio) -> None:
    if recorded_audio is None:
        return

    audio_bytes = recorded_audio.getvalue()
    audio_id = f"{recorded_audio.name}:{len(audio_bytes)}"
    if st.session_state[f"{PAGE_PREFIX}_last_audio_id"] == audio_id:
        return

    with st.spinner("Converting speech to text..."):
        stt_data = call_stt_api(recorded_audio)

    recognized_text = stt_data.get("text", "").strip()
    if not recognized_text:
        st.session_state[f"{PAGE_PREFIX}_voice_status"] = (
            "Could not recognize speech from the microphone recording."
        )
        st.session_state[f"{PAGE_PREFIX}_last_audio_id"] = audio_id
        return

    st.session_state[f"{PAGE_PREFIX}_voice_status"] = f"Recognized text: {recognized_text}"
    add_message(PAGE_PREFIX, "user", recognized_text)

    with st.spinner("Getting voice answer..."):
        chat_data = call_chat_api(
            st.session_state[f"{PAGE_PREFIX}_session_id"],
            recognized_text,
            stt_data.get("language", "en"),
        )

    if not chat_data:
        st.session_state[f"{PAGE_PREFIX}_voice_status"] = (
            "Could not get an answer from the backend."
        )
        return

    st.session_state[f"{PAGE_PREFIX}_language"] = chat_data.get(
        "language", stt_data.get("language", "en")
    )
    add_message(
        PAGE_PREFIX,
        "assistant",
        chat_data.get("response_text", ""),
        chat_data.get("audio_base64", ""),
    )
    st.session_state[f"{PAGE_PREFIX}_last_audio_id"] = audio_id


def main() -> None:
    ensure_chat_state(PAGE_PREFIX)
    render_sidebar("Voice Assistant", clear_prefix=PAGE_PREFIX)

    st.title("🎙️ Voice Assistant")
    st.caption("Speak naturally and the assistant will answer back in voice.")
    st.markdown(
        f"**Language:** ● {get_language_label(st.session_state[f'{PAGE_PREFIX}_language'])}"
    )

    for message in st.session_state[f"{PAGE_PREFIX}_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                play_audio(message.get("audio_base64", ""))

    st.write("Tap record and ask your question.")
    recorded_audio = st.audio_input("🎤 Record your voice")
    st.caption("Allow microphone access in your browser. Chrome or Edge usually works best.")

    if recorded_audio is not None:
        audio_bytes = recorded_audio.getvalue()
        audio_id = f"{recorded_audio.name}:{len(audio_bytes)}"
        if st.session_state[f"{PAGE_PREFIX}_last_audio_id"] != audio_id:
            if st.button("Send Voice Message"):
                handle_voice_input(recorded_audio)
                st.rerun()
        else:
            st.caption("This recording is already processed. Record a fresh one to ask again.")

    if st.session_state[f"{PAGE_PREFIX}_voice_status"]:
        st.write(st.session_state[f"{PAGE_PREFIX}_voice_status"])


main()
