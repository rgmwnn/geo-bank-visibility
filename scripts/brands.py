import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from scripts.io import ROOT, read_csv, write_csv


@dataclass
class Brand:
    brand: str
    parent: str | None
    type: str
    aliases: list[str]
    case_sensitive: bool
    ambiguous: bool = False
    ambiguous_aliases: list[str] = field(default_factory=list)


@dataclass
class Match:
    brand: Brand
    alias: str
    start: int
    end: int


def load_brands(path: Path) -> list[Brand]:
    out = []
    for e in yaml.safe_load(path.read_text(encoding="utf-8")):
        amb = list(e.get("ambiguous_aliases") or [])
        out.append(Brand(e["brand"], e.get("parent"), e["type"], list(e["aliases"]),
                         bool(e.get("case_sensitive", False)), bool(amb), amb))
    return out


def _pattern(alias: str, case_sensitive: bool) -> re.Pattern:
    return re.compile(r"(?<![\w’'])" + re.escape(alias) + r"(?![\w])", 0 if case_sensitive else re.IGNORECASE)


def find_matches(text: str, brands: list[Brand], unambiguous_only: bool = False) -> list[Match]:
    cands = []
    for b in brands:
        for alias in b.aliases:
            if unambiguous_only and alias in b.ambiguous_aliases:
                continue
            for m in _pattern(alias, b.case_sensitive).finditer(text):
                cands.append(Match(b, alias, m.start(), m.end()))
    cands.sort(key=lambda m: (-(m.end - m.start), m.start))
    taken: list[Match] = []
    for c in cands:
        if all(c.end <= t.start or c.start >= t.end for t in taken):
            taken.append(c)
    return sorted(taken, key=lambda m: m.start)


def credit(b: Brand) -> tuple[str, str]:
    return (b.parent, b.brand) if b.parent else (b.brand, "")


REVIEW_PATH = "data/labels/ambiguous_hits.csv"
REVIEW_COLS = ["answer_id", "sent_idx", "alias", "char_pos", "sentence", "decision", "note"]


def main() -> None:
    brands = load_brands(ROOT / "config/brands.yaml")
    sents = read_csv("data/interim/sentences.csv")
    review = read_csv(REVIEW_PATH) if (ROOT / REVIEW_PATH).exists() else pd.DataFrame(columns=REVIEW_COLS)
    decided = {(r.answer_id, int(r.sent_idx), r.alias, int(r.char_pos)): r.decision for r in review.itertuples()}
    rows, new = [], []
    for s in sents.itertuples():
        for m in find_matches(s.text, brands):
            if m.alias in m.brand.ambiguous_aliases:
                key = (s.answer_id, int(s.sent_idx), m.alias, m.start)
                if key not in decided:
                    new.append(dict(zip(REVIEW_COLS, [*key, s.text, "", ""])))
                    continue
                if decided[key] != "keep":
                    continue
            brand, sub = credit(m.brand)
            rows.append({"answer_id": s.answer_id, "sent_idx": s.sent_idx, "brand": brand, "sub_brand": sub,
                         "alias_matched": m.alias, "char_pos": m.start})
    if new:
        write_csv(pd.concat([review, pd.DataFrame(new)], ignore_index=True), REVIEW_PATH)
        raise SystemExit(f"review ambiguous hits: {len(new)} new rows in {REVIEW_PATH}")
    write_csv(pd.DataFrame(rows, columns=["answer_id", "sent_idx", "brand", "sub_brand", "alias_matched", "char_pos"]),
              "data/interim/mentions.csv")


if __name__ == "__main__":
    main()
