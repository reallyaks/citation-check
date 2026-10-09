# citation-check

Form check for case citations in a memo written for England and Wales.

It reads neutral citations (`[2018] EWCA Civ 214`), the main law reports (`[2019] QB 112`), and `ibid`. A neutral citation with no case number is malformed. `ibid` before any citation is an error. A US reporter (`512 F.3d 840`) is flagged as the wrong form. It is not converted.

It does not say the case exists, is good law, or decides the point. Leave `COURT_LISTENER_TOKEN` unset. That variable is ignored. There is no network call.

## Sample

[samples/memo.md](samples/memo.md) is a short fictional note. The report is [samples/citation-report.md](samples/citation-report.md).

The planted faults are an opening `ibid`, `[2024] EWHC (Comm)` with no number, a repeated neutral citation, and one US reporter.

## Run

```bash
python -m citation_check samples/memo.md --out /tmp/citation-report.md
python -m unittest discover -s tests
```

Python 3.10+. No packages.
