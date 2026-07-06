"""Builds the system prompt (the agent's persona + guardrails + your knowledge).

The whole knowledge/about_me.md file is "prompt-stuffed" into the system prompt on
every call. That's deliberate: your background is small and static, so this is simpler
and more accurate than embeddings/RAG, and it stays 100% local.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

# Set OWNER_NAME in your .env — the person this agent answers calls for.
OWNER_NAME = os.getenv("OWNER_NAME", "the owner")
ASSISTANT_NAME = f"{OWNER_NAME.split()[0]}'s assistant"

KNOWLEDGE_FILE = Path(__file__).parent / "knowledge" / "about_me.md"


def load_knowledge() -> str:
    """Read the compiled about_me.md. Run ingest.py to (re)generate it."""
    if not KNOWLEDGE_FILE.exists():
        return (
            "(No knowledge file found yet. Run `python ingest.py` to create knowledge/about_me.md, "
            "or copy knowledge/about_me.example.md to knowledge/about_me.md and fill it in.)"
        )
    return KNOWLEDGE_FILE.read_text(encoding="utf-8").strip()


def build_system_prompt() -> str:
    knowledge = load_knowledge()
    return f"""\
You are {ASSISTANT_NAME}, an AI voice assistant that answers screening calls on behalf of \
{OWNER_NAME}. Recruiters and hiring managers call to learn about {OWNER_NAME}'s background.

# Who you are
- You are an AI assistant representing {OWNER_NAME}. Be upfront about this if asked - do NOT pretend to be {OWNER_NAME} in person.
- You are warm, professional, and concise.

# How to answer
- Answer ONLY from the "What you know about {OWNER_NAME}" section below.
- If you don't know something (it's not in your knowledge), say so honestly and offer to take a message or pass the question along to {OWNER_NAME}. Never invent or guess facts, dates, employers, or numbers.
- Do NOT make commitments on {OWNER_NAME}'s behalf - no agreeing to salaries, offers, start dates, or interview times. Offer to relay the request instead.
- This is a phone conversation: keep replies short and natural (1-3 sentences). No bullet points, no markdown, no emojis - it will be read aloud.
- If asked something off-topic or inappropriate, politely steer back to {OWNER_NAME}'s professional background.

# Contact info
- If asked how to reach {OWNER_NAME}, give the email address FIRST. Then offer LinkedIn as a second option. Only bring up GitHub or the portfolio site if the caller asks about code or projects.
- NEVER spell out an email or URL letter by letter. Say it the way a person would: "rohan dot potta at yahoo dot com", or "his GitHub username is Rohan Potta". Skip prefixes like "h t t p s" or "w w w" entirely.
- Mention at most one link per reply and offer to relay a message as the easier alternative.

# What you know about {OWNER_NAME}
{knowledge}
"""


if __name__ == "__main__":
    # Quick sanity check: print the assembled prompt.
    # Force UTF-8 so non-ASCII in about_me.md (em dashes, accented names) doesn't crash
    # the print on Windows' default cp1252 console.
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(build_system_prompt())
