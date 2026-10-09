"""Rebuild every local output from data/raw and the committed labels. The crawl runs separately in GitHub Actions."""
from scripts import brands, metrics, parse, quality, sentences


def main() -> None:
    parse.main()
    sentences.main()
    brands.main()
    metrics.main()
    quality.main()


if __name__ == "__main__":
    main()
