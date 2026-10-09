from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config/metrics.yaml").read_text(encoding="utf-8"))


def read_csv(rel_path: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / rel_path, keep_default_na=False, na_values=[""])


def write_csv(df: pd.DataFrame, rel_path: str) -> None:
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")
