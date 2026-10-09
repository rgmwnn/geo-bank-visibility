from scripts.io import read_csv

TYPES = {"regulator", "bank_official", "news_media", "fintech_platform", "blog_aggregator", "forum_ugc", "app_store", "other"}


def test_every_domain_labelled():
    d = read_csv("config/domains.csv")
    c = read_csv("data/interim/citations.csv")
    assert set(c.domain) <= set(d.domain) and d.domain_type.isin(TYPES).all()
    assert d.authority_tier.isin(["High", "Medium", "Low"]).all()
    assert (d[d.domain_type == "other"].note.str.len() > 0).all()


def test_every_answer_brand_has_sentiment():
    m = read_csv("data/interim/mentions.csv")
    s = read_csv("data/labels/sentiment.csv")
    assert set(map(tuple, m[["answer_id", "brand"]].drop_duplicates().values)) == set(map(tuple, s[["answer_id", "brand"]].values))
    assert s.label.isin(["positive", "neutral", "negative", "mixed"]).all()
    assert (s.score == s.label.map({"positive": 1, "neutral": 0, "negative": -1, "mixed": 0})).all()
