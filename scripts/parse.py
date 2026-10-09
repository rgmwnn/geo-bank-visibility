import re
from pathlib import Path

import pandas as pd

from scripts.io import load_config

HEADING_RE = re.compile(
    r"^[ \t]*#{0,4}[ \t]*"
    r"(links?[ \t]+cited|sumber[ \t]*&[ \t]*referensi[ \t]+link|\d+[ \t]+(referensi[ \t]+dan[ \t]+)?tautan[ \t]+sumber)"
    r"[ \t]*\r?$",
    re.IGNORECASE | re.MULTILINE,
)

ENGINES = {"ChatGPT": "gpt", "Gemini": "gem"}


def split_citation_section(text: str) -> tuple[str, str]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        raise ValueError("no citation heading")
    last = matches[-1]
    return text[: last.start()], text[last.end():]


def load_answers(xlsx: Path, rerun: Path) -> pd.DataFrame:
    sheet = pd.read_excel(xlsx)
    rerun_text = rerun.read_text(encoding="utf-8")
    run_date = load_config()["run_date"]
    rows = []
    for engine, prefix in ENGINES.items():
        for _, r in sheet.iterrows():
            no = int(r["#"])
            text = rerun_text if (prefix == "gpt" and no == 8) else str(r[engine])
            rows.append({
                "answer_id": f"{prefix}-{no:02d}",
                "engine": engine,
                "prompt_no": no,
                "pillar": r["Pillar"],
                "intent": r["Intent"],
                "prompt": r["Prompt"],
                "answer_raw": text.replace("\r\n", "\n").replace("\r", "\n"),
                "run_date": run_date,
            })
    return pd.DataFrame(rows)


URL_RE = re.compile(r"https?://[^\s\)\]\>\"'`<]+")


def _unwrap(url: str) -> str:
    from urllib.parse import parse_qs, urlparse

    url = url.rstrip(".,;:*\\")
    p = urlparse(url)
    if p.netloc.lower().removeprefix("www.").startswith("google.") and p.path == "/search":
        q = parse_qs(p.query).get("q", [""])[0]
        if q.startswith("http"):
            return _unwrap(q)
    return url


def normalize_url(url: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlparse

    p = urlparse(_unwrap(url))
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/")
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_")])
    return f"https://{host}{path}" + (f"?{query}" if query else "")


def domain_of(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower().removeprefix("www.")


def extract_citations(section: str) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    for line in section.split("\n"):
        found = URL_RE.findall(line)
        if not found:
            continue
        raw = found[0]
        url = normalize_url(raw)
        if url not in seen:
            seen[url] = raw
    return [(raw, url) for url, raw in seen.items()]


def build_citations(answers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, a in answers.iterrows():
        _, section = split_citation_section(a["answer_raw"])
        for rank, (raw, url) in enumerate(extract_citations(section), start=1):
            rows.append({"answer_id": a["answer_id"], "engine": a["engine"], "rank": rank,
                         "url_raw": raw, "url": url, "domain": domain_of(url)})
    return pd.DataFrame(rows)


def main() -> None:
    from scripts.io import ROOT, write_csv

    answers = load_answers(ROOT / "data/raw/geo-bank-research.xlsx", ROOT / "data/raw/chatgpt-prompt08-rerun.md")
    answers["answer_body"] = answers["answer_raw"].map(lambda t: split_citation_section(t)[0].strip())
    cits = build_citations(answers)
    exp = load_config()["expected_counts"]
    actual = {"answers": len(answers), "citations": len(cits),
              "unique_urls": cits["url"].nunique(), "domains": cits["domain"].nunique()}
    if actual != exp:
        raise AssertionError(f"expected {exp}, got {actual}")
    write_csv(answers, "data/interim/answers.csv")
    write_csv(cits, "data/interim/citations.csv")


if __name__ == "__main__":
    main()
