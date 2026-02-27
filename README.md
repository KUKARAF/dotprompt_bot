# DotPrompt Bot

A Telegram bot that dynamically loads capabilities from `.prompt` files. Instead of hardcoding features, the bot discovers prompt files at startup and routes messages to the right one using an LLM router. Add new capabilities by dropping in a `.prompt` file and a matching tool — no code changes needed.

## How It Works

```
User Message → Router Prompt → Selected Prompt → Tool(s) → Response
```

1. **Router** (`prompts/router.prompt`) — an LLM reads the user's message and picks which prompt should handle it
2. **Prompt execution** — the selected `.prompt` file runs via `runprompt` with access to its declared tools
3. **Direct answer** — if no prompt matches, the router answers directly (greetings, chitchat, etc.)

Voice messages are transcribed via Groq Whisper before routing.

## Quick Start

### Prerequisites

- Python 3.11+
- [`runprompt`](https://github.com/corbt/runprompt) CLI installed and on PATH
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An [OpenRouter](https://openrouter.ai) API key (or swap the model in `.runprompt/config.yml`)
- A [Groq](https://console.groq.com) API key (for voice transcription)

### Setup

```bash
# Clone / use template
git clone <your-repo-url>
cd dotprompt_bot

# Create a virtualenv and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and edit configuration files
cp .env.example .env          # add your API keys
cp example.config.toml config.toml  # set your Telegram user ID & commands

# Run
python bot.py
```

### Running as a systemd service

A user service file is included at `.config/systemd/user/dotprompt-bot.service`. It expects the bot to live at `~/env/dotprompt_bot`. Adjust `WorkingDirectory` and `ExecStart` paths as needed, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now dotprompt-bot
```

## Fork & Make It Your Own

This repo is designed to be forked (or used as a GitHub template). Here's what to customize:

### 1. `.env` — your secrets

Copy `.env.example` to `.env` and fill in your keys:

| Variable | Required | Where to get it |
|----------|----------|----------------|
| `TELEGRAM_TOKEN` | Yes | [@BotFather](https://t.me/BotFather) on Telegram |
| `GROQ_API_KEY` | Yes | [console.groq.com](https://console.groq.com) |
| `OPENROUTER_API_KEY` | Yes | [openrouter.ai](https://openrouter.ai) |
| `JINA_API_KEY` | No | [jina.ai](https://jina.ai) — needed for `jina` web reading tool |

### 2. `config.toml` — your identity, paths & commands

Copy `example.config.toml` to `config.toml`:

- Set `authorized_users` to your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))
- Set `[paths]` to point to your notes vault and diary directory
- Add shell commands you want the bot to run on your behalf

### 3. `.runprompt/config.yml` — your LLM

Change the `model` field to use any LLM provider supported by `runprompt`.

### 4. `prompts/` — your capabilities

Delete the prompts you don't need, add your own. The router discovers them automatically.

## Adding a New Capability

1. **Create a tool** in `tools/` — a Python file with functions:

```python
# tools/weather.py
import requests

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    resp = requests.get(f"https://wttr.in/{city}?format=3")
    return resp.text

get_weather.safe = True  # mark read-only tools as safe
```

2. **Create a prompt** in `prompts/`:

```yaml
---
name: weather
description: Get weather information for a city
model: openrouter/openai/gpt-4o-mini
tools:
  - weather.*
input:
  schema:
    city: string
output:
  format: text
---
Get the weather for {{city}} and give a brief summary.
```

3. Restart the bot. The router will automatically discover and route to your new prompt.

## Project Structure

```
dotprompt_bot/
├── bot.py                  # Main entry point
├── config.toml             # Your config (gitignored)
├── example.config.toml     # Config template
├── .env                    # Your secrets (gitignored)
├── .env.example            # Secrets template
├── .runprompt/
│   └── config.yml          # Default LLM model & tool path
├── prompts/                # Prompt files (auto-discovered)
│   ├── router.prompt       # Message router
│   ├── bash.prompt         # Run shell commands from config.toml
│   ├── obsidian.prompt     # Search notes vault
│   └── estimate_today.prompt
└── tools/                  # Python tools available to prompts
    ├── ask.py              # Ask authorized user a question via Telegram
    ├── bash.py             # Run configured shell commands
    ├── search_obsidian.py  # Search notes with ripgrep
    ├── todo.py             # Read daily diary/todo files
    ├── calendar.py         # Google Calendar via gog CLI
    ├── jina.py             # Web reading & search via Jina AI
    ├── searxng_search.py   # Web search via SearxNG
    └── ...
```
