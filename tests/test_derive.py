from pathlib import Path

import pandas as pd

from scripts.derive import extract_html, extract_pdf, page_row

FIX = Path(__file__).parent / "fixtures"


def test_html_fields():
    d = extract_html((FIX / "article.html").read_text(), "https://news.example.id/a")
    assert d["published_date"] == "2026-08-07" and d["date_source"] == "jsonld"
    assert "NewsArticle" in d["schema_types"] and d["n_words"] >= 50


def test_consent_wall_not_readable():
    d = extract_html((FIX / "consent.html").read_text(), "https://bank.example.id")
    row = page_row({"url": "u", "final_url": "u", "http_status": 200, "fetch_error": "", "content_kind": "html"}, d, 50)
    assert row["is_readable"] is False


def test_pdf_text():
    d = extract_pdf((FIX / "report.pdf").read_bytes(), 300)
    assert d["n_pages"] == 2 and d["n_words"] > 0


def test_brand_counts_unambiguous_only_and_rollup():
    from scripts.brands import Brand
    from scripts.derive import brand_counts
    B = [Brand("Bank Jago", None, "digital", ["Bank Jago", "Jago"], True, True, ["Jago"]),
         Brand("BCA", None, "conventional", ["BCA"], True),
         Brand("blu", "BCA", "digital", ["blu by BCA Digital", "blu"], True, True, ["blu"])]
    rows = {r["brand"]: r for r in brand_counts("Bank Jago dan Jago. blu by BCA Digital. BCA hebat.", B)}
    assert rows["Bank Jago"]["count"] == 1 and rows["BCA"]["count"] == 2
    assert rows["Bank Jago"]["first_pos_ratio"] == 0.0


def test_soft_404_title_not_readable():
    meta = {"url": "u", "final_url": "u", "http_status": 200, "fetch_error": "", "content_kind": "html"}
    for title in ["404", "404 Error Page", "Halaman Tidak Ditemukan", "Page Not Found | Bank"]:
        row = page_row(meta, {"title": title, "text": "kata " * 80, "n_words": 80}, 50)
        assert row["is_readable"] is False and row["soft_404"] is True
    ok = page_row(meta, {"title": "BNI Taplus | BNI", "text": "kata " * 80, "n_words": 80}, 50)
    assert ok["is_readable"] is True and ok["soft_404"] is False


def test_load_body_prefers_rendered_html(tmp_path):
    from scripts.derive import load_body
    (tmp_path / "k.bin").write_bytes(b"<html>raw</html>")
    assert load_body(tmp_path, "k", {"rendered": False}) == (b"<html>raw</html>", "raw")
    (tmp_path / "k.rendered.html").write_bytes(b"<html>rendered</html>")
    assert load_body(tmp_path, "k", {"rendered": True}) == (b"<html>rendered</html>", "rendered")
    assert load_body(tmp_path, "missing", {}) == (None, "")


def test_htmldate_near_crawl_day_is_treated_as_unknown():
    meta = {"url": "u", "final_url": "u", "http_status": 200, "fetch_error": "", "content_kind": "html",
            "fetched_at": "2026-10-09T07:10:00+00:00"}
    near = page_row(meta, {"title": "t", "n_words": 80, "published_date": "2026-10-08", "date_source": "htmldate"}, 50)
    assert (near["published_date"], near["date_source"]) == ("", "htmldate_near_crawl")
    far = page_row(meta, {"title": "t", "n_words": 80, "published_date": "2026-09-01", "date_source": "htmldate"}, 50)
    assert far["published_date"] == "2026-09-01"
    js = page_row(meta, {"title": "t", "n_words": 80, "published_date": "2026-10-09", "date_source": "jsonld"}, 50)
    assert js["published_date"] == "2026-10-09"
