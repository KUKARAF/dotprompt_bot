# bash_help.py
import subprocess

def tldr(command: str):
    """Get concise command-line help and examples using tldr.
    
    Provides practical examples for common command-line tools.
    Use this when you need to know how to use a shell command.
    """
    try:
        result = subprocess.run(
            ['tldr', command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr or 'Command not found in tldr'}"
    except subprocess.TimeoutExpired:
        return "Error: tldr command timed out"
    except FileNotFoundError:
        return "Error: tldr not found in PATH"

tldr.safe = True  # Read-only operation
