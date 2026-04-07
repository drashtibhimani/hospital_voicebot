import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common import (
    add_message,
    call_chat_api,
    ensure_chat_state,
    get_language_label,
    render_sidebar,
)


st.set_page_config(page_title="Quick Chat", page_icon="💬", layout="centered")

PAGE_PREFIX = "text"


def main() -> None:
    ensure_chat_state(PAGE_PREFIX)
    render_sidebar("Quick Chat", clear_prefix=PAGE_PREFIX)

    st.title("💬 Quick Chat")
    st.caption("Type your hospital questions and get crisp text replies.")
    st.markdown(
        f"**Language:** ● {get_language_label(st.session_state[f'{PAGE_PREFIX}_language'])}"
    )

    for message in st.session_state[f"{PAGE_PREFIX}_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_text = st.chat_input("Ask about doctors, departments, reports, or appointments")
    if not user_text:
        return

    add_message(PAGE_PREFIX, "user", user_text)
    with st.spinner("Getting answer..."):
        data = call_chat_api(st.session_state[f"{PAGE_PREFIX}_session_id"], user_text)

    if not data:
        return

    st.session_state[f"{PAGE_PREFIX}_language"] = data.get("language", "en")
    add_message(PAGE_PREFIX, "assistant", data.get("response_text", ""))
    st.rerun()


main()
