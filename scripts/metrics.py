import math

import pandas as pd

from scripts.io import ROOT, load_config, read_csv, write_csv

ENGINES = ["ChatGPT", "Gemini"]


def pawc_weight(sent_idx: int, n_sents: int) -> float:
    return math.exp(-sent_idx / n_sents)


def _sentence_weights(sentences: pd.DataFrame) -> pd.DataFrame:
    s = sentences.copy()
    s["n_sents"] = s.groupby("answer_id")["sent_idx"].transform("count")
    s["total_words"] = s.groupby("answer_id")["n_words"].transform("sum")
    s["w"] = [n * pawc_weight(i, k) / t for n, i, k, t in zip(s.n_words, s.sent_idx, s.n_sents, s.total_words)]
    return s[["answer_id", "sent_idx", "n_sents", "w"]]


def brand_pawc(sentences: pd.DataFrame, mentions: pd.DataFrame) -> pd.DataFrame:
    w = _sentence_weights(sentences)
    m = mentions[["answer_id", "sent_idx", "brand"]].drop_duplicates().merge(w, on=["answer_id", "sent_idx"])
    return m.groupby(["answer_id", "brand"], as_index=False)["w"].sum().rename(columns={"w": "pawc"})


def _with_all(answers: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([answers, answers.assign(engine="All")], ignore_index=True)


def _brand_table(inp: dict, cut: str | None) -> pd.DataFrame:
    answers, mentions, sentiment = inp["answers"], inp["mentions"], inp["sentiment"]
    brands = sorted(mentions["brand"].unique())
    pawc = brand_pawc(inp["sentences"], mentions)
    n_sents = inp["sentences"].groupby("answer_id").size()
    first = mentions.groupby(["answer_id", "brand"])["sent_idx"].min().reset_index()
    first["first_mention_pos"] = first["sent_idx"] / first["answer_id"].map(n_sents)
    a = _with_all(answers)
    keys = ["engine"] + ([cut] if cut else [])
    rows = []
    for key, grp in a.groupby(keys):
        key = key if isinstance(key, tuple) else (key,)
        ids = set(grp.answer_id)
        m = mentions[mentions.answer_id.isin(ids)]
        total = len(m)
        for b in brands:
            mb = m[m.brand == b]
            pw = pawc[(pawc.brand == b) & pawc.answer_id.isin(ids)]["pawc"].sum() / len(ids)
            fm = first[(first.brand == b) & first.answer_id.isin(ids)]["first_mention_pos"]
            se = sentiment[(sentiment.brand == b) & sentiment.answer_id.isin(ids)]
            rows.append({**dict(zip(keys, key)), "brand": b, "n": len(ids),
                         "n_answers_mentioning": mb.answer_id.nunique(),
                         "mention_rate": mb.answer_id.nunique() / len(ids),
                         "ai_mentions": len(mb), "ai_sov": len(mb) / total if total else 0.0,
                         "pawc": pw, "first_mention_pos": fm.mean() if len(fm) else float("nan"),
                         "sentiment_mean": se.score.mean() if len(se) else float("nan"),
                         "n_pos": int((se.label == "positive").sum()), "n_neu": int((se.label == "neutral").sum()),
                         "n_neg": int((se.label == "negative").sum()), "n_mixed": int((se.label == "mixed").sum())})
    return pd.DataFrame(rows)


def _no_brand_rate(inp: dict) -> pd.DataFrame:
    a = _with_all(inp["answers"])
    with_brand = set(inp["mentions"].answer_id)
    a["no_brand"] = ~a.answer_id.isin(with_brand)
    rows = []
    for intent_val in [None, *sorted(a.intent.unique())]:
        sub = a if intent_val is None else a[a.intent == intent_val]
        for eng, g in sub.groupby("engine"):
            rows.append({"engine": eng, "intent": intent_val or "All", "n": len(g), "no_brand_rate": g.no_brand.mean()})
    return pd.DataFrame(rows)


def _readable(inp: dict) -> set:
    p = inp["pages"]
    return set(p[p.is_readable.astype(str).str.lower() == "true"].url)


def _attributed(inp: dict, cfg: dict) -> pd.DataFrame:
    s = inp["attribution_scores"]
    s = s[(s.best_score >= cfg["attribution_threshold"]) & s.best_url.isin(_readable(inp))]
    return s.merge(_sentence_weights(inp["sentences"]), on=["answer_id", "sent_idx"])


def _citation_tables(inp: dict, cfg: dict) -> dict:
    c = inp["citations"].merge(inp["answers"][["answer_id", "prompt_no", "pillar"]], on="answer_id")
    c = c.merge(inp["domains"][["domain", "domain_type", "authority_tier"]], on="domain", how="left")
    out = {}
    att = _attributed(inp, cfg).merge(inp["answers"][["answer_id", "engine"]], on="answer_id")
    att["domain"] = att.best_url.str.split("/").str[2].str.removeprefix("www.")
    spd = att.groupby(["domain", "engine"]).agg(source_pawc=("w", "sum"), n_answers=("answer_id", "nunique")).reset_index()
    out["source_pawc_domain"] = spd

    d = c.groupby(["domain", "domain_type", "authority_tier"]).agg(
        citations=("url", "size"), unique_pages=("url", "nunique"), prompts=("prompt_no", "nunique"),
        answers=("answer_id", "nunique"), avg_rank=("rank", "mean")).reset_index()
    for eng, col in [("ChatGPT", "gpt"), ("Gemini", "gem")]:
        e = c[c.engine == eng].groupby("domain").agg(n=("url", "size"), r=("rank", "mean"))
        d[col] = d.domain.map(e["n"]).fillna(0).astype(int)
        d[f"avg_rank_{col}"] = d.domain.map(e["r"])
        d[f"source_pawc_{col}"] = d.domain.map(spd[spd.engine == eng].set_index("domain").source_pawc).fillna(0.0)
    d["n"] = len(c)
    out["domains"] = d.sort_values(["citations", "domain"], ascending=[False, True]).reset_index(drop=True)

    p = c.groupby(["url", "domain"]).agg(citations=("answer_id", "size"), gpt=("engine", lambda s: (s == "ChatGPT").sum()),
                                        gem=("engine", lambda s: (s == "Gemini").sum()),
                                        engines=("engine", lambda s: "+".join(sorted(set(s))))).reset_index()
    p = p.sort_values(["citations", "url"], ascending=[False, True]).reset_index(drop=True)
    p["rank"] = range(1, len(p) + 1)
    p["n"] = len(c)
    out["pages_top"] = p
    out["cross_engine_pages"] = p[p.engines == "ChatGPT+Gemini"].reset_index(drop=True)

    def mix(col, extra=()):
        rows = []
        for keys, g in [(("All",), c)] + [((e,), c[c.engine == e]) for e in ENGINES]:
            subsets = [("All", g)] + ([(v, g[g.pillar == v]) for v in sorted(g.pillar.unique())] if extra else [])
            for pv, sg in subsets:
                for val, n in sg[col].value_counts().items():
                    rows.append({"engine": keys[0], **({"pillar": pv} if extra else {}), col: val,
                                 "citations": int(n), "share": n / len(sg), "n": len(sg)})
        return pd.DataFrame(rows)

    out["domain_type_mix"] = mix("domain_type", extra=("pillar",))
    out["authority_mix"] = mix("authority_tier")
    rows = []
    for eng, g in [("All", c)] + [(e, c[c.engine == e]) for e in ENGINES]:
        top5 = g.domain.value_counts().head(5).sum()
        rows.append({"engine": eng, "top5_share": top5 / len(g), "n": len(g)})
    out["concentration"] = pd.DataFrame(rows)

    sents = inp["sentences"].merge(inp["answers"][["answer_id", "engine"]], on="answer_id")
    rows = []
    for eng, g in [("All", sents)] + [(e, sents[sents.engine == e]) for e in ENGINES]:
        n_att = att[att.answer_id.isin(set(g.answer_id))].shape[0]
        rows.append({"engine": eng, "n_sentences": len(g), "attributed": n_att, "coverage": n_att / len(g)})
    out["attribution_coverage"] = pd.DataFrame(rows)
    return out


def _page_tables(inp: dict, cfg: dict) -> dict:
    pages = inp["pages"].copy()
    pages["is_readable"] = pages.is_readable.astype(str).str.lower() == "true"
    pages["domain"] = pages.url.str.split("/").str[2].str.removeprefix("www.")
    pages = pages.merge(inp["domains"][["domain", "domain_type"]], on="domain", how="left")
    readable = set(pages[pages.is_readable].url)
    out = {}

    pbc = inp["page_brand_counts"]
    pbc = pbc[pbc.url.isin(readable)]
    src = pbc.groupby("brand").agg(source_count=("count", "sum"), n_pages=("url", "nunique"))
    # each page carries equal weight: its brand shares sum to 1, so one long PDF cannot dominate
    pbc = pbc.assign(page_share=pbc["count"] / pbc.groupby("url")["count"].transform("sum"))
    n_brand_pages = pbc.url.nunique()
    weighted = pbc.groupby("brand").page_share.sum() / n_brand_pages if n_brand_pages else pbc.groupby("brand").page_share.sum()
    ai = inp["mentions"].groupby("brand").size()
    brands = sorted(set(src.index) | set(ai.index))
    total_src, total_ai = src.source_count.sum(), ai.sum()
    rows = []
    for b in brands:
        sc = int(src.source_count.get(b, 0))
        am = int(ai.get(b, 0))
        s_sov = float(weighted.get(b, 0.0))
        a_sov = am / total_ai if total_ai else 0.0
        rows.append({"brand": b, "source_sov": s_sov, "source_sov_raw": sc / total_src if total_src else 0.0,
                     "source_count": sc, "n_pages": int(src.n_pages.get(b, 0)), "ai_mentions": am, "ai_sov": a_sov,
                     "sov_gap": a_sov - s_sov, "n_pages_with_brands": n_brand_pages, "n_readable_pages": len(readable)})
    out["source_sov"] = pd.DataFrame(rows)

    def reason(r):
        if r.is_readable:
            return "readable"
        if str(getattr(r, "soft_404", "")).lower() == "true":
            return "soft_404"
        err = str(r.fetch_error) if pd.notna(r.fetch_error) else ""
        if err:
            return err.split(":")[0]
        status = r.http_status
        if pd.notna(status) and status != "" and int(float(status)) != 200:
            return f"http_{int(float(status))}"
        return "too_little_text"

    pages["reason"] = pages.apply(reason, axis=1)
    rows = []
    for dt, g in [("All", pages)] + list(pages.groupby("domain_type")):
        for rsn, n in g.reason.value_counts().items():
            rows.append({"cut": "domain_type", "value": dt, "reason": rsn, "pages": int(n), "share": n / len(g), "n": len(g)})
    c = inp["citations"].merge(pages[["url", "reason"]], on="url", how="left")
    for eng, g in [("All", c)] + [(e, c[c.engine == e]) for e in ENGINES]:
        for rsn, n in g.reason.value_counts().items():
            rows.append({"cut": "engine_citations", "value": eng, "reason": rsn, "pages": int(n), "share": n / len(g), "n": len(g)})
    out["readability"] = pd.DataFrame(rows)

    run = pd.Timestamp(cfg["run_date"])
    b1, b2, b3 = cfg["recency_bins"]

    def group(date):
        if not isinstance(date, str) or not date:
            return "unknown"
        days = (run - pd.Timestamp(date)).days
        return f"0-{b1}" if days <= b1 else f"{b1 + 1}-{b2}" if days <= b2 else f"{b2 + 1}-{b3}" if days <= b3 else f">{b3}"

    pages["group"] = pages.published_date.map(group)
    cr = inp["citations"].merge(pages[["url", "group", "is_readable", "domain_type"]], on="url")
    cr = cr[cr.is_readable]
    rows = []
    for eng, g in [("All", cr)] + [(e, cr[cr.engine == e]) for e in ENGINES]:
        for grp, n in g.group.value_counts().items():
            rows.append({"engine": eng, "group": grp, "citations": int(n), "share": n / len(g), "n": len(g)})
    out["recency"] = pd.DataFrame(rows)

    html = pages[pages.is_readable & (pages.content_kind == "html")].copy()
    st = html.schema_types.fillna("").astype(str)
    html["any_jsonld"] = st != ""
    html["article"] = st.str.contains(r"Article|BlogPosting|Report")
    html["faq"] = st.str.contains("FAQPage")
    html["org"] = st.str.contains(r"Organization|BankOrCreditUnion|FinancialService|Corporation")
    rows = []
    for dt, g in [("All", html)] + list(html.groupby("domain_type")):
        rows.append({"domain_type": dt, "n": len(g), "any_jsonld": g.any_jsonld.mean(), "article": g.article.mean(),
                     "faq": g.faq.mean(), "org": g.org.mean()})
    out["schema"] = pd.DataFrame(rows)
    return out


def _vis(inp: dict, cfg: dict, brand_engine: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    auth = cfg["authority_values"]
    c = inp["citations"].merge(inp["domains"][["domain", "authority_tier"]], on="domain", how="left")
    c["auth"] = c.authority_tier.map(auth)
    m = inp["mentions"].merge(inp["answers"][["answer_id", "engine"]], on="answer_id")
    w = cfg["vis_weights"]
    out = {}
    for eng in ["All", *ENGINES]:
        be = brand_engine[(brand_engine.engine == eng) & (brand_engine.n_answers_mentioning > 0)].copy()
        max_p = be.pawc.max()
        rows = []
        for r in be.itertuples():
            ids = set(m[(m.brand == r.brand) & ((m.engine == eng) | (eng == "All"))].answer_id)
            authority = c[c.answer_id.isin(ids)].auth.mean()
            sent_norm = (r.sentiment_mean + 1) / 2
            engines_with = m[m.brand == r.brand].engine.nunique()
            parts = {"pawc": r.pawc / max_p if max_p else 0.0, "authority": authority, "sentiment": sent_norm}
            if eng == "All":
                parts["diversity"] = engines_with / len(ENGINES)
            weights = {k: w[k] for k in parts}
            vis = 100 * sum(parts[k] * weights[k] for k in parts) / sum(weights.values())
            rows.append({"brand": r.brand, "engine": eng, "n_answers": len(ids), "low_n": len(ids) < cfg["low_n_answers"],
                         "pawc": r.pawc, "pawc_norm": parts["pawc"], "authority": authority, "sentiment_norm": sent_norm,
                         "diversity": parts.get("diversity", float("nan")), "vis": vis})
        out[eng] = pd.DataFrame(rows).sort_values("vis", ascending=False).reset_index(drop=True)
    return out["All"], pd.concat([out[e] for e in ENGINES], ignore_index=True)


def compute_all(inputs: dict, cfg: dict) -> dict:
    out = {"brand_engine": _brand_table(inputs, None), "brand_pillar": _brand_table(inputs, "pillar"),
           "brand_intent": _brand_table(inputs, "intent"), "no_brand_rate": _no_brand_rate(inputs)}
    out.update(_citation_tables(inputs, cfg))
    out.update(_page_tables(inputs, cfg))
    out["vis"], out["vis_engine"] = _vis(inputs, cfg, out["brand_engine"])
    return out


def load_inputs() -> dict:
    return {
        "answers": read_csv("data/interim/answers.csv"), "sentences": read_csv("data/interim/sentences.csv"),
        "mentions": read_csv("data/interim/mentions.csv"), "sentiment": read_csv("data/labels/sentiment.csv"),
        "citations": read_csv("data/interim/citations.csv"), "domains": read_csv("config/domains.csv"),
        "pages": read_csv("data/interim/pages.csv"), "page_brand_counts": read_csv("data/interim/page_brand_counts.csv"),
        "attribution_scores": read_csv("data/interim/attribution_scores.csv"),
    }


def main() -> None:
    out = compute_all(load_inputs(), load_config())
    for key, df in out.items():
        write_csv(df, f"data/processed/{key}.csv")
        (ROOT / f"data/processed/{key}.json").write_text(df.to_json(orient="records", force_ascii=False, indent=1),
                                                          encoding="utf-8")


if __name__ == "__main__":
    main()
