# Groot — Personal AI Assistant

A Jarvis-style always-on voice assistant. Say the wake word, speak naturally. Groot controls your Tesla Model 3 and manages your calendars.

## Architecture

```
Wake word (Porcupine) → Whisper STT → Claude claude-sonnet-4-6 (tool use) → System TTS
                                              ↕
                                 Tesla API | Google Cal | Apple iCloud Cal
```

## Features

- Always-on wake word detection (low CPU, runs on-device)
- Offline speech recognition via Whisper (no cloud STT)
- Full conversation memory within a session
- Tesla Model 3: status, climate, lock/unlock, charging, horn, lights
- Google Calendar + Apple iCloud Calendar: read and create events
- System TTS: macOS `say` or Linux `espeak` — no extra API key needed

## Setup

### 1. Install system dependencies

**macOS:**
```bash
brew install portaudio
```

**Linux:**
```bash
sudo apt install portaudio19-dev espeak
```

### 2. Install Python packages

```bash
pip install -r requirements.txt
```

### 3. API keys

Copy `.env.example` to `.env` and fill in:

| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `PICOVOICE_ACCESS_KEY` | [console.picovoice.ai](https://console.picovoice.ai) — free personal tier |

### 4. Google Calendar

1. [Google Cloud Console](https://console.cloud.google.com) → New project → Enable **Google Calendar API**
2. Create **OAuth 2.0 credentials** (Desktop app type) → download JSON
3. Save as `google_credentials.json` in the project root

A browser window will open on first run to authorize access.

### 5. Apple Calendar

1. Sign in at [appleid.apple.com](https://appleid.apple.com/account/manage)
2. Security → **App-Specific Passwords** → Generate one
3. Set `APPLE_ID` and `APPLE_APP_PASSWORD` in `.env`

### 6. Tesla

No pre-setup needed. On first run `teslapy` will prompt for your Tesla account credentials and cache a refresh token locally.

### 7. Custom wake word (optional)

The default keyword is `jarvis` (built into Porcupine). To use **Groot**:

1. Log in at [console.picovoice.ai](https://console.picovoice.ai)
2. Porcupine → Train a model → enter "Groot"
3. Download the `.ppn` file for your platform (Mac or Linux)
4. In `config.yaml` set:
   ```yaml
   wake_word:
     custom_model_path: "models/groot_mac.ppn"
   ```

## Run

```bash
python groot.py
```

Say your wake word (default: **"Jarvis"**), then speak naturally. Say *"Goodnight"* or *"That's all"* to return to standby.

## Example commands

- "How's the car doing?"
- "Turn on the heat, set it to 72"
- "Lock the Tesla"
- "Start charging"
- "What's on my calendar this week?"
- "Schedule a meeting with Sarah tomorrow at 2pm"
- "What time is it?"

## Extending Groot

Drop a new file in `integrations/`, add tool definitions to `tools/registry.py`, and Claude will automatically discover and use them. No changes to the main loop needed.
