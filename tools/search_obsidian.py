"""
Tool: search_obsidian
Description: Search Obsidian vault using ripgrep
"""

import subprocess
import json
from pathlib import Path
import os

def execute(query: str, max_results: int = 5) -> dict:
    """
    Search Obsidian vault
    
    Args:
        query: Text to search for
        max_results: Max results to return
        
    Returns:
        {
            "results": [
                {
                    "file": "path/to/note.md",
                    "title": "Note Title",
                    "preview": "...matching text...",
                    "line": 42
                }
            ]
        }
    """
    vault_path = Path("/var/home/rafa/vimwiki/layer55")
    
    if not vault_path.exists():
        return {
            "error": f"Obsidian vault not found at {vault_path}",
            "results": []
        }
    
    try:
        # Use ripgrep for fast search
        result = subprocess.run(
            [
                "rg",
                "--json",
                "--max-count", str(max_results),
                "--context", "2",
                query,
                str(vault_path)
            ],
            capture_output=True,
            text=True
        )
        
        # Parse results
        results = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    results.append({
                        "file": data["data"]["path"]["text"],
                        "title": _extract_title(data["data"]["path"]["text"]),
                        "preview": data["data"]["lines"]["text"],
                        "line": data["data"]["line_number"]
                    })
            except json.JSONDecodeError:
                continue
        
        return {"results": results[:max_results]}
    
    except FileNotFoundError:
        return {
            "error": "ripgrep (rg) not found. Please install ripgrep.",
            "results": []
        }
    except Exception as e:
        return {"error": str(e), "results": []}

def _extract_title(file_path: str) -> str:
    """Extract note title from file path"""
    return Path(file_path).stem.replace("-", " ").title()

execute.safe = True
