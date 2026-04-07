import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common import get_backend_url, render_sidebar


st.set_page_config(page_title="Insights", page_icon="📊", layout="wide")


# Convert the dropdown label into the API language code.
def get_language_code(option: str) -> str:
    mapping = {
        "All": "all",
        "English (en)": "en",
        "Hindi (hi)": "hi",
        "Gujarati (gu)": "gu",
    }
    return mapping.get(option, "all")


# Request analytics data from the backend with the selected filters.
def fetch_analytics(from_date, language_option: str) -> dict:
    params = {
        "start_date": from_date.isoformat() if from_date else None,
        "language": get_language_code(language_option),
    }
    try:
        response = requests.get(f"{get_backend_url()}/analytics", params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        print(f"Analytics request failed: {error}")
        st.error("Could not load analytics data.")
        return {}


# Find the most used language label from the language count dictionary.
def get_most_used_language(lang_counts: dict) -> str:
    labels = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}
    if not lang_counts:
        return "N/A"
    top_code = max(lang_counts, key=lang_counts.get)
    return labels.get(top_code, top_code)


# Convert log records into a dataframe for display and export.
def build_logs_dataframe(logs: list[dict]) -> pd.DataFrame:
    if not logs:
        return pd.DataFrame(columns=["Timestamp", "Language", "Query", "Response"])
    rows = []
    for log in logs:
        rows.append(
            {
                "Timestamp": log.get("timestamp", ""),
                "Language": log.get("language", ""),
                "Query": log.get("query", ""),
                "Response": log.get("response", ""),
            }
        )
    return pd.DataFrame(rows)


# Render the main dashboard page with filters, metrics, charts, and logs.
def main() -> None:
    render_sidebar("Insights")

    st.title("📊 Conversation Insights")
    st.caption("Track usage, language trends, and recent conversation activity.")

    col1, col2, col3 = st.columns([1, 1, 0.6])
    with col1:
        from_date = st.date_input("From date")
    with col2:
        language_option = st.selectbox(
            "Language",
            ["All", "English (en)", "Hindi (hi)", "Gujarati (gu)"],
        )
    with col3:
        refresh = st.button("Refresh")

    if refresh or "dashboard_data" not in st.session_state:
        with st.spinner("Loading analytics..."):
            st.session_state.dashboard_data = fetch_analytics(from_date, language_option)

    data = st.session_state.get("dashboard_data", {})
    logs = data.get("logs", [])
    if not data or (
        not data.get("total_conversations")
        and not data.get("lang_counts")
        and not data.get("top_queries")
        and not logs
    ):
        st.info("No conversation data is available yet.")
        return

    lang_counts = data.get("lang_counts", {})
    top_queries = data.get("top_queries", [])

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Total Conversations", data.get("total_conversations", 0))
    metric2.metric("Avg Response Time (ms)", data.get("avg_response_ms", 0.0))
    metric3.metric("Most Used Language", get_most_used_language(lang_counts))
    metric4.metric("Total Languages Used", len(lang_counts))

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        if lang_counts:
            pie_data = pd.DataFrame(
                {"Language": list(lang_counts.keys()), "Count": list(lang_counts.values())}
            )
            st.plotly_chart(
                px.pie(pie_data, names="Language", values="Count", title="Language Distribution"),
                use_container_width=True,
            )
        else:
            st.info("No language distribution data yet.")

    with chart_col2:
        if top_queries:
            bar_data = pd.DataFrame({"Word": top_queries, "Count": list(range(len(top_queries), 0, -1))})
            st.plotly_chart(
                px.bar(bar_data, x="Word", y="Count", title="Top Query Words"),
                use_container_width=True,
            )
        else:
            st.info("No query word data yet.")

    st.subheader("Conversation Logs")
    logs_df = build_logs_dataframe(logs)
    st.dataframe(logs_df, use_container_width=True)

    csv_buffer = StringIO()
    logs_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download CSV",
        data=csv_buffer.getvalue(),
        file_name="conversation_logs.csv",
        mime="text/csv",
    )


main()
