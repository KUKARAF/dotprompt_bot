#!/usr/bin/env python3
"""
Ask tool - sends a question as a Telegram DM to an authorized user
and waits for their reply via file-based IPC with the bot.
"""

import os
import time
import json
import tomllib
import httpx
from pathlib import Path

ASK_DIR = Path("/tmp/dotprompt_ask")
CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


def _load_config():
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def ask(question):
    """
    Ask a clarifying question by sending a Telegram DM to an authorized user.

    Parameters
    ----------
    question : str
        The question to send to the authorized user.
    Returns
    -------
    str
        The user's answer.
    """
    config = _load_config()
    token = os.getenv("TELEGRAM_TOKEN")
    authorized_users = config["telegram"]["authorized_users"]

    if not token:
        return "(error: TELEGRAM_TOKEN not set)"
    if not authorized_users:
        return "(error: no authorized users configured in config.toml)"

    ASK_DIR.mkdir(exist_ok=True)

    question_id = str(int(time.time() * 1000))
    question_file = ASK_DIR / f"{question_id}.question"
    response_file = ASK_DIR / f"{question_id}.response"

    user_id = authorized_users[0]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    resp = httpx.post(url, json={
        "chat_id": user_id,
        "text": f"Question from bot:\n\n{question}",
        "reply_markup": {"force_reply": True},
    })
    msg_data = resp.json()

    if not msg_data.get("ok"):
        return f"(error sending message: {msg_data})"

    message_id = msg_data["result"]["message_id"]

    question_file.write_text(json.dumps({
        "question_id": question_id,
        "message_id": message_id,
        "chat_id": user_id,
        "question": question,
    }))

    timeout = 300
    start = time.time()
    while time.time() - start < timeout:
        if response_file.exists():
            answer = response_file.read_text().strip()
            question_file.unlink(missing_ok=True)
            response_file.unlink(missing_ok=True)
            return answer if answer else "(empty response)"
        time.sleep(1)

    question_file.unlink(missing_ok=True)
    return "(no response received within 5 minutes)"


ask.safe = True

if __name__ == "__main__":
    answer = ask("What's your name?")
    print(f"Answer: {answer}")
