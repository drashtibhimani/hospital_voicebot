from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


# Store each chat exchange in the database for analytics and history.
class ConversationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str
    language: str
    query: str
    response: str
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Validate the incoming chat request from the frontend.
class ChatRequest(SQLModel):
    session_id: str
    text: str
    language: str = "auto"


# Return the bot reply text, detected language, and audio data.
class ChatResponse(SQLModel):
    response_text: str
    language: str
    audio_base64: str


class KnowledgeBaseUploadResponse(SQLModel):
    filename: str
    stored_path: str
    chunks_added: int
    message: str
