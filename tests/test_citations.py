from scripts.io import read_csv
from scripts.parse import extract_citations, main, normalize_url


def test_unwrap_google_redirect():
    assert normalize_url("https://www.google.com/search?q=https://www.bca.co.id/id/x") == "https://bca.co.id/id/x"


def test_label_real_href_redirect_and_reverse():
    a = "1. [https://www.ojk.go.id/p](https://www.google.com/search?q=https://www.ojk.go.id/p)"
    b = "1. [https://www.google.com/search?q=https://www.ojk.go.id/p](https://www.ojk.go.id/p)"
    assert extract_citations(a)[0][1] == extract_citations(b)[0][1] == "https://ojk.go.id/p"


def test_utm_and_trailing_slash():
    assert normalize_url("https://www.jago.com/id/?utm_source=chatgpt.com&x=1") == "https://jago.com/id?x=1"


def test_duplicate_within_answer_kept_once():
    sec = "1. [https://blubybcadigital.id/info/fees-rates](x)\n2. [https://blubybcadigital.id/info/fees-rates/](y)"
    assert len(extract_citations(sec)) == 1


def test_real_counts():
    main()
    c = read_csv("data/interim/citations.csv")
    assert (len(c), c.url.nunique(), c.domain.nunique()) == (399, 241, 99)
    assert c.groupby("answer_id").size().drop("gpt-02").eq(10).all()
