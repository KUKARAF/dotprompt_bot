import datetime as dt
import os
import tomllib
from pathlib import Path
from typing import Dict

CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


def _load_config():
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def get_todos() -> Dict[str, str]:
    """
    Return the contents of today's todo file.
    """
    config = _load_config()
    base = os.path.expanduser(config.get("paths", {}).get("diary", "~/diary"))
    path = f"{base}/{dt.datetime.now().strftime('%Y-%m-%d')}.md"

    if not os.path.exists(path):
        raise FileNotFoundError("Today's file not present.")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def calculate(expression: str):
    """Evaluates a mathematical expression.
    
    Use this for arithmetic calculations.
    """
    return eval(expression)

get_todos.safe = True
calculate.safe = True


if __name__ == "__main__":
    print(get_todos())
