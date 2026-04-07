import time

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.database import get_session
from backend.models import ChatRequest, ChatResponse, ConversationLog
from backend.services.lang_service import detect_language
from backend.services.rag_service import get_rag_response
from backend.services.tts_service import text_to_base64_audio


router = APIRouter()


# Handle a user chat request and return text plus audio response.
@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, session: Session = Depends(get_session)) -> ChatResponse:
    start_time = time.time()
    language = request.language
    if language == "auto":
        language = detect_language(request.text)

    response_text = get_rag_response(request.text, language, [])
    audio_base64 = text_to_base64_audio(response_text, language)
    response_time_ms = (time.time() - start_time) * 1000

    log = ConversationLog(
        session_id=request.session_id,
        language=language,
        query=request.text,
        response=response_text,
        response_time_ms=response_time_ms,
    )
    session.add(log)
    session.commit()

    return ChatResponse(
        response_text=response_text,
        language=language,
        audio_base64=audio_base64,
    )
