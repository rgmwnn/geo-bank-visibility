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


def needs_render(meta: dict, n_words: int, min_words: int) -> bool:
    return meta.get("http_status") == 200 and meta.get("content_kind") == "html" and n_words < min_words


def retry_wait(headers: dict, default: int = 5, cap: int = 30) -> int:
    value = str(headers.get("Retry-After", "")).strip()
    return min(int(value), cap) if value.isdigit() else default


def by_host(urls: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for u in urls:
        groups[urlparse(u).netloc].append(u)
    return dict(groups)


def robots_decision(get, url: str, cache: dict, timeout: int = 10) -> tuple[bool, str]:
    """RFC 9309: 2xx parse rules, 4xx allow all, 5xx or network error assume full disallow."""
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in cache:
        try:
            r = get(base + "/robots.txt", timeout=timeout)
            if 200 <= r.status_code < 300:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(r.text.splitlines())
                cache[base] = rp
            elif 400 <= r.status_code < 500:
                cache[base] = "allow"
            else:
                cache[base] = "unreachable"
        except Exception:
            cache[base] = "unreachable"
    rule = cache[base]
    if rule == "allow":
        return True, ""
    if rule == "unreachable":
        return False, "robots_unreachable"
    return (True, "") if rule.can_fetch(USER_AGENT, url) else (False, "robots_disallowed")


def _fetch_host(urls: list[str], cache: Path, delay: float, timeout: int) -> None:
    import requests

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "id,en;q=0.8"})
    robots: dict = {}
    last = 0.0
    for url in urls:
        key = cache_key(url)
        meta = {"url": url, "final_url": "", "http_status": None, "fetch_error": "", "content_type": "",
                "content_kind": "", "encoding": "", "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        wait = delay - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        try:
            allowed, reason = robots_decision(session.get, url, robots, timeout=min(timeout, 10))
            if not allowed:
                meta["fetch_error"] = reason
            else:
                r = session.get(url, timeout=timeout, allow_redirects=True)
                if r.status_code == 429:
                    time.sleep(retry_wait(r.headers))
                    r = session.get(url, timeout=timeout, allow_redirects=True)
                meta.update(final_url=r.url, http_status=r.status_code, content_type=r.headers.get("content-type", ""),
                            encoding=r.encoding or r.apparent_encoding or "utf-8")
                meta["content_kind"] = content_kind(meta["content_type"], r.url)
                if r.status_code == 200 and meta["content_kind"] in ("html", "pdf"):
                    (cache / f"{key}.bin").write_bytes(r.content)
        except Exception as e:
            meta["fetch_error"] = f"{type(e).__name__}: {str(e)[:200]}"
        last = time.monotonic()
        (cache / f"{key}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        print(meta["http_status"], meta["fetch_error"][:40], url, flush=True)


def fetch_all(urls: list[str], cache: Path, delay: float = 1.0, timeout: int = 20, workers: int = 8) -> None:
    from concurrent.futures import ThreadPoolExecutor

    cache.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for f in [pool.submit(_fetch_host, group, cache, delay, timeout) for group in by_host(urls).values()]:
            f.result()


def render_short_pages(cache: Path, min_words: int, timeout_ms: int = 30000) -> None:
    """Pages built by JavaScript return almost no text in their raw HTML. Render those in headless Chromium."""
    from playwright.sync_api import sync_playwright

    from scripts.derive import extract_html

    todo = []
    for meta_path in sorted(cache.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        body = cache / f"{meta_path.stem}.bin"
        if not body.exists():
            continue
        html = body.read_bytes().decode(meta.get("encoding") or "utf-8", errors="replace")
        if needs_render(meta, extract_html(html, meta["url"])["n_words"], min_words):
            todo.append((meta_path, meta))
    print(f"rendering {len(todo)} short pages", flush=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(user_agent=USER_AGENT, locale="id-ID")
        for meta_path, meta in todo:
            page = context.new_page()
            try:
                page.goto(meta["url"], wait_until="networkidle", timeout=timeout_ms)
                (cache / f"{meta_path.stem}.rendered.html").write_text(page.content(), encoding="utf-8")
                meta["rendered"] = True
            except Exception as e:
                meta["render_error"] = f"{type(e).__name__}: {str(e)[:120]}"
            finally:
                page.close()
            meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            print("rendered" if meta.get("rendered") else "render failed", meta["url"], flush=True)
        browser.close()


def main() -> None:
    from scripts.io import load_config

    urls = sorted(read_csv("data/interim/citations.csv")["url"].unique())
    fetch_all(urls, ROOT / ".cache/crawl")
    render_short_pages(ROOT / ".cache/crawl", load_config()["readable_min_words"])


if __name__ == "__main__":
    main()
