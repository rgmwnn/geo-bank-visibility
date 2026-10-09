"""Slide copy. Every number comes from facts (via N) or from a named outside source (EXTERNAL)."""
import re

from deck.fmt import num, pct

# Numbers quoted from outside sources, each with where it comes from.
EXTERNAL = {
    "14%": "OpenAI usage study via Search Engine Journal: information-seeking share of ChatGPT conversations, before",
    "24%": "same study, a year later",
    "12%": "Ahrefs: share of AI-cited URLs that rank in Google's top 10 for the same query",
    "15,000": "Ahrefs: prompts analysed",
    "0.119": "Writesonic: Jaccard overlap of ChatGPT and Gemini citations",
    "88,969": "Writesonic: prompts compared",
    "27.24%": "Bisnis, May 2023: Akulaku stake in Bank Neo Commerce",
    "2023": "year of the Bisnis report",
    "2024": "Aggarwal et al., KDD 2024",
    "2025": "Tow Center study year",
    "2026": "year of the run and of the SparkToro report",
    "3,000": "SparkToro and Gumshoe: runs",
    "1 in 100": "SparkToro and Gumshoe: chance of the same list twice",
    "2311.09735": "arXiv id of the GEO paper",
}

REPO = "github.com/rgmwnn/geo-bank-visibility"
SLATE_DATE = "09.10.2026"
DISPLAY = {"Bank BTPN": "Bank BTPN (Jenius)"}


def numbers(f: dict) -> dict:
    mr, am = f["mention_rate"], f["answers_mentioning"]
    vis = f["vis"].set_index("brand").vis
    sov = f["sov_gap"].set_index("brand")
    mix = f["source_mix"]
    o = f["overlap"]
    wd, wt, dd, dt = f["dead_links"]
    sc = f["sentiment_counts"]
    sch = f["schema_by_type"].set_index("domain_type").any_jsonld
    how_share, how_n = f["intent_named_share"]["How-to"]
    pc = f["pillar_counts"]
    pc_n = pc.groupby("pillar").n.first()
    pc_top = pc.groupby("pillar").named.max()
    names = {"Fees & rates": "Fees and rates", "Digital experience": "Digital experience",
             "Safety & security": "Safety", "Service": "Service", "Trust": "Trust"}
    leads = ". ".join(f"{names[p]}: {_and(f['pillar_leaders'][p])}, {pc_top[p]} of {pc_n[p]}"
                      for p in ["Fees & rates", "Digital experience", "Safety & security", "Service", "Trust"]) + "."
    unb_prompts = f["prompts"] - f["branded_prompts"]
    return {
        "answers": str(f["answers"]), "prompts": str(f["prompts"]), "engines": "2",
        "pillars": str(f["pillars"]), "intents": str(f["intents"]), "per_answer": str(f["citations_per_answer"]),
        "branded": str(f["branded_prompts"]), "digital": str(len(f["digital_prompts"])),
        "cold_no": "13", "sentences": num(f["sentences"]), "mentions": num(f["mentions"]),
        "citations": num(f["citations"]), "pages": num(f["pages"]), "readable": num(f["readable_pages"]),
        "readable_bank": num(f["readable_pages_with_bank"]), "rendered": str(f["rendered_pages"]),
        "bca_n": str(am["BCA"]["All"]), "jago_n": str(am["Bank Jago"]["All"]), "sea_n": str(am["SeaBank"]["All"]),
        "bri_n": str(am["BRI"]["All"]),
        "vis_bca": num(vis["BCA"], 1), "vis_jago": num(vis["Bank Jago"], 1), "vis_bri": num(vis["BRI"], 1),
        "vis_sea": num(vis["SeaBank"], 1), "low_n_cut": "3",
        "banks_gpt": str(f["banks_gpt"]), "banks_gem": str(f["banks_gem"]),
        "btpn_gem": str(am["Bank BTPN"]["Gemini"]), "super_gem": str(am["Superbank"]["Gemini"]),
        "pillar_leads": leads, "unb_prompts": str(unb_prompts), "unb_answers": str(unb_prompts * 2),
        "cit_gpt": str(f["citations_by_engine"]["ChatGPT"]), "cit_gem": str(f["citations_by_engine"]["Gemini"]),
        "schema_pages": str(int(f["schema_by_type"].n.sum())),
        "pairs": str(f["sentiment_pairs"]), "positive": str(sc["positive"]), "mixed": str(sc["mixed"]),
        "how_named": str(round(how_share * how_n)), "how_n": str(how_n),
        "gpt_first": pct(mix["ChatGPT"]["bank_official"] + mix["ChatGPT"]["regulator"]),
        "gem_third": pct(mix["Gemini"]["fintech_platform"] + mix["Gemini"]["blog_aggregator"] + mix["Gemini"]["news_media"]),
        "sites_both": str(o["sites_both"]), "gpt_sites": str(o["sites_both"] + o["sites_gpt_only"]), "sites_total": str(o["sites_total"]),
        "pages_both": str(o["pages_both"]), "pages_total": str(o["pages_total"]),
        "jac_sites": num(o["jaccard_sites"], 2), "jac_pages": num(o["jaccard_pages"], 2),
        "aku_page": str(f["top_page_gem_answers"]["akulaku.com"]), "zai_page": str(f["top_page_gem_answers"]["zaipad.com"]),
        "fazz_cit": str(f["gemini_citations"]["fazz.com"]), "fazz_ans": str(f["gemini_answers_citing"]["fazz.com"]),
        "gem_answers": str(f["answers"] // 2),
        "comp_lo": str(min(f["gemini_answers_citing"].values())), "comp_hi": str(max(f["gemini_answers_citing"].values())),
        "conc_gpt": pct(f["concentration"]["ChatGPT"]), "conc_gem": pct(f["concentration"]["Gemini"]),
        "jago_ai": pct(sov.loc["Bank Jago", "ai_sov_weighted"], 1), "jago_src": pct(sov.loc["Bank Jago", "source_sov"], 1),
        "mandiri_src": pct(sov.loc["Bank Mandiri", "source_sov"], 1),
        "mandiri_ai": pct(sov.loc["Bank Mandiri", "ai_sov_weighted"], 1),
        "wrapped_dead": str(wd), "wrapped": str(wt), "direct": str(dt),
        "sch_bank": pct(sch["bank_official"]), "sch_news": pct(sch["news_media"]), "sch_blog": pct(sch["blog_aggregator"]),
        "dated": str(f["dated_citations"]), "readable_cit": str(f["readable_citations"]),
        "bca_rate": pct(mr["BCA"]["All"]), "sea_rate": pct(mr["SeaBank"]["All"], 1),
        "sparktoro_prompts": "12", "vis_lo": "0", "vis_hi": "100",
    }


def _and(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _cold_banks(names: list[str]) -> str:
    return "\n".join(DISPLAY.get(b, b) for b in names)


def slides(f: dict) -> list[dict]:
    N = numbers(f)
    c = f["cold_open"]
    S = []

    def add(kind, layout, title="", body=(), chart=None, foot="", notes="", **extra):
        S.append(dict(kind=kind, layout=layout, title=title, body=list(body), chart=chart, foot=foot, notes=notes, **extra))

    add("full", "cover", "Favoured Banks",
        [f"Which Indonesian banks ChatGPT and Gemini recommend, and which web pages they lean on"],
        kicker=f"A GEO STUDY  ·  {N['answers']} AI ANSWERS  ·  {SLATE_DATE}",
        byline="Rahmananda Ridho Gamawan",
        notes="A study of how two AI engines answer everyday banking questions in Indonesia, and which sources they cite. "
              "Everything here is built from public code and data in the repo named on the last slide.")
    add("letterbox", "cold_open", "One question, two answers",
        part="COLD OPEN", prompt=c["prompt"], english=c["english"],
        cols=[("ChatGPT named", _cold_banks(c["banks_gpt"]), "gpt"), ("Gemini named", _cold_banks(c["banks_gem"]), "gem")],
        foot=f"Prompt {N['cold_no']} of {N['prompts']}  ·  run on {SLATE_DATE}  ·  source: data/interim/mentions.csv",
        notes="A freelancer asks which bank fits irregular income. Both engines answer with a short list of banks. "
              "There is no results page to compete on: a bank is either in the answer or it is not.")
    add("full", "hero", "People now ask for answers. A strong Google rank is a weak guide to who gets cited.",
        heroes=[("14% → 24%", "share of ChatGPT conversations that seek information, a year apart",
                 "OpenAI usage study, via Search Engine Journal"),
                ("12%", "of URLs cited by AI assistants rank in Google's top 10 for the same query",
                 "Ahrefs, 15,000 prompts")],
        notes="Two outside numbers set the scene. Information-seeking is a growing share of ChatGPT use, and the pages "
              "AI assistants cite are mostly not the pages that rank on Google.")
    add("letterbox", "list", "Three questions",
        ["Which banks does each engine name, how early, and in what tone?",
         "Which sources does each engine cite, and do the two engines agree?",
         "Where does a bank's share of the answers differ from its share of the cited pages?"],
        part="COLD OPEN", numbered=True,
        notes="The rest of the deck answers these three questions in order.")
    add("title_card", "card", "Method", [f"{N['prompts']} prompts, {N['engines']} engines, one day"], part="PART I")
    add("letterbox", "side", f"{N['prompts']} everyday banking questions, asked in Bahasa Indonesia",
        [f"{N['pillars']} customer needs by {N['intents']} question types. Only {N['branded']} prompts name a bank, "
         f"all of them comparisons.",
         f"Each prompt was asked once in ChatGPT and once in Gemini, with a request for {N['per_answer']} sources.",
         f"The lit circle is prompt {N['cold_no']}, the cold open."],
        chart="prompt_grid", part="PART I · METHOD", foot=f"source: data/interim/answers.csv  ·  n = {N['prompts']} prompts",
        notes="The prompt set is written to be unbranded so share of voice is fair. Only the head-to-head comparisons "
              "name banks.")
    add("letterbox", "stack", f"From {N['answers']} answers to {N['readable']} readable source pages",
        ["Each step is code in the public repo, covered by tests. Only links under each answer's source list count as "
         "citations."],
        chart="pipeline", part="PART I · METHOD", foot=f"code and data: {REPO}  ·  n = {N['answers']} answers",
        notes="Parse the answers, split them into sentences, match bank names, extract the listed sources, deduplicate "
              "the pages, then crawl them from GitHub's servers while respecting robots.txt.")
    add("letterbox", "metrics", "What is measured",
        [("Mention rate", "share of answers that name the bank"),
         ("AI share of voice", "the bank's share of bank mentions, each answer weighted equally"),
         ("Brand PAWC", "how much of an answer is about the bank, earlier sentences weighted more"),
         ("Source share of voice", "the bank's share of bank mentions in the readable cited pages"),
         ("SOV gap", "AI share of voice minus source share of voice"),
         ("VIS", f"{N['vis_lo']} to {N['vis_hi']}: equal mix of PAWC, source authority, sentiment and coverage of "
                 "both engines")],
        chart="pawc_curve", part="PART I · METHOD",
        foot="PAWC adapted from Aggarwal et al., GEO: Generative Engine Optimization, KDD 2024",
        notes="Brand PAWC uses the position-adjusted word count from the GEO paper, applied to banks instead of sources. "
              "The chart shows the weight each sentence gets in a ten-sentence answer.")
    add("letterbox", "side", "The evidence, and what it cannot show",
        ["One run per prompt per engine: a snapshot.",
         f"Asking for {N['per_answer']} sources makes both engines cite more than usual.",
         f"{N['digital']} of {N['prompts']} prompts lean digital: they name digital banks or ask about apps.",
         "Claude labelled sentiment and site types; RG spot-checked a sample.",
         "Pages that blocked the crawler drop out of page-level measures.",
         f"Banks named in fewer than {N['low_n_cut']} answers are marked low n."],
        chart="funnel", part="PART I · METHOD", bullets=True, foot=f"source: data/interim/pages.csv, page_brand_counts.csv  ·  n = {N['pages']} pages",
        notes="The funnel shows how much of the cited web could be read. The list is what the data cannot tell you.")

    add("title_card", "card", "The answers", ["Who gets named, how early, and in what tone"], part="PART II")
    add("letterbox", "side", "BCA, Bank Jago and SeaBank are each named in more than half of all answers",
        [f"BCA and Bank Jago appear in {N['bca_n']} of {N['answers']} answers, SeaBank in {N['sea_n']}, "
         f"BRI in {N['bri_n']}."],
        chart="mention_dots", part="PART II · THE ANSWERS", foot=f"source: data/processed/brand_engine.csv  ·  top 10 banks  ·  n = {N['gem_answers']} answers per engine",
        notes="One dot per engine. The line between the dots is the gap between the engines for that bank.")
    add("letterbox", "side", "BCA scores highest, with Bank Jago and BRI close behind",
        [f"VIS {N['vis_bca']} for BCA, then Bank Jago {N['vis_jago']}, BRI {N['vis_bri']} and SeaBank {N['vis_sea']}.",
         f"Dashed bars are banks named in fewer than {N['low_n_cut']} answers. Read those as unranked."],
        chart="vis_rank", part="PART II · THE ANSWERS", foot=f"source: data/processed/vis.csv  ·  n = {N['answers']} answers",
        notes="VIS combines prominence in the answer, the authority of the pages cited alongside the bank, sentiment and "
              "whether both engines name it.")
    add("letterbox", "stack", f"Gemini names a wider field: {N['banks_gem']} banks against ChatGPT's {N['banks_gpt']}",
        [f"Bright marks are banks only one engine named. Gemini alone named Bank BTPN (Jenius) in {N['btpn_gem']} "
         f"answers and Superbank in {N['super_gem']}."],
        chart="wider_field", part="PART II · THE ANSWERS",
        foot=f"source: data/processed/brand_engine.csv  ·  n = {N['gem_answers']} answers per engine",
        notes="Apps and subsidiaries credit their parent bank, so Jenius counts for Bank BTPN and blu for BCA.")
    add("letterbox", "stack", "No bank leads every customer need, and no lead is more than one answer",
        [f"Counted on the {N['unb_prompts']} prompts that name no bank. {N['pillar_leads']}"],
        chart="pillar_heatmap", part="PART II · THE ANSWERS",
        foot=f"source: data/interim/answers.csv, mentions.csv  ·  share of a need's answers that name the bank  ·  "
             f"n = {N['unb_answers']} answers",
        notes="The three comparison prompts name banks, which puts those banks in the answer, so they are left out here. "
              "Outlined cells lead their row, ties together. Every lead is a tie or one answer, so read the rows as close.")
    add("letterbox", "side", "Named often and named early go together",
        ["BCA and Bank Jago lead on both measures.",
         "BRI scores higher on PAWC than SeaBank while appearing in fewer answers: when BRI is named, it takes up more "
         "of the answer."],
        chart="often_vs_early", part="PART II · THE ANSWERS",
        foot=f"source: data/processed/brand_engine.csv  ·  banks named in at least {N['low_n_cut']} answers  ·  "
             f"n = {N['answers']} answers",
        notes="Brand PAWC rises when a bank is named early and talked about at length.")
    add("letterbox", "stack", "No answer was negative about a bank",
        [f"Of {N['pairs']} answer and bank pairs, {N['positive']} are positive. The {N['mixed']} mixed labels attach a "
         f"condition, such as a minimum balance for free transfers. Being named at all is what to measure."],
        chart="sentiment_marks", part="PART II · THE ANSWERS",
        foot=f"source: data/labels/sentiment.csv  ·  labelled by Claude, spot-checked by RG  ·  n = {N['pairs']} pairs",
        notes="Each mark is one bank in one answer.")
    add("letterbox", "side", "How-to answers rarely name a bank",
        ["Every best and decision-brief answer named at least one bank.",
         f"Only {N['how_named']} of {N['how_n']} how-to answers did. Explainers on deposit insurance, scams and "
         f"complaints look like a gap for banks."],
        chart="intent_named", part="PART II · THE ANSWERS",
        foot=f"source: data/processed/no_brand_rate.csv  ·  n = {N['answers']} answers",
        notes="Questions about how something works get general answers without bank names.")

    add("title_card", "card", "The sources", ["Which pages the engines lean on"], part="PART III")
    add("letterbox", "stack", "ChatGPT cites banks and regulators. Gemini cites fintech, blog and news sites.",
        [f"{N['gpt_first']} of ChatGPT's citations go to bank and regulator sites. {N['gem_third']} of Gemini's go to "
         f"fintech platforms, blogs and news."],
        chart="source_mix", part="PART III · THE SOURCES",
        foot=f"source: data/processed/domain_type_mix.csv  ·  shares rounded on their own, sums can differ by 1 point  ·  "
             f"n = {N['cit_gpt']} and {N['cit_gem']} citations",
        notes="Site types were labelled per domain. Percentages are rounded.")
    add("letterbox", "side", f"The engines share sites more than pages: {N['sites_both']} of {N['sites_total']} sites, "
                             f"{N['pages_both']} of {N['pages_total']} pages",
        [f"{N['sites_both']} of ChatGPT's {N['gpt_sites']} sites are also cited by Gemini, but rarely the same page. "
         f"The Jaccard overlap is {N['jac_sites']} for sites and {N['jac_pages']} for pages.",
         "Writesonic found 0.119 between ChatGPT and Gemini across 88,969 prompts, without saying whether it "
         "compared pages or sites."],
        chart="overlap", part="PART III · THE SOURCES",
        foot=f"source: data/interim/citations.csv  ·  Writesonic, AI citation source overlap study  ·  "
             f"n = {N['sites_total']} sites, {N['pages_total']} pages",
        notes="A bank that wants to appear in both engines cannot rely on one set of pages.")
    add("letterbox", "stack", "Most cited sites: ChatGPT on the left, Gemini on the right",
        ["Bank and regulator sites lead for ChatGPT. Fazz, Akulaku and Zaipad are cited only by Gemini."],
        chart="mirror_sites", part="PART III · THE SOURCES",
        foot=f"source: data/processed/domains.csv  ·  top sites by citations  ·  n = {N['citations']} citations",
        notes="The fold in the middle is the comparison: the same sites, two very different weights.")
    add("letterbox", "stack", "A few comparison articles appear across Gemini's answers",
        [f"One Akulaku article is cited in {N['aku_page']} of Gemini's {N['gem_answers']} answers, one Zaipad article in "
         f"{N['zai_page']}, and Fazz articles {N['fazz_cit']} times across {N['fazz_ans']} answers. ChatGPT cites none "
         f"of them.",
         "Akulaku held 27.24% of Bank Neo Commerce in May 2023 (Bisnis). The article has not been checked for bias."],
        chart="top_pages", part="PART III · THE SOURCES",
        foot=f"source: data/processed/pages_top.csv  ·  most cited pages  ·  n = {N['citations']} citations",
        notes="If Gemini keeps citing the same few articles, a bank's place in them could carry into many answers.")
    add("letterbox", "side", "ChatGPT leans on fewer sites",
        [f"Its top five sites hold {N['conc_gpt']} of its citations. Gemini's top five hold {N['conc_gem']}."],
        chart="concentration", part="PART III · THE SOURCES",
        foot=f"source: data/processed/concentration.csv  ·  n = {N['cit_gpt']} and {N['cit_gem']} citations",
        notes="Higher concentration means a few sites carry more of the answers.")
    add("letterbox", "side", "Bank Mandiri gets less of the answers than its sources give it",
        [f"Bank Mandiri holds {N['mandiri_src']} of bank mentions in the cited pages and {N['mandiri_ai']} in the answers.",
         f"Bank Jago and BCA lean the other way. Bank Jago holds {N['jago_ai']} of mentions in the answers and "
         f"{N['jago_src']} in the pages.",
         "Pages were counted without a bare “Jago” or “blu”, so these two banks' source share may be low and their "
         "gaps too wide."],
        chart="sov_gap", part="PART III · THE SOURCES",
        foot=f"source: data/processed/source_sov.csv  ·  answers and pages weighted equally  ·  "
             f"n = {N['answers']} answers, {N['readable_bank']} pages",
        notes="A positive gap means the engines talk about the bank more than the cited pages do.")
    add("letterbox", "side", "Gemini's dead links all sit behind a Google redirect",
        [f"{N['wrapped_dead']} of its {N['wrapped']} links wrapped in google.com/search were dead. None of its "
         f"{N['direct']} direct links were.",
         "The Tow Center found Gemini gave more fabricated links than correct ones in its 2025 tests (Nieman Lab)."],
        chart="dead_links", part="PART III · THE SOURCES",
        foot=f"source: data/interim/citations.csv, pages.csv  ·  n = {N['cit_gem']} Gemini citations",
        notes="The redirect wrapper is where Gemini's broken links concentrate in this data.")
    add("letterbox", "side", "Pages without schema still get cited",
        [f"Bank sites carry schema on {N['sch_bank']} of cited pages, against {N['sch_news']} for news and "
         f"{N['sch_blog']} for blogs, yet they are the most cited type.",
         f"Only {N['dated']} of {N['readable_cit']} readable citations point to a page with a structured publish date.",
         "Google: “there's also no special schema.org structured data that you need to add.”"],
        chart="schema", part="PART III · THE SOURCES",
        foot=f"source: data/processed/schema.csv, recency.csv  ·  Google Search Central  ·  "
             f"n = {N['schema_pages']} pages, {N['readable_cit']} citations",
        notes="This suggests schema did not decide which pages got cited. It is a pattern, not a test.")

    add("title_card", "card", "What it means", ["For banks, and for people who measure AI search"], part="PART IV")
    add("letterbox", "list", "For banks",
        ["Plan for each engine. ChatGPT cites bank and regulator pages; Gemini cites comparison sites, blogs and news.",
         "Fee and rate pages look like the most direct route. ChatGPT cites SeaBank's and blu's fee pages by name.",
         f"Know what the comparison sites say about you. Gemini cites Akulaku's, Zaipad's and Fazz's sites in "
         f"{N['comp_lo']} to {N['comp_hi']} of its {N['gem_answers']} answers.",
         "No answer was negative. Measure whether you are named at all.",
         f"Write the explainers. Only {N['how_named']} of {N['how_n']} how-to answers named a bank."],
        part="PART IV · WHAT IT MEANS", numbered=True,
        notes="These are likely levers based on one snapshot, not tested interventions.")
    add("letterbox", "list", "For GEO practitioners: what building this taught me",
        ["Count only the listed sources. Inline links and source chips inflate citation counts.",
         "Unwrap redirects and normalise URLs before counting pages.",
         f"Render pages built with JavaScript. {N['rendered']} cited pages needed a headless browser to be read.",
         "Weight pages equally in source share, or one long annual report can dominate it.",
         "Weight answers equally in answer share, so one long answer does not count many times.",
         "Per-source PAWC needs inline citation markers. Neither engine gave them, so only brand PAWC is reported."],
        part="PART IV · WHAT IT MEANS", numbered=True,
        notes="Each of these came from a bug or a check during the build. The fixes and tests are in the repo history.")
    add("letterbox", "list", "One run is a snapshot",
        ["SparkToro and Gumshoe ran 12 prompts nearly 3,000 times. The same brand list came back less than 1 in 100 "
         "times (Search Engine Land, January 2026).",
         f"Read gaps of a few points here as ties: BCA and Bank Jago at {N['bca_rate']}, SeaBank at {N['sea_rate']}."],
        part="PART IV · WHAT IT MEANS",
        notes="Repeat runs would turn each number into a range.")
    add("letterbox", "list", "Next steps",
        [f"Run the same {N['prompts']} prompts at least four more times, so every number has a range.",
         "Add Perplexity, Microsoft Copilot and Google AI Mode.",
         "Read the top Gemini comparison articles and record how each one describes each bank.",
         "Put the tables in a public dashboard that refreshes after each run."],
        part="PART IV · WHAT IT MEANS", numbered=True)
    add("full", "close", "Favoured Banks in ChatGPT and Gemini",
        [f"Data, code and method: {REPO}"],
        sources=["Aggarwal et al. (2024). GEO: Generative Engine Optimization. KDD 2024. arXiv 2311.09735",
                 "Writesonic. AI citation source overlap study",
                 "Ahrefs. AI search overlap with Google results",
                 "Search Engine Land. AI recommendation lists rarely repeat (SparkToro and Gumshoe)",
                 "Nieman Lab (2025). Tow Center study of AI search citations",
                 "Google Search Central. AI features and your website",
                 "Search Engine Journal. OpenAI usage study",
                 "Bisnis (2023). Akulaku stake in Bank Neo Commerce"],
        byline="Rahmananda Ridho Gamawan  ·  data analyst, Indonesia")
    return S


def allowed_numbers(f: dict) -> set:
    pat = re.compile(r"\d[\d,.]*\d|\d")
    ordinals = [f"{i:02d}" for i in range(1, 10)]  # list item numbers
    pool = list(numbers(f).values()) + list(EXTERNAL) + [SLATE_DATE] + ordinals
    found = set()
    for v in pool:
        found.update(t.rstrip(".,") for t in pat.findall(str(v)))
    return found
