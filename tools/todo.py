import datetime as dt
import os
from typing import Dict

def get_todos() -> Dict[str, str]:
    """
    Return the contents of today's todo file.
    """
    # Build path of today's todo file
    base = os.path.expanduser('~/vimwiki/diary')
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
