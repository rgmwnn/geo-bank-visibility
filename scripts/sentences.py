import re

import pandas as pd

from scripts.io import read_csv, write_csv

ITEM = "• "  # marks a list item or table row that is one sentence on its own
PLUS_RE = re.compile(r"^\s*\+\d+\s*$")
HR_RE = re.compile(r"^\s*([-*_]\s*){3,}$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
LIST_RE = re.compile(r"^\s*(?:[*+\-\u2022]|\d+[.)])\s+")
ANY_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)", re.DOTALL)
DOMAIN_LINE_RE = re.compile(r"^\s*[\w-]+(\.[\w-]+)*\.(com|id|org|net|co|io|app)\s*$", re.IGNORECASE)
FAVICON = "\x00favicon"
ABBREV = {"p.a", "tbk", "dll", "no", "dsb", "dst", "pt", "jl", "dr", "vs", "e.g", "i.e", "rp", "sdr", "bpk", "ibu", "st"}
SPLIT_RE = re.compile(r"[.?!][\"'”’)\]]*\s+(?=[A-Z0-9\"“(])")


def _inline(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*|__|`", "", text)
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!&|~<>])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip().strip("|").strip()


def _join_soft_wraps(body: str) -> str:
    """Lines inside one block (no blank line between) are one line, unless a line starts a list item, table row,
    heading or chip marker. ChatGPT's copied answers break list items across lines this way."""
    out: list[str] = []
    joinable = False
    for line in body.split("\n"):
        st = line.strip()
        if not st:
            out.append("")
            joinable = False
            continue
        marker = st == FAVICON or PLUS_RE.match(line) or HR_RE.match(line) or st == "Add to Favorites"
        starts_new = marker or LIST_RE.match(line) or st.startswith(("|", "#"))
        if joinable and not starts_new:
            out[-1] = out[-1].rstrip() + " " + st
        else:
            out.append(line)
        joinable = not (marker or st.startswith("|"))
    return "\n".join(out)


def clean_body(body: str) -> str:
    out = []
    after_favicon = False
    body = ANY_IMAGE_RE.sub(lambda m: f"\n{FAVICON}\n" if "s2/favicons" in m.group(0) else "\n", body)
    body = re.sub(r"(?m)^\s*(<br\s*/?>\s*)+", "", body, flags=re.IGNORECASE)
    body = _join_soft_wraps(body)
    lines = body.split("\n")
    nonblank = [i for i, ln in enumerate(lines) if ln.strip()]
    next_of = {i: lines[j] for i, j in zip(nonblank, nonblank[1:])}
    for idx, line in enumerate(lines):
        if not line.strip() or not line.strip().strip("|").strip():
            continue
        if line.strip() == FAVICON:
            after_favicon = True
            continue
        if DOMAIN_LINE_RE.match(line):
            continue
        if PLUS_RE.match(line) or line.strip() == "Add to Favorites" or HR_RE.match(line) or TABLE_SEP_RE.match(line):
            after_favicon = False
            continue
        if after_favicon and PLUS_RE.match(next_of.get(idx, "")):
            after_favicon = False
            continue
        if after_favicon and len(line.split()) <= 4 and not LIST_RE.match(line):
            after_favicon = False
            continue
        after_favicon = False
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [_inline(c) for c in stripped.strip("|").split("|")]
            text = " ".join(c for c in cells if c)
            if text:
                out.append(ITEM + text)
            continue
        if LIST_RE.match(line):
            text = _inline(LIST_RE.sub("", line, count=1))
            if text:
                out.append(ITEM + text)
            continue
        text = _inline(re.sub(r"^\s*#{1,6}\s*", "", line))
        if text and not re.fullmatch(r"\d+[.)]?", text) and re.search(r"\w", text):
            out.append(text)
    return "\n".join(out)


def _split_paragraph(par: str) -> list[str]:
    parts, start = [], 0
    for m in SPLIT_RE.finditer(par):
        before = par[start:m.start()].split()
        last = before[-1].lower().rstrip(".") if before else ""
        if last in ABBREV:
            continue
        parts.append(par[start:m.start() + 1 + len(m.group(0).rstrip()) - 1].strip())
        start = m.end()
    parts.append(par[start:].strip())
    return [p for p in parts if p]


def split_sentences(clean: str) -> list[str]:
    sents = []
    for line in clean.split("\n"):
        if not line.strip():
            continue
        if line.startswith(ITEM):
            sents.append(line[len(ITEM):].strip())
        else:
            sents.extend(_split_paragraph(line))
    return sents


def build_sentences(answers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, a in answers.iterrows():
        for i, s in enumerate(split_sentences(clean_body(a["answer_body"]))):
            rows.append({"answer_id": a["answer_id"], "sent_idx": i, "text": s, "n_words": len(s.split())})
    return pd.DataFrame(rows)


def main() -> None:
    write_csv(build_sentences(read_csv("data/interim/answers.csv")), "data/interim/sentences.csv")


if __name__ == "__main__":
    main()
