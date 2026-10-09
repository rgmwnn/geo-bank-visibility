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


def page_row(meta: dict, extracted: dict, min_words: int) -> dict:
    types = set(extracted.get("schema_types") or [])
    status = meta.get("http_status")
    n_words = int(extracted.get("n_words") or 0)
    soft_404 = bool(SOFT_404_RE.search(extracted.get("title") or ""))
    return {
        "url": meta["url"], "final_url": meta.get("final_url", ""), "http_status": status,
        "fetch_error": meta.get("fetch_error", ""), "content_kind": meta.get("content_kind", ""),
        "is_readable": bool(status == 200 and n_words >= min_words and not soft_404), "soft_404": soft_404,
        "title": extracted.get("title", ""), "n_words": n_words, "n_pages": extracted.get("n_pages", ""),
        "published_date": extracted.get("published_date", ""), "date_source": extracted.get("date_source", ""),
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


def load_stopwords() -> set[str]:
    return set((ROOT / "config/stopwords.txt").read_text(encoding="utf-8").split())


def tokens(text: str, stop: set[str]) -> list[str]:
    text = re.sub(r"(?<=\d)[.,](?=\d)", "", text.lower())
    return [t for t in re.findall(r"[a-z0-9]+", text) if t not in stop]


def _bigrams(toks: list[str]) -> set[tuple[str, str]]:
    return set(zip(toks, toks[1:]))


def overlap(sentence: str, page_text: str, stop: set[str]) -> float:
    return _overlap(tokens(sentence, stop), *_page_index(page_text, stop))


def _page_index(page_text: str, stop: set[str]) -> tuple[set, set]:
    toks = tokens(page_text, stop)
    return set(toks), _bigrams(toks)


def _overlap(sent_toks: list[str], page_uni: set, page_bi: set) -> float:
    if not sent_toks:
        return 0.0
    if len(sent_toks) < 3:
        uni = set(sent_toks)
        return len(uni & page_uni) / len(uni)
    bi = _bigrams(sent_toks)
    return len(bi & page_bi) / len(bi)


def attribution_scores(sentences: pd.DataFrame, citations: pd.DataFrame, page_texts: dict[str, str]) -> pd.DataFrame:
    stop = load_stopwords()
    index = {u: _page_index(t, stop) for u, t in page_texts.items()}
    by_answer = {a: g.sort_values("rank")[["rank", "url"]].values.tolist() for a, g in citations.groupby("answer_id")}
    rows = []
    for s in sentences.itertuples():
        toks = tokens(s.text, stop)
        scored = [(_overlap(toks, *index[u]), rank, u) for rank, u in by_answer.get(s.answer_id, []) if u in index]
        scored.sort(key=lambda x: (-x[0], x[1]))
        best = scored[0] if scored else (0.0, None, None)
        second = scored[1] if len(scored) > 1 else (0.0, None, None)
        rows.append({"answer_id": s.answer_id, "sent_idx": s.sent_idx, "best_url": best[2],
                     "best_score": round(best[0], 4), "second_url": second[2], "second_score": round(second[0], 4)})
    return pd.DataFrame(rows, columns=["answer_id", "sent_idx", "best_url", "best_score", "second_url", "second_score"])


def main(cache: Path = ROOT / ".cache/crawl") -> None:
    cfg = load_config()
    brands = load_brands(ROOT / "config/brands.yaml")
    cits = read_csv("data/interim/citations.csv")
    pages, counts, texts = [], [], {}
    for url in sorted(cits["url"].unique()):
        key = cache_key(url)
        meta = json.loads((cache / f"{key}.json").read_text(encoding="utf-8"))
        body = cache / f"{key}.bin"
        extracted: dict = {}
        if body.exists():
            data = body.read_bytes()
            try:
                if meta.get("content_kind") == "pdf":
                    extracted = extract_pdf(data, cfg["pdf_max_pages"])
                elif meta.get("content_kind") == "html":
                    extracted = extract_html(data.decode(meta.get("encoding") or "utf-8", errors="replace"), url)
            except Exception as e:
                meta["fetch_error"] = f"extract_error: {type(e).__name__}"
        row = page_row(meta, extracted, cfg["readable_min_words"])
        pages.append(row)
        if row["is_readable"]:
            texts[url] = extracted["text"]
            counts += [{"url": url, **c} for c in brand_counts(extracted["text"], brands)]
    write_csv(pd.DataFrame(pages), "data/interim/pages.csv")
    write_csv(pd.DataFrame(counts, columns=["url", "brand", "count", "first_pos_ratio"]), "data/interim/page_brand_counts.csv")
    write_csv(attribution_scores(read_csv("data/interim/sentences.csv"), cits, texts), "data/interim/attribution_scores.csv")


if __name__ == "__main__":
    main()
