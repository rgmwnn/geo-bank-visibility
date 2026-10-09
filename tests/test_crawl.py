import requests

from scripts.crawl import by_host, content_kind, robots_decision


def test_content_kind():
    assert content_kind("application/pdf", "https://x/a") == "pdf"
    assert content_kind("text/html; charset=utf-8", "https://x/a") == "html"
    assert content_kind("", "https://x/a.PDF") == "pdf"
    assert content_kind("image/png", "https://x/a.png") == "other"


def test_by_host_groups_and_keeps_order():
    g = by_host(["https://a.id/1", "https://b.id/1", "https://a.id/2"])
    assert g == {"a.id": ["https://a.id/1", "https://a.id/2"], "b.id": ["https://b.id/1"]}


class _Resp:
    def __init__(self, status, text=""):
        self.status_code, self.text = status, text


def _getter(resp=None, exc=None):
    def get(url, timeout):
        assert timeout > 0
        if exc:
            raise exc
        return resp
    return get


def test_robots_rules_rfc9309():
    rules = "User-agent: *\nDisallow: /private\n"
    assert robots_decision(_getter(_Resp(200, rules)), "https://a.id/private/x", {}) == (False, "robots_disallowed")
    assert robots_decision(_getter(_Resp(200, rules)), "https://a.id/ok", {}) == (True, "")
    assert robots_decision(_getter(_Resp(404)), "https://a.id/x", {}) == (True, "")
    assert robots_decision(_getter(_Resp(403)), "https://a.id/x", {}) == (True, "")
    assert robots_decision(_getter(_Resp(503)), "https://a.id/x", {}) == (False, "robots_unreachable")
    assert robots_decision(_getter(exc=requests.Timeout()), "https://a.id/x", {}) == (False, "robots_unreachable")


def test_robots_cached_per_host():
    calls = []
    def get(url, timeout):
        calls.append(url)
        return _Resp(404)
    cache = {}
    robots_decision(get, "https://a.id/1", cache); robots_decision(get, "https://a.id/2", cache)
    assert calls == ["https://a.id/robots.txt"]


def test_needs_render_only_for_short_html_200():
    from scripts.crawl import needs_render
    assert needs_render({"http_status": 200, "content_kind": "html"}, 10, 50) is True
    assert needs_render({"http_status": 200, "content_kind": "html"}, 80, 50) is False
    assert needs_render({"http_status": 403, "content_kind": "html"}, 0, 50) is False
    assert needs_render({"http_status": 200, "content_kind": "pdf"}, 0, 50) is False


def test_retry_wait_reads_retry_after():
    from scripts.crawl import retry_wait
    assert retry_wait({"Retry-After": "7"}) == 7
    assert retry_wait({}) == 5
    assert retry_wait({"Retry-After": "999"}) == 30
    assert retry_wait({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}) == 5
