# Personal HR-Screening Voice Agent

An AI voice agent that answers screening calls on your behalf. A recruiter talks to it, and it
answers questions about your background (experience, skills, projects) from your resume / portfolio.

**Stack (all free to start):** Pipecat · Deepgram (speech-to-text) · Groq/Llama (LLM brain) ·
Cartesia (text-to-speech). You test it **in your browser** first — no phone number needed.

```
your voice → Deepgram (STT) → Groq/Llama (brain + your info) → Cartesia (TTS) → speaker
```

## 1. Setup (once)

```powershell
# from the project folder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Windows fix for an onnxruntime DLL load error (used by the voice-activity detector):
pip install onnxruntime==1.19.2 --no-deps
```

## 2. Add your API keys

Copy `.env.example` to `.env` and paste in your three keys (all free):

| Key | Where to get it | Cost |
|-----|-----------------|------|
| `DEEPGRAM_API_KEY` | https://console.deepgram.com → API Keys | free signup credit |
| `GROQ_API_KEY` | https://console.groq.com/keys | free |
| `CARTESIA_API_KEY` | https://play.cartesia.ai → API Keys | free tier |

## 3. Add your info

Put your resume in `knowledge/resume.pdf`, then compile it (plus any links) into the agent's knowledge:

```powershell
python ingest.py --resume knowledge/resume.pdf --url https://your-portfolio.com --url https://github.com/yourname
```

This writes `knowledge/about_me.md`. Open it and tidy it up if you like — the agent reads it verbatim.
(You only re-run this when your resume/portfolio changes. You can also just edit `about_me.md` by hand.)

Set your name in `persona.py` (`OWNER_NAME`).

## 4. Talk to it

```powershell
python bot.py
```

Open the printed URL (http://localhost:7860), click **Connect**, allow the microphone, and start talking.

## Tweaking

- **Voice:** preview voices at https://play.cartesia.ai and set `CARTESIA_VOICE` in `bot.py`.
- **Persona / guardrails:** edit `persona.py`.
- **Smarter brain:** change `GROQ_MODEL` in `bot.py`, or swap `GroqLLMService` for Claude later.

## Later: real phone calls

This POC runs in the browser. To take real calls you add a telephony provider (Twilio): buy a number,
run a small server with Pipecat's `FastAPIWebsocketTransport` + `TwilioFrameSerializer`, and point the
number's webhook at it. The STT → LLM → TTS core stays exactly the same. (Not built yet — next phase.)
