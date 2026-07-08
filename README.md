# Personal HR-Screening Voice Agent

🎥 **Here is a demo:** [watch the agent take a screening call](https://drive.google.com/file/d/1-kRtGCASSPWa09K8USVhTQ79TlB1CtiS/view?usp=sharing)

An AI voice agent that answers recruiter screening calls **on your behalf**. A recruiter talks to
it in natural speech, and it answers questions about your background — experience, skills,
projects — from your resume and portfolio. It introduces itself honestly as your AI assistant
(it doesn't pretend to be you), refuses to invent facts, and points callers to your email or
LinkedIn for anything it can't answer.

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

Try asking it: *"What technical skills do you have?"*, *"What projects have they worked
on?"*

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
requirements.txt             # Python deps
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

## Real phone calls (Twilio)

The agent also answers real phone calls. The STT → LLM → TTS core is identical — a phone call is
just a different transport, enabled with `-t twilio`. The agent hangs up on its own when the
caller says goodbye, or after two silence timeouts (a friendly check-in, then a farewell).

### 1. Twilio setup

1. Sign up at https://www.twilio.com/try-twilio (free trial credit) and buy a trial number.
2. From the [Console](https://console.twilio.com) dashboard's **Account Info** panel, copy your
   **Account SID** and **Auth Token** into `.env`:

   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxx
   ```

   (These let the agent terminate the call cleanly when it hangs up.)
3. Trial accounts only accept calls from **Verified Caller IDs** — your own number gets verified
   during signup; add others under Phone Numbers → Manage → Verified Caller IDs.

### 2. Expose the bot over HTTPS

Twilio streams call audio over a **secure websocket (`wss://`) and requires a valid TLS
certificate** — a bare IP or plain HTTP won't work. Two options:

**Option A — ngrok (quickest, for testing):**

```bash
ngrok http 7860                                  # note the https host it gives you
python bot.py -t twilio -x abc123.ngrok-free.app # -x = your public hostname, no scheme
```

**Option B — an always-on server (what a real deployment looks like, e.g. AWS EC2):**

1. On the server: clone the repo, create the venv, `pip install -r requirements.txt`.
2. Copy your personal files over manually — they're gitignored, so they don't come with the
   clone. Watch the destinations: `.env` belongs in the repo root, `about_me.md` inside
   `knowledge/` (anywhere else and the agent silently runs with no knowledge):

   ```bash
   scp .env user@server:personal_voice_agent/
   scp knowledge/about_me.md user@server:personal_voice_agent/knowledge/
   ```

3. **Give the server HTTPS (all free).** The bot itself only speaks plain HTTP on port 7860,
   but Twilio will only stream call audio to a URL with a real TLS certificate. Certificates are
   only issued to *domain names* — you can't get one for a bare IP, and Let's Encrypt won't issue
   one for Amazon's built-in `ec2-....amazonaws.com` names either. That sounds like you need to
   buy a domain, but you don't:

   - **A free hostname:** [sslip.io](https://sslip.io) gives every IP address a working hostname
     for free, with zero setup — the IP is simply written into the name. If your server's public
     IP is `2.130.19.188`, then `2-130-19-188.sslip.io` already points at it.
   - **A free certificate, automatically:** [Caddy](https://caddyserver.com) is a small web
     server you put in front of the bot. Given the two-line config below, it fetches a free
     Let's Encrypt certificate for that hostname on startup, renews it forever, and forwards the
     (decrypted) traffic to the bot on port 7860. No certbot, no cron jobs, no manual cert steps.

   Install Caddy, then put this in `/etc/caddy/Caddyfile` (swap in your own IP-hostname) and
   `sudo systemctl reload caddy`:

   ```
   2-130-19-188.sslip.io {
       reverse_proxy localhost:7860
   }
   ```

   Finally, open ports **80 and 443** in the instance's security group — 443 is where Twilio
   connects, and Caddy needs 80/443 reachable to prove to Let's Encrypt that it owns the
   hostname.

4. **Run the bot** (from the repo directory, venv activated), telling it its public hostname:

   ```bash
   python bot.py -t twilio -x 2-130-19-188.sslip.io   # swap in your own IP-hostname
   ```

   That's enough to test. To keep it running after you log out and across reboots, wrap that
   exact command in a systemd service — `ExecStart` pointing at the venv's python with the flags
   above, `WorkingDirectory` set to the repo, `Restart=always` — then
   `sudo systemctl enable --now` it.

5. Caveat: the sslip.io hostname encodes the IP — if the instance is stopped/started the public
   IP changes, and the Caddyfile, the `-x` flag in your run command (or systemd service), and
   the Twilio webhook all need the new one (attach an Elastic IP to avoid this).

Verify from anywhere: `curl -X POST https://<your-host>/` should return TwiML XML containing
`wss://<your-host>/ws`.

### 3. Point your Twilio number at it

Twilio Console → **Phone Numbers → Manage → Active numbers** → click your number → **Voice
Configuration** → under "A call comes in" choose **Webhook**, enter `https://<your-host>/` with
method **HTTP POST** → **Save configuration**. (Redo this whenever your host changes — e.g. a new
ngrok URL each session.)

### 4. Call it

Call your Twilio number from a verified phone. You'll hear the trial announcement (press a key if
prompted), then the agent picks up. Costs on trial: inbound minutes ~$0.01/min from your free
credit; the *caller* pays their own carrier's rate (international, if calling a US number from
abroad).
