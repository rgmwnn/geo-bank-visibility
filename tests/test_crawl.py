from scripts.crawl import content_kind, schedule


def test_content_kind():
    assert content_kind("application/pdf", "https://x/a") == "pdf"
    assert content_kind("text/html; charset=utf-8", "https://x/a") == "html"
    assert content_kind("", "https://x/a.PDF") == "pdf"
    assert content_kind("image/png", "https://x/a.png") == "other"


def test_per_domain_delay_scheduler():
    order = schedule(["https://a.id/1", "https://a.id/2", "https://b.id/1"])
    assert order[0][0] != order[1][0]
    assert sorted(u for _, u in order) == ["https://a.id/1", "https://a.id/2", "https://b.id/1"]
