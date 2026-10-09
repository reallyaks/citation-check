"""US case-citation form checker. Offline. Not a citator."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

REPORTER = (
    r"F\.4th|F\.3d|F\.2d|F\. Supp\. 3d|F\. Supp\. 2d|F\. Supp\.|"
    r"U\.S\.|S\. Ct\.|L\. Ed\. 2d|A\.3d|A\.2d|N\.E\.3d|N\.W\.2d|"
    r"P\.3d|S\.E\.2d|So\. 3d|S\.W\.3d|Cal\. App\. 5th|N\.Y\.3d"
)
FULL_RE = re.compile(
    rf"(?<!\w)(?P<volume>\d{{1,4}})[\t ]+(?P<reporter>{REPORTER})[\t ]+"
    rf"(?P<page>\d{{1,5}})(?:[\t ]*,[\t ]*(?P<pincite>\d{{1,5}}(?:[\t ]*[-–][\t ]*\d{{1,5}})?))?[\t ]*"
    rf"\((?:(?P<court>[^()]{{1,80}}?)[\t ]+)?(?P<year>(?:17|18|19|20)\d{{2}})\)"
)
MISSING_YEAR_RE = re.compile(
    rf"(?<!\w)(?P<volume>\d{{1,4}})[\t ]+(?P<reporter>{REPORTER})[\t ]+"
    rf"(?P<page>\d{{1,5}})(?:[\t ]*,[\t ]*(?P<pincite>\d{{1,5}}))?[\t ]*"
    rf"\((?P<court>[^()]{{1,80}})\)"
)
ID_RE = re.compile(r"(?<!\w)Id\.(?:[\t ]+at[\t ]+(?P<pincite>\d{1,5}))?", re.IGNORECASE)


@dataclass
class Hit:
    kind: str
    text: str
    start: int
    detail: str
    volume: str = ""
    reporter: str = ""
    page: str = ""
    year: str = ""
    court: str = ""
    pincite: str = ""


@dataclass
class Report:
    hits: list[Hit] = field(default_factory=list)

    @property
    def parsed(self) -> list[Hit]:
        return [h for h in self.hits if h.kind == "full"]

    @property
    def malformed(self) -> list[Hit]:
        return [h for h in self.hits if h.kind == "malformed"]

    @property
    def id_no_antecedent(self) -> list[Hit]:
        return [h for h in self.hits if h.kind == "id-no-antecedent"]

    @property
    def repeated(self) -> list[Hit]:
        return [h for h in self.hits if h.kind == "repeated"]


def parse_memo(text: str) -> Report:
    spans: list[tuple[int, int, Hit]] = []
    for match in FULL_RE.finditer(text):
        hit = Hit(
            kind="full",
            text=match.group(0),
            start=match.start(),
            detail="full cite",
            volume=match.group("volume"),
            reporter=match.group("reporter"),
            page=match.group("page"),
            year=match.group("year"),
            court=(match.group("court") or "").strip(),
            pincite=match.group("pincite") or "",
        )
        spans.append((match.start(), match.end(), hit))
    occupied = [(a, b) for a, b, _ in spans]
    for match in MISSING_YEAR_RE.finditer(text):
        if any(not (match.end() <= a or match.start() >= b) for a, b in occupied):
            continue
        spans.append(
            (
                match.start(),
                match.end(),
                Hit(
                    kind="malformed",
                    text=match.group(0),
                    start=match.start(),
                    detail="missing year",
                    volume=match.group("volume"),
                    reporter=match.group("reporter"),
                    page=match.group("page"),
                    court=(match.group("court") or "").strip(),
                    pincite=match.group("pincite") or "",
                ),
            )
        )
    for match in ID_RE.finditer(text):
        spans.append(
            (
                match.start(),
                match.end(),
                Hit(
                    kind="id",
                    text=match.group(0),
                    start=match.start(),
                    detail="id",
                    pincite=match.group("pincite") or "",
                ),
            )
        )
    spans.sort(key=lambda item: item[0])
    report = Report()
    last_full: Hit | None = None
    seen: dict[tuple[str, str, str], int] = {}
    for _, _, hit in spans:
        if hit.kind == "full":
            key = (hit.volume, hit.reporter, hit.page)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > 1:
                hit.kind = "repeated"
                hit.detail = f"repeats {hit.volume} {hit.reporter} {hit.page}"
            last_full = hit if hit.kind == "full" else last_full
            if hit.kind == "repeated":
                # still a usable antecedent
                last_full = Hit(
                    kind="full",
                    text=hit.text,
                    start=hit.start,
                    detail="full cite",
                    volume=hit.volume,
                    reporter=hit.reporter,
                    page=hit.page,
                    year=hit.year,
                    court=hit.court,
                )
            report.hits.append(hit)
        elif hit.kind == "malformed":
            report.hits.append(hit)
        else:
            if last_full is None:
                hit.kind = "id-no-antecedent"
                hit.detail = "Id. appears before any full citation"
            else:
                hit.detail = f"antecedent {last_full.volume} {last_full.reporter} {last_full.page}"
                hit.kind = "id"
            report.hits.append(hit)
    return report


def render(report: Report, source: str) -> str:
    lines = [
        f"# Citation report — {source}",
        "",
        "Form check only. This does not confirm that a case exists or that a pincite is accurate.",
        "Offline by default. Set COURT_LISTENER_TOKEN to attempt a lookup; this sample report did not.",
        "",
        "## Counts",
        "",
        "| | |",
        "| --- | --- |",
        f"| parsed | {len(report.parsed)} |",
        f"| malformed | {len(report.malformed)} |",
        f"| Id. with no antecedent | {len(report.id_no_antecedent)} |",
        f"| repeated | {len(report.repeated)} |",
        "",
        "## Hits",
        "",
        "| Kind | Text | Detail |",
        "| --- | --- | --- |",
    ]
    for hit in report.hits:
        lines.append(f"| {hit.kind} | {hit.text} | {hit.detail} |")
    if not report.hits:
        lines.append("| — | — | none |")
    lines.append("")
    return "\n".join(lines)
