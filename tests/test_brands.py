from scripts.brands import Brand, credit, find_matches

B = [Brand("BCA", None, "conventional", ["BCA", "Bank Central Asia"], True, False, []),
     Brand("blu", "BCA", "digital", ["blu by BCA Digital", "BCA Digital", "blu"], True, True, ["blu"]),
     Brand("Bank Jago", None, "digital", ["Bank Jago", "Jago"], True, True, ["Jago"])]


def test_longest_alias_and_rollup():
    m = find_matches("Buka blu by BCA Digital sekarang.", B)
    assert [credit(x.brand) for x in m] == [("BCA", "blu")]


def test_parent_and_sub_in_one_sentence_two_mentions():
    assert len(find_matches("BCA dan blu sama-sama bagus.", B)) == 2


def test_lowercase_jago_is_not_a_bank():
    assert find_matches("Dia jago masak.", B) == []


def test_case_sensitive_acronym():
    assert find_matches("bca", B) == [] and len(find_matches("BCA", B)) == 1


def test_unambiguous_only_skips_bare_jago():
    assert find_matches("Jago itu", B, unambiguous_only=True) == []
    assert len(find_matches("Bank Jago itu", B, unambiguous_only=True)) == 1


def test_word_boundary_inside_longer_token():
    assert find_matches("myBCA dan BCAmobile", B) == []


def test_brands_yaml_valid_and_all_review_done():
    from scripts.brands import load_brands
    from scripts.io import ROOT, read_csv
    bs = load_brands(ROOT / "config/brands.yaml")
    names = {b.brand for b in bs}
    assert all(b.parent in names for b in bs if b.parent)
    assert all(set(b.ambiguous_aliases) <= set(b.aliases) for b in bs)
    h = read_csv("data/labels/ambiguous_hits.csv")
    assert h.decision.isin(["keep", "reject"]).all()
