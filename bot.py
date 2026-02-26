#!/usr/bin/env python3
"""
DotPrompt Bot - Telegram bot that delegates to runprompt subagents
"""

import os
import json
import asyncio
import tempfile
import tomllib
import yaml
from pathlib import Path
from groq import Groq
from telegram.ext import ApplicationBuilder, ApplicationHandlerStop, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path("prompts")
ROUTER_PROMPT = PROMPTS_DIR / "router.prompt"
ASK_DIR = Path("/tmp/dotprompt_ask")
CONFIG_PATH = Path(__file__).parent / "config.toml"


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def discover_prompts() -> dict:
    """Read .prompt files and extract name + description from YAML frontmatter."""
    prompts = {}
    for prompt_file in PROMPTS_DIR.glob("*.prompt"):
        if prompt_file.name == "router.prompt":
            continue
        try:
            content = prompt_file.read_text()
            parts = content.split("---")
            if len(parts) >= 3:
                config = yaml.safe_load(parts[1])
                name = prompt_file.stem
                prompts[name] = {
                    "description": config.get("description", ""),
                    "file": str(prompt_file),
                }
        except Exception as e:
            print(f"Warning: failed to load {prompt_file}: {e}")
    return prompts


async def run_prompt(prompt_file: str, input_data: dict, tool_path: str = None) -> str:
    """Run a .prompt file via runprompt subprocess."""
    cmd = ["runprompt", "--safe-yes"]
    if tool_path:
        cmd.extend(["--tool-path", tool_path])
    cmd.append(prompt_file)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate(json.dumps(input_data).encode())

    if proc.returncode != 0:
        raise RuntimeError(f"runprompt failed (exit {proc.returncode}): {stderr.decode()}")

    return stdout.decode().strip()


async def route_and_respond(update: Update, context, user_message: str):
    """Route a message through the prompt system and reply."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        prompts = discover_prompts()
        prompt_list = "\n".join(
            f"- {name}: {info['description']}" for name, info in prompts.items()
        )

        router_input = {"message": user_message, "prompts": prompt_list}
        router_output = await run_prompt(str(ROUTER_PROMPT), router_input)

        decision = json.loads(router_output)
        print(f"Router decision: {decision}")

        selected_prompt = decision.get("prompt")

        if selected_prompt and selected_prompt in prompts:
            prompt_input = decision.get("input", {})
            response = await run_prompt(
                prompts[selected_prompt]["file"],
                prompt_input,
                tool_path="./tools",
            )
        else:
            response = decision.get("answer", "I'm not sure how to handle that.")

        await update.message.reply_text(response)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(f"Sorry, something went wrong: {e}")


async def handle_ask_reply(update: Update, context):
    """Check if this message is a reply to a pending ask question from an authorized user."""
    if not update.message or not update.message.reply_to_message:
        return

    config = load_config()
    authorized_users = config.get("telegram", {}).get("authorized_users", [])

    if update.effective_user.id not in authorized_users:
        return

    reply_to_id = update.message.reply_to_message.message_id
    chat_id = update.effective_chat.id

    if not ASK_DIR.exists():
        return

    for qfile in ASK_DIR.glob("*.question"):
        try:
            data = json.loads(qfile.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if data["message_id"] == reply_to_id and data["chat_id"] == chat_id:
            response_file = ASK_DIR / f"{data['question_id']}.response"
            response_file.write_text(update.message.text)
            await update.message.reply_text("Got it, thanks!")
            raise ApplicationHandlerStop


async def handle_message(update: Update, context):
    """Handle incoming text message."""
    user_message = update.message.text
    print(f"Received: {user_message}")
    await route_and_respond(update, context, user_message)


async def handle_voice(update: Update, context):
    """Handle incoming voice/audio message: transcribe via Groq STT then route."""
    print("Received voice message")

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
        await file.download_to_drive(tmp_path)

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                language="en",
                temperature=0.0,
            )

        text = transcription.text.strip()
        print(f"Transcribed: {text}")

        if not text:
            await update.message.reply_text("Couldn't understand the audio.")
            return

        await route_and_respond(update, context, text)

    finally:
        os.unlink(tmp_path)


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN not set in environment")
        return

    print("Starting DotPrompt Bot...")
    prompts = discover_prompts()
    print(f"Discovered prompts: {list(prompts.keys())}")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY & ~filters.COMMAND, handle_ask_reply), group=-1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("Bot is running.")
    app.run_polling()


if __name__ == "__main__":
    main()
