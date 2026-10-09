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
