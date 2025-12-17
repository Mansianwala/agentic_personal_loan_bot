"""Lightweight OpenAI wrapper used by agents POST chat mode.

Usage:
 - Set environment variable `OPENAI_API_KEY` before running the app.
 - The wrapper will return None if OpenAI is not available or not configured.
"""
import os
import logging

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    openai = None
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


def is_configured():
    return OPENAI_AVAILABLE and bool(os.environ.get("OPENAI_API_KEY"))


def generate_chat_reply(user_message: str, session_context: dict | None = None, model: str = "gpt-3.5-turbo") -> str | None:
    """Return a short assistant reply using OpenAI ChatCompletion. Returns None if not available.

    session_context can include last_details, last_reason, or other info to help the model.
    """
    if not is_configured():
        return None

    try:
        openai.api_key = os.environ.get("OPENAI_API_KEY")

        system_prompt = (
            "You are a helpful, concise financial assistant for a personal loan application system. "
            "Answer user questions politely, explain decisions briefly, and offer next steps. "
            "Do not produce PII or store data. If you are unsure, ask a clarifying question."
        )

        # craft messages
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]

        # add context if available
        if session_context:
            ctx_parts = []
            if session_context.get("last_reason"):
                ctx_parts.append(f"Last decision reason: {session_context.get('last_reason')}")
            details = session_context.get("last_details")
            if details:
                parts = []
                if details.get("emi") is not None:
                    parts.append(f"EMI: {int(details.get('emi'))}")
                if details.get("preapproved_limit") is not None:
                    parts.append(f"Preapproved limit: {int(details.get('preapproved_limit'))}")
                if parts:
                    ctx_parts.append("; ".join(parts))
            if ctx_parts:
                messages.insert(1, {"role": "system", "content": "Context: " + " | ".join(ctx_parts)})

        resp = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=150, temperature=0.6)
        text = resp["choices"][0]["message"]["content"].strip()
        return text
    except Exception as e:
        logger.exception("OpenAI call failed: %s", e)
        return None
