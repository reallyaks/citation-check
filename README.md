# citation-check

Open [samples/citation-report.md](samples/citation-report.md) first. The memo it came from is [samples/memo.md](samples/memo.md).

Checks the *form* of US case citations in a markdown memo: volume, reporter, page, optional pincite, court, year, plus `Id.` antecedents.

Not a citator. Not legal advice. It will not tell you the case is real, good law, or on point.

## Two deliberate errors in the sample

[samples/memo.md](samples/memo.md) is a short fictional memo.

- `Id. at 14` in the question presented has no full cite before it.
- `88 F. Supp. 2d 12 (D. Or.)` has no year.
- `512 F.3d 840 (9th Cir. 2008)` is repeated later and marked repeated, not malformed.

The committed report is [samples/citation-report.md](samples/citation-report.md). You can read it without running anything.

## Run

```bash
python -m citation_check samples/memo.md --out /tmp/citation-report.md
python -m unittest discover -s tests
```

No third-party packages. Python 3.10+.

## Optional lookup

Leave `COURT_LISTENER_TOKEN` unset. The default path never calls the network. If the variable is set, the CLI prints a one-line note and still writes the offline form report. The citation-refusal problem in a sibling tool matters more than a live lookup here: a missing year is a form error even when the network is down.
