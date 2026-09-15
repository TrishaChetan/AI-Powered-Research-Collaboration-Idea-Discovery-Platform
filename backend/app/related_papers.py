"""
Related Papers Finder — queries arXiv's free, public, no-key-required API
to find real papers related to an uploaded paper's title/topic.

API docs: https://info.arxiv.org/help/api/user-manual.html
"""
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def search_related_papers(query: str, max_results: int = 5) -> List[Dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    try:
        resp = requests.get(ARXIV_API_URL, params=params, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"arXiv search failed: {e}") from e

    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title = entry.findtext(f"{ATOM_NS}title", default="").strip().replace("\n", " ")
        summary = entry.findtext(f"{ATOM_NS}summary", default="").strip().replace("\n", " ")
        published = entry.findtext(f"{ATOM_NS}published", default="")
        url = entry.findtext(f"{ATOM_NS}id", default="")
        authors = [
            a.findtext(f"{ATOM_NS}name", default="").strip()
            for a in entry.findall(f"{ATOM_NS}author")
        ]
        results.append({
            "title": title,
            "authors": authors,
            "summary": summary[:400] + ("…" if len(summary) > 400 else ""),
            "url": url,
            "published": published[:10],  # just the date
        })
    return results
