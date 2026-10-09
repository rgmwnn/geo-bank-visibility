import hashlib
import json
import re
from io import BytesIO
from pathlib import Path

import pandas as pd

from scripts.brands import credit, find_matches, load_brands
from scripts.io import ROOT, load_config, read_csv, write_csv

ARTICLE_TYPES = {"Article", "NewsArticle", "BlogPosting", "Report"}
FAQ_TYPES = {"FAQPage"}
ORG_TYPES = {"Organization", "BankOrCreditUnion", "FinancialService", "Corporation"}
SOFT_404_RE = re.compile(r"\b404\b|not found|error page|tidak ditemukan", re.IGNORECASE)


def cache_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _walk_jsonld(node, types: list, dates: list) -> None:
    if isinstance(node, list):
        for n in node:
            _walk_jsonld(n, types, dates)
    elif isinstance(node, dict):
        t = node.get("@type")
        types.extend(t if isinstance(t, list) else [t] if t else [])
        if node.get("datePublished"):
            dates.append(str(node["datePublished"]))
        for v in node.values():
            if isinstance(v, (list, dict)):
                _walk_jsonld(v, types, dates)


def _iso_date(value: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def extract_html(html: str, url: str) -> dict:
    import trafilatura
    from bs4 import BeautifulSoup
    from htmldate import find_date

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    types, dates = [], []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            _walk_jsonld(json.loads(tag.string or ""), types, dates)
        except (json.JSONDecodeError, TypeError):
            continue
    published, source = "", ""
    jd = next((d for d in map(_iso_date, dates) if d), "")
    if jd:
        published, source = jd, "jsonld"
    else:
        meta = soup.find("meta", attrs={"property": "article:published_time"})
        md = _iso_date(meta.get("content", "")) if meta else ""
        if md:
            published, source = md, "meta"
        else:
            try:
                hd = find_date(html, original_date=True, extensive_search=False, outputformat="%Y-%m-%d")
            except Exception:
                hd = None
            if hd:
                published, source = hd, "htmldate"
    text = trafilatura.extract(html, url=url, include_comments=False) or ""
    return {"title": title, "text": text, "n_words": len(text.split()), "published_date": published,
            "date_source": source, "schema_types": sorted({str(t) for t in types})}


def extract_pdf(data: bytes, max_pages: int) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    n_pages = len(reader.pages)
    parts = []
    for page in reader.pages[:max_pages]:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(parts)
    return {"text": text, "n_words": len(text.split()), "n_pages": n_pages}


def page_row(meta: dict, extracted: dict, min_words: int, near_crawl_days: int = 3) -> dict:
    types = set(extracted.get("schema_types") or [])
    published, date_source = extracted.get("published_date", ""), extracted.get("date_source", "")
    if date_source == "htmldate" and published and meta.get("fetched_at"):
        # htmldate falls back to build or crawl dates when a page states none; a date that close to the crawl is not a publish date
        gap = abs((pd.Timestamp(meta["fetched_at"][:10]) - pd.Timestamp(published)).days)
        if gap <= near_crawl_days:
            published, date_source = "", "htmldate_near_crawl"
    status = meta.get("http_status")
    n_words = int(extracted.get("n_words") or 0)
    soft_404 = bool(SOFT_404_RE.search(extracted.get("title") or ""))
    return {
        "url": meta["url"], "final_url": meta.get("final_url", ""), "http_status": status,
        "fetch_error": meta.get("fetch_error", ""), "content_kind": meta.get("content_kind", ""),
        "is_readable": bool(status == 200 and n_words >= min_words and not soft_404), "soft_404": soft_404,
        "title": extracted.get("title", ""), "n_words": n_words, "n_pages": extracted.get("n_pages", ""),
        "published_date": published, "date_source": date_source,
        "schema_types": ";".join(sorted(types)),
        "has_article_schema": bool(types & ARTICLE_TYPES), "has_faq_schema": bool(types & FAQ_TYPES),
        "has_org_schema": bool(types & ORG_TYPES), "crawled_at": meta.get("fetched_at", ""),
    }


def brand_counts(text: str, brands) -> list[dict]:
    out: dict[str, dict] = {}
    n = max(len(text), 1)
    for m in find_matches(text, brands, unambiguous_only=True):
        brand, _ = credit(m.brand)
        row = out.setdefault(brand, {"brand": brand, "count": 0, "first_pos_ratio": round(m.start / n, 4)})
        row["count"] += 1
    return list(out.values())


def load_body(cache: Path, key: str, meta: dict) -> tuple[bytes | None, str]:
    rendered = cache / f"{key}.rendered.html"
    if meta.get("rendered") and rendered.exists():
        return rendered.read_bytes(), "rendered"
    raw = cache / f"{key}.bin"
    return (raw.read_bytes(), "raw") if raw.exists() else (None, "")


def main(cache: Path = ROOT / ".cache/crawl") -> None:
    cfg = load_config()
    brands = load_brands(ROOT / "config/brands.yaml")
    cits = read_csv("data/interim/citations.csv")
    pages, counts = [], []
    for url in sorted(cits["url"].unique()):
        key = cache_key(url)
        meta = json.loads((cache / f"{key}.json").read_text(encoding="utf-8"))
        data, source = load_body(cache, key, meta)
        extracted: dict = {}
        if data is not None:
            encoding = "utf-8" if source == "rendered" else (meta.get("encoding") or "utf-8")
            try:
                if meta.get("content_kind") == "pdf":
                    extracted = extract_pdf(data, cfg["pdf_max_pages"])
                elif meta.get("content_kind") == "html":
                    extracted = extract_html(data.decode(encoding, errors="replace"), url)
            except Exception as e:
                meta["fetch_error"] = f"extract_error: {type(e).__name__}"
        row = page_row(meta, extracted, cfg["readable_min_words"])
        row["body_source"] = source
        pages.append(row)
        if row["is_readable"]:
            counts += [{"url": url, **c} for c in brand_counts(extracted["text"], brands)]
    write_csv(pd.DataFrame(pages), "data/interim/pages.csv")
    write_csv(pd.DataFrame(counts, columns=["url", "brand", "count", "first_pos_ratio"]), "data/interim/page_brand_counts.csv")


if __name__ == "__main__":
    main()
