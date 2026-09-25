"""Pexels video search and download.

Pexels returns preview frames (`video_pictures`) with every result, which is
what lets an agent look at candidates before one is used.
"""

from __future__ import annotations

import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

API = "https://api.pexels.com/videos/search"


@dataclass
class Candidate:
    id: int
    url: str
    duration: float
    width: int
    height: int
    previews: list[str]  # first, middle and last preview frame
    file_url: str
    file_width: int
    file_height: int
    author: str
    author_url: str
    query: str

    def to_dict(self) -> dict:
        return asdict(self)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["Authorization"] = os.environ["PEXELS_API_KEY"]
    return s


def pick_file(files: list[dict], width: int, height: int) -> dict | None:
    """The smallest rendition that covers the output frame, else the largest one."""
    usable = [f for f in files if f.get("width") and f.get("height") and f.get("link")]
    if not usable:
        return None
    covering = [f for f in usable if f["width"] >= width and f["height"] >= height]
    if covering:
        return min(covering, key=lambda f: f["width"] * f["height"])
    return max(usable, key=lambda f: f["width"] * f["height"])


def search(queries: list[str], min_duration: float, width: int, height: int, limit: int = 9) -> list[Candidate]:
    orientation = "portrait" if height > width else "landscape"
    session = _session()
    seen: set[int] = set()
    found: list[Candidate] = []
    per_query = max(3, math.ceil(limit / max(1, len(queries))) + 2)
    for query in queries:
        r = session.get(
            API,
            params={
                "query": query,
                "orientation": orientation,
                "per_page": per_query,
                "min_duration": math.ceil(min_duration),
            },
            timeout=30,
        )
        if r.status_code == 429:
            raise SystemExit("Pexels rate limit reached (200 requests per hour by default)")
        r.raise_for_status()
        for v in r.json().get("videos", []):
            if v["id"] in seen or v.get("duration", 0) < min_duration:
                continue
            f = pick_file(v.get("video_files", []), width, height)
            pictures = [p["picture"] for p in v.get("video_pictures", []) if p.get("picture")]
            if not f or not pictures:
                continue
            seen.add(v["id"])
            previews = [pictures[0], pictures[len(pictures) // 2], pictures[-1]]
            user = v.get("user") or {}
            found.append(
                Candidate(
                    id=v["id"], url=v.get("url", ""), duration=float(v["duration"]),
                    width=v["width"], height=v["height"], previews=previews,
                    file_url=f["link"], file_width=f["width"], file_height=f["height"],
                    author=user.get("name", ""), author_url=user.get("url", ""), query=query,
                )
            )
    # Interleave queries so the sheet is not all one query's results.
    by_query: dict[str, list[Candidate]] = {}
    for c in found:
        by_query.setdefault(c.query, []).append(c)
    mixed: list[Candidate] = []
    while any(by_query.values()) and len(mixed) < limit:
        for q in list(by_query):
            if by_query[q] and len(mixed) < limit:
                mixed.append(by_query[q].pop(0))
    return mixed


def download(url: str, dest: Path) -> Path:
    with _session().get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in r.iter_content(1 << 16):
                fh.write(chunk)
    return dest
