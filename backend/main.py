from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_db_and_tables
from backend.routers import analytics, chat, knowledgebase, stt


load_dotenv()
app = FastAPI(title="Hospital Voicebot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables when the API starts.
@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


# Return a simple health check response.
@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(stt.router, prefix="/stt", tags=["stt"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(knowledgebase.router, prefix="/knowledgebase", tags=["knowledgebase"])
