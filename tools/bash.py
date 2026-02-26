import subprocess


def deploy_costwise():
    """Pull latest images and restart the Costwise stack."""
    result = subprocess.run(
        "cd /home/rafa/env/layer55/costwise && docker compose pull && docker compose restart",
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        return f"Failed (exit {result.returncode}):\n{output}"
    return f"Done:\n{output}"
