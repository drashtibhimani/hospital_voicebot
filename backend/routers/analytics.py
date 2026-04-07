from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import ConversationLog


router = APIRouter()


# Return simple conversation analytics with optional filters.
@router.get("")
def get_analytics(
    start_date: str | None = None,
    language: str | None = None,
    session: Session = Depends(get_session),
) -> dict:
    logs = session.exec(select(ConversationLog)).all()

    if start_date:
        filter_date = datetime.fromisoformat(start_date)
        logs = [log for log in logs if log.timestamp >= filter_date]
    if language and language != "all":
        logs = [log for log in logs if log.language == language]

    total_conversations = len(logs)
    avg_response_ms = 0.0
    if total_conversations:
        avg_response_ms = round(
            sum(log.response_time_ms for log in logs) / total_conversations, 1
        )

    lang_counts = dict(Counter(log.language for log in logs))
    words: list[str] = []
    for log in logs:
        for word in log.query.lower().split():
            clean_word = word.strip(".,!?()[]{}\"'").strip()
            if len(clean_word) >= 3:
                words.append(clean_word)

    top_queries = [word for word, _ in Counter(words).most_common(10)]
    last_logs = sorted(logs, key=lambda item: item.timestamp, reverse=True)[:50]
    log_dicts = [
        {
            "id": log.id,
            "session_id": log.session_id,
            "language": log.language,
            "query": log.query,
            "response": log.response,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in last_logs
    ]

    return {
        "total_conversations": total_conversations,
        "avg_response_ms": avg_response_ms,
        "lang_counts": lang_counts,
        "top_queries": top_queries,
        "logs": log_dicts,
    }
