"""Six-answer fixture. Every expected value in test_metrics.py is worked out by hand from these rows."""
import pandas as pd

CFG = {"run_date": "2026-10-09", "attribution_threshold": 0.30, "authority_values": {"High": 1.0, "Medium": 0.7, "Low": 0.4},
       "low_n_answers": 3, "recency_bins": [30, 180, 365], "vis_weights": {"pawc": 1, "authority": 1, "sentiment": 1, "diversity": 1}}

IDS = ["gpt-01", "gpt-02", "gpt-03", "gem-01", "gem-02", "gem-03"]
answers = pd.DataFrame({"answer_id": IDS, "engine": ["ChatGPT"] * 3 + ["Gemini"] * 3, "prompt_no": [1, 2, 3, 1, 2, 3],
                        "pillar": ["Fees", "Service", "Fees"] * 2, "intent": ["Best", "Compare", "How-to"] * 2})
# every answer: 4 sentences of 10 words
sentences = pd.DataFrame([{"answer_id": a, "sent_idx": i, "text": f"s{i}", "n_words": 10} for a in IDS for i in range(4)])
mentions = pd.DataFrame([
    ("gpt-01", 0, "BCA"), ("gpt-01", 2, "BCA"), ("gpt-01", 1, "Bank Jago"),
    ("gpt-02", 0, "BCA"),
    ("gem-01", 0, "Bank Jago"), ("gem-01", 0, "Bank Jago"), ("gem-01", 3, "BCA"),
    ("gem-02", 1, "Bank Jago"),
    ("gem-03", 0, "BCA"),
], columns=["answer_id", "sent_idx", "brand"])
mentions["sub_brand"] = ""
sentiment = pd.DataFrame([
    ("gpt-01", "BCA", "positive", 1), ("gpt-01", "Bank Jago", "neutral", 0), ("gpt-02", "BCA", "positive", 1),
    ("gem-01", "Bank Jago", "mixed", 0), ("gem-01", "BCA", "negative", -1), ("gem-02", "Bank Jago", "positive", 1),
    ("gem-03", "BCA", "positive", 1),
], columns=["answer_id", "brand", "label", "score"])
_cit = {"gpt-01": ["https://a.id/1", "https://b.id/1"], "gpt-02": ["https://a.id/1", "https://c.id/1"],
        "gpt-03": ["https://a.id/2", "https://b.id/1"], "gem-01": ["https://a.id/1", "https://c.id/1"],
        "gem-02": ["https://b.id/2", "https://c.id/1"], "gem-03": ["https://b.id/1", "https://a.id/1"]}
citations = pd.DataFrame([{"answer_id": a, "engine": "ChatGPT" if a.startswith("gpt") else "Gemini", "rank": r + 1,
                           "url": u, "domain": u.split("/")[2]} for a, us in _cit.items() for r, u in enumerate(us)])
domains = pd.DataFrame([("a.id", "regulator", "High"), ("b.id", "news_media", "Medium"), ("c.id", "blog_aggregator", "Low")],
                       columns=["domain", "domain_type", "authority_tier"])
pages = pd.DataFrame([
    ("https://a.id/1", 200, "", "html", True, "2026-10-01", "Article"),
    ("https://a.id/2", 403, "", "html", False, "", ""),
    ("https://b.id/1", 200, "", "html", True, "2026-05-01", ""),
    ("https://b.id/2", 200, "", "html", True, "", "FAQPage"),
    ("https://c.id/1", 200, "", "pdf", True, "2024-01-01", ""),
], columns=["url", "http_status", "fetch_error", "content_kind", "is_readable", "published_date", "schema_types"])
page_brand_counts = pd.DataFrame([
    ("https://a.id/1", "BCA", 3), ("https://a.id/2", "Bank Jago", 10), ("https://b.id/1", "BCA", 1),
    ("https://b.id/1", "Krom Bank", 4), ("https://b.id/2", "Bank Jago", 2), ("https://c.id/1", "Bank Jago", 1),
], columns=["url", "brand", "count"])
attribution_scores = pd.DataFrame([
    ("gpt-01", 0, "https://a.id/1", 0.8), ("gpt-01", 1, "https://b.id/1", 0.2), ("gpt-01", 2, "https://a.id/1", 0.5),
    ("gem-01", 0, "https://c.id/1", 0.9), ("gem-01", 1, "https://a.id/2", 0.9),
], columns=["answer_id", "sent_idx", "best_url", "best_score"])

MINI = dict(answers=answers, sentences=sentences, mentions=mentions, sentiment=sentiment, citations=citations,
            domains=domains, pages=pages, page_brand_counts=page_brand_counts, attribution_scores=attribution_scores)
