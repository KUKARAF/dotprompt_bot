import subprocess
import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


def _load_commands():
    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)
    return config.get("commands", [])


def _run_command(cmd_config):
    result = subprocess.run(
        cmd_config["command"],
        shell=True,
        capture_output=True,
        text=True,
        timeout=cmd_config.get("timeout", 120),
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return f"Failed (exit {result.returncode}):\n{output}"
    return output if output else "Done (no output)"


def run_command(name: str):
    """Run a named command from config.toml.

    Parameters
    ----------
    name : str
        The command name to run. Available commands can be listed with list_commands().
    Returns
    -------
    str
        The command output.
    """
    commands = _load_commands()
    for cmd in commands:
        if cmd["name"] == name:
            return _run_command(cmd)
    available = ", ".join(c["name"] for c in commands)
    return f"Unknown command '{name}'. Available: {available}"


def list_commands():
    """List all available commands and their descriptions.

    Returns
    -------
    str
        A formatted list of command names and descriptions.
    """
    commands = _load_commands()
    if not commands:
        return "No commands configured in config.toml"
    lines = [f"- {c['name']}: {c['description']}" for c in commands]
    return "\n".join(lines)


list_commands.safe = True
