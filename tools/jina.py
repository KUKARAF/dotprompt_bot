import urllib.request
import urllib.parse

import os
import requests

def _jina_api_key() -> str:
    key = os.environ.get('JINA_API_KEY')
    if not key:
        raise EnvironmentError("JINA_API_KEY environment variable is not set")
    return key

def fetch_url(url: str) -> str:
    """Fetch readable text content from a URL using Jina AI reader.
    
    Returns clean markdown-formatted page content suitable for analysis.
    Use this for every link you want to read.
    """
    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(jina_url, headers={"User-Agent": "runprompt/1.0", "Authorization": f"Bearer {_jina_api_key()}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

fetch_url.safe = True


def search_web(query: str) -> str:
    """Search the web and return results including titles, URLs and snippets.

    Returns a JSON string with a list of search results.
    Each result has: title, url, description.
    """
    import json
    encoded = urllib.parse.quote(query)
    jina_url = f"https://s.jina.ai/?q={encoded}"
    req = urllib.request.Request(jina_url, headers={
        "User-Agent": "runprompt/1.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {_jina_api_key()}",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

search_web.safe = True
