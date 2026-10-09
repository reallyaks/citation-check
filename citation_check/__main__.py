import argparse
from pathlib import Path

from citation_check.parser import parse_memo, render

def main() -> None:
    parser = argparse.ArgumentParser(description="Check English case-citation form in a markdown memo.")
    parser.add_argument("memo")
    parser.add_argument("--out", default="citation-report.md")
    args = parser.parse_args()
    text = Path(args.memo).read_text()
    report = parse_memo(text)
    Path(args.out).write_text(render(report, Path(args.memo).name))
    print(
        f"{args.out}: {len(report.parsed)} parsed, {len(report.malformed)} malformed, "
        f"{len(report.ibid_no_antecedent)} ibid without antecedent, {len(report.us_reporter)} US reporters"
    )

if __name__ == "__main__":
    main()
