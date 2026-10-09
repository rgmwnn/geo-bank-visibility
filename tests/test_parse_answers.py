import pytest

from scripts.io import ROOT
from scripts.parse import RERUNS, load_answers, split_citation_section


def test_heading_variants_split():
    for h in ["### Links Cited", "### Sumber & Referensi Link", "## 10 tautan sumber",
              "10 tautan sumber", "10 referensi dan tautan sumber"]:
        body, sec = split_citation_section(f"Isi jawaban.\n\n{h}\n\n1. [https://a.id](https://a.id)")
        assert body.strip() == "Isi jawaban." and "https://a.id" in sec


def test_crlf_same_as_lf():
    t = "Isi.\r\n\r\n## 10 tautan sumber\r\n\r\n1. [https://a.id](https://a.id)\r\n"
    crlf = [x.replace("\r", "") for x in split_citation_section(t)]
    lf = list(split_citation_section(t.replace("\r\n", "\n")))
    assert crlf == lf


def test_missing_heading_raises():
    with pytest.raises(ValueError):
        split_citation_section("no sources here https://a.id")


def test_load_answers_real_file():
    df = load_answers(ROOT / "data/raw/geo-bank-research.xlsx", RERUNS)
    assert len(df) == 40 and df.answer_id.is_unique
    a = df.set_index("answer_id").answer_raw
    assert "Laporan Tahunan" in a["gpt-08"]
    assert "myBCA" in a["gpt-09"] and "tabungan jangka panjang" not in a["gpt-09"].lower()
    assert not df.answer_raw.str.contains("\r").any()
    assert (df.run_date == "2026-10-09").all()
