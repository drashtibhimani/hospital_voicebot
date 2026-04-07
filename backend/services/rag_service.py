import os
from functools import lru_cache

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma


EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
CHROMA_DIRECTORY = "./chroma_db"
MAX_HISTORY_MESSAGES = 2
MAX_QUERY_CHARS = 400
RETRIEVAL_K = 2
MAX_DOC_CHARS = 700
embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
vectorstore = Chroma(
    persist_directory=CHROMA_DIRECTORY,
    embedding_function=embeddings,
)

AGENT_SYSTEM_PROMPT = """
You are Maya, a warm and professional virtual assistant for our hospital.
Your role is to help patients, visitors, and staff by answering questions about 
the hospital — including departments, services, timings, doctors, procedures, 
appointments, and general health guidance available at this facility.

────────────────────────────────────────────
PERSONALITY & TONE
────────────────────────────────────────────
- Always be warm, calm, empathetic, and professional.
- Use simple, clear language that patients and visitors can easily understand.
- Avoid medical jargon unless the user specifically uses it.
- Always respond in the same language the user writes in.

────────────────────────────────────────────
GREETINGS
────────────────────────────────────────────
- When a user greets you (e.g., "Hi", "Hello", "Good morning"), respond warmly.
  Example: "Hello! I'm Maya, your hospital assistant. How can I help you today? 😊"
- For follow-up messages, stay friendly but concise — don't repeat the full introduction.

────────────────────────────────────────────
ANSWERING QUESTIONS
────────────────────────────────────────────
- Before answering ANY factual question about the hospital, ALWAYS look it up 
  using your information retrieval capability first.
- Only answer based on what you find. Do NOT guess, assume, or generate 
  information that was not retrieved.
- If the retrieved information fully answers the question → answer clearly and concisely.
- If the retrieved information is partial → share what you found and note the limitation.
- If nothing relevant is retrieved → respond honestly:
  "I'm sorry, I don't have information about that at the moment. 
   I'd recommend contacting our reception or helpdesk directly for assistance."

────────────────────────────────────────────
GUARDRAILS — WHAT YOU MUST NOT DO
────────────────────────────────────────────
- ❌ Do NOT diagnose medical conditions or prescribe treatments.
- ❌ Do NOT give personalized medical advice (e.g., "You should take X medicine").
- ❌ Do NOT make up doctor names, room numbers, timings, or any hospital data.
- ❌ Do NOT answer questions unrelated to the hospital or healthcare context
     (e.g., politics, sports, coding, general trivia).
- ❌ Do NOT share or ask for sensitive personal information (e.g., passwords, 
     payment details, national ID).
- ❌ Do NOT promise outcomes (e.g., "Your surgery will go fine").

If someone asks something outside your scope, respond kindly:
  "That's outside what I can help with, but I'm here for any hospital-related 
   questions you may have!"

────────────────────────────────────────────
EMERGENCY SITUATIONS
────────────────────────────────────────────
- If a user describes a medical emergency, immediately respond:
  "This sounds like a medical emergency. Please call emergency services (108) 
   or go to our Emergency Department immediately. Do not wait."
- Do not attempt to guide treatment in emergencies.


"""

def get_embeddings() -> HuggingFaceEmbeddings:
    return embeddings


def get_vectorstore() -> Chroma:
    return vectorstore


# Build the short chat history in the format expected by the model.
def _build_history_messages(history: list[dict[str, str]]) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        role = item.get("role", "user")
        content = str(item.get("content", "")).strip()[:MAX_QUERY_CHARS]
        if content:
            messages.append((role, content))
    return messages


def _trim_text(text: str, limit: int) -> str:
    content = text.strip()
    if len(content) <= limit:
        return content
    trimmed = content[:limit].rsplit(" ", 1)[0].strip()
    return f"{trimmed}..." if trimmed else f"{content[:limit]}..."


def _build_agent_messages(
    query: str,
    lang_code: str,
    history: list[dict[str, str]],
) -> list[HumanMessage | AIMessage]:
    messages: list[HumanMessage | AIMessage] = []
    for role, content in _build_history_messages(history):
        if role == "assistant":
            messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))

    messages.append(
        HumanMessage(
            content=(
                f"User language code: {lang_code}\n"
                f"User question: {_trim_text(query, MAX_QUERY_CHARS)}\n"
                "Please answer in the same language as the user."
            )
        )
    )
    return messages


@tool
def knowledge_retrieval(query: str) -> str:
    """Search the hospital knowledge base for information relevant to the user's question."""
    docs = get_vectorstore().similarity_search(_trim_text(query, MAX_QUERY_CHARS), k=RETRIEVAL_K)
    if not docs:
        return "No relevant hospital knowledge was found."

    results: list[str] = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "knowledge_base")
        content = _trim_text(doc.page_content, MAX_DOC_CHARS)
        if content:
            results.append(f"[{index}] Source: {source}\n{content}")
    return "\n\n".join(results) if results else "No relevant hospital knowledge was found."


@lru_cache(maxsize=1)
def _build_agent():
    model = ChatGroq(
        model=GROQ_MODEL_NAME,
        api_key=GROQ_API_KEY,
        temperature=0,
    )
    return create_agent(
        model=model,
        tools=[knowledge_retrieval],
        system_prompt=AGENT_SYSTEM_PROMPT,
        debug=True,
        name="hospital_knowledge_agent",
    )


def _extract_final_answer(result: dict) -> str:
    messages = result.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            if isinstance(message.content, str):
                return message.content.strip()
            if isinstance(message.content, list):
                text_parts = [
                    item.get("text", "").strip()
                    for item in message.content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                return "\n".join(part for part in text_parts if part).strip()
    return ""


# Search the knowledge base with a LangChain agent and generate a reply in the same language.
def get_rag_response(query: str, lang_code: str, history: list[dict[str, str]]) -> str:
    try:
        agent = _build_agent()
        result = agent.invoke(
            {
                "messages": _build_agent_messages(query, lang_code, history),
            }
        )
        answer = _extract_final_answer(result)
        if answer:
            return answer
        raise ValueError("Agent returned no final answer.")
    except Exception as error:
        print(f"Groq agent request failed: {error}")
        fallback = {
            "en": "Sorry, I could not get an answer right now.",
            "hi": "माफ़ कीजिए, मैं अभी उत्तर नहीं दे सका।",
            "gu": "માફ કરશો, હું અત્યારે જવાબ આપી શક્યો નથી.",
        }
        return fallback.get(lang_code, fallback["en"])
