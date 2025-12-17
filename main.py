from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from agents import master_agent
from typing import Optional

app = FastAPI()

# sessions keyed by session_id (simple in-memory store for demo)
SESSIONS = {}


@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
def chat(data: dict):
    """Chat endpoint expects JSON {"message": str, "session_id": Optional[str]}.

    If no session_id is provided, a default session is used (useful for quick demos).
    """
    user_message = data.get("message", "")
    session_id: Optional[str] = data.get("session_id")

    if session_id:
        session = SESSIONS.setdefault(session_id, {"step": "START"})
    else:
        # fallback single demo session
        session = SESSIONS.setdefault("__default__", {"step": "START"})

    reply = master_agent(user_message, session)

    response = {"reply": reply, "session_id": session_id or "__default__"}
    # Include a file link if a sanction PDF was created in this session
    if session.get("last_file"):
        response["file"] = session.get("last_file")
    # Also include last_reason/details for richer clients
    if session.get("last_reason"):
        response["last_reason"] = session.get("last_reason")
    if session.get("last_details"):
        response["last_details"] = session.get("last_details")

    return response
