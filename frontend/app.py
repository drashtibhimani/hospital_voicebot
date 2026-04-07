import streamlit as st

from common import render_sidebar


st.set_page_config(page_title="Hospital Voicebot", page_icon="✚", layout="centered")


def apply_home_styles() -> None:
    st.markdown(
        """
        <style>
        .mode-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }
        .mode-copy {
            color: rgba(250,250,250,0.82);
            line-height: 1.7;
            margin-bottom: 0.7rem;
        }
        div[data-testid="column"] .stButton > button {
            border-radius: 14px;
            padding: 0.88rem 1rem;
            font-weight: 700;
            border: none;
            color: white;
            width: 100%;
            transition: transform 0.15s ease, opacity 0.15s ease;
        }
        div[data-testid="column"] .stButton > button:hover {
            transform: translateY(-1px);
            opacity: 0.96;
        }
        div[data-testid="column"]:nth-of-type(1) .stButton > button {
            background: linear-gradient(135deg, #2b6cb0, #1d4ed8);
        }
        div[data-testid="column"]:nth-of-type(2) .stButton > button {
            background: linear-gradient(135deg, #db2777, #7c3aed);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    render_sidebar("Choose your experience")
    apply_home_styles()

    st.title("MAYA ✚")
    st.caption("Your hospital's AI assistant for quick info and voice interactions.")
    st.caption("Choose the way you want to talk with the assistant.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="mode-title">💬 Quick Chat</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="mode-copy">Perfect for fast typed questions, quick hospital lookups, and clean text replies without audio.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Open Quick Chat", use_container_width=True, key="open_quick_chat"):
            st.switch_page("pages/text_chat.py")

    with col2:
        st.markdown('<div class="mode-title">🎙️ Voice Assistant</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="mode-copy">Speak naturally, let the app transcribe your question, and get a spoken answer back with audio playback.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Open Voice Assistant", use_container_width=True, key="open_voice_assistant"):
            st.switch_page("pages/voice_chat.py")

    st.markdown("### How It Feels")
    st.write("💬 Quick Chat: text in, text out.")
    st.write("🎙️ Voice Assistant: voice in, voice out, with recognized text shown.")
    st.write("📊 Insights: review conversations and usage from the sidebar.")


main()
