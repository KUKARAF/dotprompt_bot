import subprocess


def get_today_events() -> str:
    """
    Return today's Google Calendar events using gog cli.
    """
    result = subprocess.run(
        ["gog", "cal", "events", "--today", "--all", "--plain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gog failed: {result.stderr.strip()}")
    return result.stdout.strip() or "No events today."


get_today_events.safe = True


def get_tomorrow_events() -> str:
    """
    Return tomorrow's Google Calendar events using gog cli.
    """
    result = subprocess.run(
        ["gog", "cal", "events", "--tomorrow", "--all", "--plain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gog failed: {result.stderr.strip()}")
    return result.stdout.strip() or "No events tomorrow."


get_tomorrow_events.safe = True


def get_week_events() -> str:
    """
    Return this week's Google Calendar events using gog cli.
    """
    result = subprocess.run(
        ["gog", "cal", "events", "--week", "--all", "--plain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gog failed: {result.stderr.strip()}")
    return result.stdout.strip() or "No events this week."


get_week_events.safe = True

if __name__ == "__main__":
    print(get_today_events())
