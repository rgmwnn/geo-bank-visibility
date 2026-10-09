"""Every number the deck shows, computed from the repo's data files."""
import pandas as pd

from scripts.io import read_csv
from scripts.parse import URL_RE, normalize_url, split_citation_section

ENGINES = ["ChatGPT", "Gemini"]
COLD_OPEN_PROMPT = 13
COLD_OPEN_ENGLISH = ("I'm a freelancer with irregular income. I need an account with no minimum balance "
                     "that lets me split money into pockets. Which bank fits?")


def _truthy(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower() == "true"


def _wrapped_links(answers: pd.DataFrame) -> set:
    wrapped = set()
    for r in answers.itertuples():
        _, section = split_citation_section(r.answer_raw)
        for line in section.split("\n"):
            urls = URL_RE.findall(line)
            if urls and any("google.com/search" in u for u in urls):
                wrapped.add((r.answer_id, normalize_url(urls[0])))
    return wrapped


def load() -> dict:
    answers = read_csv("data/interim/answers.csv")
    sentences = read_csv("data/interim/sentences.csv")
    mentions = read_csv("data/interim/mentions.csv")
    citations = read_csv("data/interim/citations.csv")
    pages = read_csv("data/interim/pages.csv")
    sentiment = read_csv("data/labels/sentiment.csv")
    brand_engine = read_csv("data/processed/brand_engine.csv")
    brand_pillar = read_csv("data/processed/brand_pillar.csv")
    vis = read_csv("data/processed/vis.csv")
    no_brand = read_csv("data/processed/no_brand_rate.csv")
    type_mix = read_csv("data/processed/domain_type_mix.csv")
    domains = read_csv("data/processed/domains.csv")
    pages_top = read_csv("data/processed/pages_top.csv")
    concentration = read_csv("data/processed/concentration.csv")
    source_sov = read_csv("data/processed/source_sov.csv")
    schema = read_csv("data/processed/schema.csv")
    recency = read_csv("data/processed/recency.csv")

    f: dict = {}
    readable = pages[_truthy(pages.is_readable)]
    f.update(answers=len(answers), sentences=len(sentences), mentions=len(mentions), citations=len(citations),
             pages=len(pages), readable_pages=len(readable))

    m = mentions.merge(answers[["answer_id", "engine"]], on="answer_id")
    f["banks_gpt"] = m[m.engine == "ChatGPT"].brand.nunique()
    f["banks_gem"] = m[m.engine == "Gemini"].brand.nunique()

    named = brand_engine[brand_engine.n_answers_mentioning > 0]
    f["mention_rate"] = {b: dict(zip(g.engine, g.mention_rate)) for b, g in named.groupby("brand")}
    f["answers_mentioning"] = {b: dict(zip(g.engine, g.n_answers_mentioning)) for b, g in named.groupby("brand")}
    f["brand_engine"] = brand_engine
    f["vis"] = vis[["brand", "n_answers", "vis", "low_n"]].assign(low_n=_truthy(vis.low_n))

    bp = brand_pillar[(brand_pillar.engine == "All") & (brand_pillar.n_answers_mentioning > 0)]
    f["pillar_rates"] = bp[["pillar", "brand", "n", "mention_rate"]].reset_index(drop=True)
    f["pillar_leaders"] = (bp.sort_values(["pillar", "mention_rate", "brand"], ascending=[True, False, True])
                           .groupby("pillar").head(1)[["pillar", "brand", "mention_rate"]].reset_index(drop=True))

    counts = sentiment.label.value_counts()
    f["sentiment_counts"] = {k: int(counts.get(k, 0)) for k in ["positive", "neutral", "mixed", "negative"]}
    f["sentiment_pairs"] = len(sentiment)

    nb = no_brand[(no_brand.engine == "All") & (no_brand.intent != "All")]
    f["intent_named_share"] = {r.intent: (1 - r.no_brand_rate, int(r.n)) for r in nb.itertuples()}

    tm = type_mix[(type_mix.pillar == "All") & type_mix.engine.isin(ENGINES)]
    f["source_mix"] = {e: dict(zip(g.domain_type, g.share)) for e, g in tm.groupby("engine")}
    f["source_mix_counts"] = {e: dict(zip(g.domain_type, g.citations)) for e, g in tm.groupby("engine")}

    gpt_sites = set(citations[citations.engine == "ChatGPT"].domain)
    gem_sites = set(citations[citations.engine == "Gemini"].domain)
    gpt_pages = set(citations[citations.engine == "ChatGPT"].url)
    gem_pages = set(citations[citations.engine == "Gemini"].url)
    f["overlap"] = {
        "sites_both": len(gpt_sites & gem_sites), "sites_gpt_only": len(gpt_sites - gem_sites),
        "sites_gem_only": len(gem_sites - gpt_sites), "sites_total": len(gpt_sites | gem_sites),
        "pages_both": len(gpt_pages & gem_pages), "pages_total": len(gpt_pages | gem_pages),
        "jaccard_sites": len(gpt_sites & gem_sites) / len(gpt_sites | gem_sites),
        "jaccard_pages": len(gpt_pages & gem_pages) / len(gpt_pages | gem_pages),
    }
    f["top_sites"] = domains[["domain", "domain_type", "citations", "gpt", "gem"]].head(12).reset_index(drop=True)
    f["top_pages"] = pages_top[["url", "domain", "citations", "gpt", "gem"]].head(8).reset_index(drop=True)
    gem_answers = citations[citations.engine == "Gemini"].groupby("domain").answer_id.nunique()
    f["gemini_answers_citing"] = {d: int(gem_answers.get(d, 0)) for d in ["akulaku.com", "zaipad.com", "fazz.com"]}
    f["gemini_citations"] = {d: int((citations[(citations.engine == "Gemini")].domain == d).sum())
                             for d in ["akulaku.com", "zaipad.com", "fazz.com"]}
    f["concentration"] = dict(zip(concentration.engine, concentration.top5_share))

    f["sov_gap"] = (source_sov[source_sov.ai_mentions > 0]
                    .sort_values("ai_sov_weighted", ascending=False)
                    [["brand", "ai_sov_weighted", "source_sov", "sov_gap"]].head(8).reset_index(drop=True))

    dead = set(pages[(pages.http_status.astype(str).str.startswith("404")) | _truthy(pages.soft_404)].url)
    wrapped = _wrapped_links(answers)
    gem = citations[citations.engine == "Gemini"]
    is_wrapped = [(a, u) in wrapped for a, u in zip(gem.answer_id, gem.url)]
    gem = gem.assign(wrapped=is_wrapped, dead=gem.url.isin(dead))
    f["dead_links"] = (int((gem.wrapped & gem.dead).sum()), int(gem.wrapped.sum()),
                       int((~gem.wrapped & gem.dead).sum()), int((~gem.wrapped).sum()))
    f["dead_citations"] = int(citations.url.isin(dead).sum())
    f["dead_pages"] = len(dead)

    f["schema_by_type"] = schema[schema.domain_type != "All"][["domain_type", "n", "any_jsonld"]].reset_index(drop=True)
    citation_share = type_mix[(type_mix.pillar == "All") & (type_mix.engine == "All")]
    f["citation_share_by_type"] = dict(zip(citation_share.domain_type, citation_share.share))
    rec = recency[(recency.cut == "engine") & (recency.value == "All") & (recency.basis == "structured dates only")]
    f["readable_citations"] = int(rec.n.iloc[0])
    f["dated_citations"] = int(rec[rec.group != "unknown"].citations.sum())
    f["recency_structured"] = dict(zip(rec.group, rec.citations))

    ans = answers.set_index("answer_id")
    cold = m[m.answer_id.str.endswith(f"-{COLD_OPEN_PROMPT:02d}")]
    f["cold_open"] = {
        "prompt": ans.loc[f"gpt-{COLD_OPEN_PROMPT:02d}", "prompt"], "english": COLD_OPEN_ENGLISH,
        "banks_gpt": sorted(cold[cold.engine == "ChatGPT"].brand.unique()),
        "banks_gem": sorted(cold[cold.engine == "Gemini"].brand.unique()),
    }
    f["prompt_grid"] = answers[answers.engine == "ChatGPT"][["prompt_no", "pillar", "intent"]].reset_index(drop=True)
    return f
