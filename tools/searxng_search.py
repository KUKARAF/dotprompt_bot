import requests
from typing import List, Dict


def search_searxng(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """Search the public SearxNG instance at ``https://searx.osmosis.page``.

    The function performs a GET request to the SearxNG search endpoint with
    ``format=json`` which returns a lightweight JSON payload.  The payload
    contains a list of results; each result is reduced to a dictionary with the
    keys ``title``, ``url`` and ``snippet``.

    Parameters
    ----------
    query: str
        The search query.
    limit: int, optional
        Maximum number of results to return (default 5).  The SearxNG API
        respects the ``num`` parameter for limiting results.

    Returns
    -------
    List[Dict[str, str]]
        A list of dictionaries, each containing ``title``, ``url`` and
        ``snippet`` fields.  If the request fails or the response cannot be
        parsed, an empty list is returned.
    """
    base_url = "https://searx.osmosis.page/search"
    params = {
        "q": query,
        "format": "json",
        "num": limit,
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            })
        return results
    except Exception as e:
        # In a real‑world tool you might log the error; here we simply return []
        return []

# Mark the tool as safe – it only performs a read‑only HTTP GET.
search_searxng.safe = True
