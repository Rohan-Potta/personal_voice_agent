# Personal HR-Screening Voice Agent

An AI voice agent that answers recruiter screening calls **on your behalf**. A recruiter talks to
it in natural speech, and it answers questions about your background — experience, skills,
projects, availability — from your resume and portfolio. It introduces itself honestly as your AI
assistant (it doesn't pretend to be you), refuses to invent facts, and offers to take a message
for anything it doesn't know.

You test it **in your browser** — no phone number needed.

```
caller's voice ──► Deepgram (speech-to-text) ──► Groq/Llama (brain + your info) ──► Cartesia (text-to-speech) ──► speaker
```

Built on [Pipecat](https://github.com/pipecat-ai/pipecat). Every provider is on a free tier, so
running the POC costs ~$0.

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/Rohan-Potta/personal_voice_agent.git
cd personal_voice_agent
python -m venv .venv
```

Activate the venv:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

**Windows only** — if `bot.py` later fails with a "DLL initialization routine failed" error from
onnxruntime, pin the older runtime (same functionality for the voice-activity detector):

```bash
pip install onnxruntime==1.19.2 --no-deps
```

### 2. Configure your name + API keys

Copy `.env.example` to `.env`, set `OWNER_NAME` to your full name, and paste in your three keys
(all free):

| Key | Where to get it | Cost |
|-----|-----------------|------|
| `DEEPGRAM_API_KEY` | https://console.deepgram.com → API Keys | free signup credit |
| `GROQ_API_KEY` | https://console.groq.com/keys | free |
| `CARTESIA_API_KEY` | https://play.cartesia.ai → API Keys | free tier |

`.env` is gitignored — your keys and name never get committed.

### 3. Add your info

The agent answers only from one local file: `knowledge/about_me.md` (gitignored, so your personal
info stays on your machine). Create it one of two ways:

**Option A — generate it from your resume / links:**

```bash
python ingest.py --resume knowledge/resume.pdf --url https://your-portfolio.com --url https://github.com/yourname
```

**Option B — write it by hand:**

```bash
cp knowledge/about_me.example.md knowledge/about_me.md
# then open it and fill in each section
```

Either way, open `knowledge/about_me.md` afterwards and tidy it up — the agent reads it verbatim,
so the cleaner it is, the better the agent sounds. Re-run/re-edit only when your info changes.

### 4. Talk to it

```bash
python bot.py
```

Open http://localhost:7860, click **Connect**, allow the microphone, and start talking. The bot
greets you first; there's no push-to-talk — just speak, and the conversation transcript appears
live in the page.

Try asking it: *"How many years of experience do they have?"*, *"What projects have they worked
on?"*, *"How do I get in touch?"* — and something that's NOT in your file, to confirm it admits
not knowing instead of making things up.

## Customizing

- **Voice:** preview voices at https://play.cartesia.ai and paste a voice ID into
  `CARTESIA_VOICE` in `bot.py`.
- **Brain:** change `GROQ_MODEL` in `bot.py`, or swap `GroqLLMService` for any other Pipecat LLM
  service (e.g. Claude) — it's a one-class change.
- **Persona & guardrails:** edit the system prompt in `persona.py` (tone, what it may promise,
  how it handles contact info, etc.).
- **Greeting:** edit the `on_client_connected` handler in `bot.py`.

## Project structure

```
.env.example                 # template for your name + API keys (copy to .env)
requirements.txt             # pinned Python deps
ingest.py                    # one-time: resume PDF + URLs -> knowledge/about_me.md
persona.py                   # system prompt: persona, guardrails, loads your knowledge
bot.py                       # the Pipecat pipeline + dev server (entry point)
knowledge/
  about_me.example.md        # template for your background (committed)
  about_me.md                # YOUR background — gitignored, created by you
```

## Troubleshooting

- **`ModuleNotFoundError` when running `bot.py`** — your venv isn't activated. Activate it (step 1)
  and try again.
- **`http://localhost:7860` returns 404 / "Prebuilt frontend not available"** — the
  `pipecat-ai-prebuilt` package is missing; `pip install -r requirements.txt` inside the venv.
- **Bot connects but never hears you** — check the mic mute button in the page (red = muted), make
  sure the right microphone is selected in the Devices dropdown, and close other tabs that are
  holding the mic (browser shows "Microphone in use").
- **onnxruntime DLL error on Windows** — see the pin command in step 1.

## Roadmap: real phone calls

This POC runs in the browser. To answer real calls, add a telephony provider (e.g. Twilio): buy a
number, run a small server using Pipecat's `FastAPIWebsocketTransport` + `TwilioFrameSerializer`,
and point the number's webhook at it. The STT → LLM → TTS core stays exactly the same.
