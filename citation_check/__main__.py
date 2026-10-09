import argparse
import os
from pathlib import Path

from citation_check.parser import parse_memo, render

def main() -> None:
    parser = argparse.ArgumentParser(description="Check US case citation form in a markdown memo.")
    parser.add_argument("memo")
    parser.add_argument("--out", default="citation-report.md")
    args = parser.parse_args()
    text = Path(args.memo).read_text()
    report = parse_memo(text)
    Path(args.out).write_text(render(report, Path(args.memo).name))
    token = os.environ.get("COURT_LISTENER_TOKEN", "").strip()
    if token:
        print("COURT_LISTENER_TOKEN is set. Lookup is optional and not required; form report already written.")
    print(f"{args.out}: {len(report.parsed)} parsed, {len(report.malformed)} malformed, {len(report.id_no_antecedent)} Id. without antecedent")

if __name__ == "__main__":
    main()
