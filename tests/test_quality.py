from scripts.quality import build_report


def test_report_sections():
    r = build_report()
    for h in ["## Counts", "## Citations per answer", "## Crawl outcomes",
              "## Ambiguous brand hits", "## Sentiment spot-check", "## Known limitations"]:
        assert h in r
    assert "—" not in r and "–" not in r


def test_report_lists_every_unreadable_url():
    from scripts.io import read_csv
    p = read_csv("data/interim/pages.csv")
    r = build_report()
    for url in p[p.is_readable.astype(str) != "True"].url:
        assert url in r
