import json
import time
import urllib.robotparser
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from scripts.derive import cache_key
from scripts.io import ROOT, read_csv

USER_AGENT = "FavouredBanksResearch/1.0 (+https://github.com/rgmwnn/geo-bank-visibility)"


def content_kind(content_type: str, url: str) -> str:
    ct = (content_type or "").lower()
    if "pdf" in ct or urlparse(url).path.lower().endswith(".pdf"):
        return "pdf"
    if "html" in ct or "xml" in ct:
        return "html"
    return "other"


def schedule(urls: list[str]) -> list[tuple[str, str]]:
    queues: dict[str, list[str]] = defaultdict(list)
    for u in urls:
        queues[urlparse(u).netloc].append(u)
    order = []
    while any(queues.values()):
        for host in list(queues):
            if queues[host]:
                order.append((host, queues[host].pop(0)))
    return order


def _robots_allows(rp_cache: dict, url: str) -> bool:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in rp_cache:
        rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        rp_cache[base] = rp
    rp = rp_cache[base]
    return True if rp is None else rp.can_fetch(USER_AGENT, url)


def fetch_all(urls: list[str], cache: Path, delay: float = 1.0, timeout: int = 20) -> None:
    import requests

    cache.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "id,en;q=0.8"})
    last_hit: dict[str, float] = {}
    robots: dict = {}
    for host, url in schedule(urls):
        key = cache_key(url)
        meta = {"url": url, "final_url": "", "http_status": None, "fetch_error": "", "content_type": "",
                "content_kind": "", "encoding": "", "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        wait = delay - (time.monotonic() - last_hit.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        try:
            if not _robots_allows(robots, url):
                meta["fetch_error"] = "robots_disallowed"
            else:
                r = session.get(url, timeout=timeout, allow_redirects=True)
                meta.update(final_url=r.url, http_status=r.status_code, content_type=r.headers.get("content-type", ""),
                            encoding=r.encoding or r.apparent_encoding or "utf-8")
                meta["content_kind"] = content_kind(meta["content_type"], r.url)
                if r.status_code == 200 and meta["content_kind"] in ("html", "pdf"):
                    (cache / f"{key}.bin").write_bytes(r.content)
        except Exception as e:
            meta["fetch_error"] = f"{type(e).__name__}: {str(e)[:200]}"
        last_hit[host] = time.monotonic()
        (cache / f"{key}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        print(meta["http_status"], meta["fetch_error"][:40], url, flush=True)


def main() -> None:
    urls = sorted(read_csv("data/interim/citations.csv")["url"].unique())
    fetch_all(urls, ROOT / ".cache/crawl")


if __name__ == "__main__":
    main()
