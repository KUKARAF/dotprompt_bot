import platform
import psutil
from typing import Dict, Any

def run() -> Dict[str, Any]:
    """Collect basic system information.

    Returns
    -------
    dict
        A dictionary containing OS, release, version, CPU count, and memory stats.
    """
    info: Dict[str, Any] = {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(logical=True),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "used": psutil.virtual_memory().used,
            "percent": psutil.virtual_memory().percent,
        },
    }
    return info

# This tool only reads system information, so it is safe.
run.safe = True
