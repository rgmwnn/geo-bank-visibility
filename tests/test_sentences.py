from scripts.io import read_csv
from scripts.sentences import clean_body, main, split_sentences

CHIP = ("Teks pertama.\n\n![](https://www.google.com/s2/favicons?domain=x)\n\nNEXT Indonesia Center\n\n+1\n\n"
        "Add to Favorites\n\nTeks kedua.")


def test_chip_artifacts_removed():
    assert split_sentences(clean_body(CHIP)) == ["Teks pertama.", "Teks kedua."]


def test_decimals_currency_abbrev_not_split():
    s = split_sentences("Bunga 6,5% p.a. untuk saldo Rp2.000.000. PT Bank Central Asia Tbk. menawarkan ini. No. 3 juga.")
    assert s == ["Bunga 6,5% p.a. untuk saldo Rp2.000.000.", "PT Bank Central Asia Tbk. menawarkan ini.", "No. 3 juga."]


def test_list_items_and_table_rows_are_sentences():
    md = "* **SeaBank:** bunga 3,5%\n* Jago: gratis\n\n| Bank | Bunga |\n| --- | --- |\n| Krom | 7% |"
    assert split_sentences(clean_body(md)) == ["SeaBank: bunga 3,5%", "Jago: gratis", "Bank Bunga", "Krom 7%"]


def test_link_text_kept_hr_dropped():
    assert split_sentences(clean_body("Cek [situs LPS](https://lps.go.id).\n\n---\n\nSelesai.")) == ["Cek situs LPS.", "Selesai."]


def test_real_file_every_answer_has_sentences():
    main()
    s = read_csv("data/interim/sentences.csv")
    assert s.answer_id.nunique() == 40 and (s.n_words > 0).all()
    assert not s.text.str.contains(r"^\+\d+$|Add to Favorites|images\.openai\.com").any()


def test_domain_only_chip_line_dropped():
    assert split_sentences(clean_body("Rating bisa berubah.\n\nmedianasabah.com\n\nLanjut di sini.")) == [
        "Rating bisa berubah.", "Lanjut di sini."]


def test_br_tags_and_bullet_char():
    md = "| Jago | Kuota berjenjang:<br>\n<br>• Level 4: 150x<br>\n<br>• Level 3: 60x |"
    assert split_sentences(clean_body(md)) == ["Jago Kuota berjenjang:", "Level 4: 150x", "Level 3: 60x"]


def test_bare_numbering_and_punctuation_only_lines_dropped():
    assert split_sentences(clean_body("Langkah awal.\n\n1.\n\nCara komplain ke bank\n\n.\n\nSelesai.")) == [
        "Langkah awal.", "Cara komplain ke bank", "Selesai."]


def test_long_chip_title_between_favicon_and_plus_dropped():
    md = ("Isi pertama.\n\n![](https://www.google.com/s2/favicons?domain=x)\n\nPerbedaan BCA Mobile dan myBCA\n\n+4\n\n"
          "Isi kedua yang panjang sekali di sini.")
    assert split_sentences(clean_body(md)) == ["Isi pertama.", "Isi kedua yang panjang sekali di sini."]
