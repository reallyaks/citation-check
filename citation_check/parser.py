"""Form check for English case citations. Offline. Not a citator."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NEUTRAL_RE = re.compile(
    r"\[(?P<year>(?:19|20)\d{2})\]\s+"
    r"(?P<court>UKSC|UKPC|EWCA\s+Civ|EWCA\s+Crim|EWHC|UKUT|UKFTT)\s+"
    r"(?P<number>\d+)(?:\s+\((?P<division>[^)]{1,40})\))?",
    re.IGNORECASE,
)
BROKEN_NEUTRAL_RE = re.compile(
    r"\[(?P<year>(?:19|20)\d{2})\]\s+"
    r"(?P<court>UKSC|UKPC|EWCA\s+Civ|EWCA\s+Crim|EWHC|UKUT|UKFTT)\s+"
    r"\((?P<division>[^)]{1,40})\)",
    re.IGNORECASE,
)
REPORT_RE = re.compile(
    r"\[(?P<year>(?:19|20)\d{2})\]\s+(?:(?P<volume>\d+)\s+)?"
    r"(?P<series>AC|QB|Ch|Fam|WLR|All ER)\s+(?P<page>\d+)"
)
US_RE = re.compile(
    r"\b\d{1,4}\s+(?:F\.4th|F\.3d|F\.2d|F\.\s*Supp\.(?:\s*3d|\s*2d)?|U\.S\.|S\.\s*Ct\.)\s+\d+"
)
IBID_RE = re.compile(r"(?<!\w)ibid\.?(?:\s+\[?(?P<pin>\d+)\]?)?", re.IGNORECASE)


@dataclass
class Hit:
    kind: str
    text: str
    start: int
    detail: str
    year: str = ""
    court: str = ""
    number: str = ""
    series: str = ""
    page: str = ""


@dataclass
class Report:
    hits: list[Hit] = field(default_factory=list)

    @property
    def parsed(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.kind in {"neutral", "report"}]

    @property
    def malformed(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.kind == "malformed"]

    @property
    def ibid_no_antecedent(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.kind == "ibid-no-antecedent"]

    @property
    def repeated(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.kind == "repeated"]

    @property
    def us_reporter(self) -> list[Hit]:
        return [hit for hit in self.hits if hit.kind == "us-reporter"]


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(not (end <= left or start >= right) for left, right in spans)


def parse_memo(text: str) -> Report:
    spans: list[tuple[int, int, Hit]] = []
    occupied: list[tuple[int, int]] = []

    def take(start: int, end: int, hit: Hit) -> None:
        if _overlaps(start, end, occupied):
            return
        occupied.append((start, end))
        spans.append((start, end, hit))

    for match in NEUTRAL_RE.finditer(text):
        take(
            match.start(),
            match.end(),
            Hit(
                kind="neutral",
                text=match.group(0),
                start=match.start(),
                detail="neutral citation",
                year=match.group("year"),
                court=re.sub(r"\s+", " ", match.group("court")),
                number=match.group("number"),
            ),
        )
    for match in BROKEN_NEUTRAL_RE.finditer(text):
        take(
            match.start(),
            match.end(),
            Hit(
                kind="malformed",
                text=match.group(0),
                start=match.start(),
                detail="neutral citation with no case number",
                year=match.group("year"),
                court=re.sub(r"\s+", " ", match.group("court")),
            ),
        )
    for match in REPORT_RE.finditer(text):
        take(
            match.start(),
            match.end(),
            Hit(
                kind="report",
                text=match.group(0),
                start=match.start(),
                detail="law report",
                year=match.group("year"),
                series=match.group("series"),
                page=match.group("page"),
                number=match.group("volume") or "",
            ),
        )
    for match in US_RE.finditer(text):
        take(
            match.start(),
            match.end(),
            Hit(
                kind="us-reporter",
                text=match.group(0),
                start=match.start(),
                detail="US reporter. Not a neutral citation and not a law report used in England and Wales.",
            ),
        )
    for match in IBID_RE.finditer(text):
        take(
            match.start(),
            match.end(),
            Hit(kind="ibid", text=match.group(0), start=match.start(), detail="ibid", page=match.group("pin") or ""),
        )

    spans.sort(key=lambda item: item[0])
    report = Report()
    last: Hit | None = None
    seen: dict[tuple[str, str, str], int] = {}
    for _, _, hit in spans:
        if hit.kind in {"neutral", "report"}:
            key = (hit.kind, hit.year, hit.number if hit.kind == "neutral" else f"{hit.series} {hit.page}")
            if hit.kind == "neutral":
                key = ("neutral", f"{hit.year} {hit.court}", hit.number)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > 1:
                hit.kind = "repeated"
                hit.detail = "repeats an earlier citation"
            last = hit
            report.hits.append(hit)
        elif hit.kind == "ibid":
            if last is None or last.kind not in {"neutral", "report", "repeated"}:
                hit.kind = "ibid-no-antecedent"
                hit.detail = "ibid appears before any neutral citation or law report"
            else:
                hit.detail = f"follows {last.text}"
            report.hits.append(hit)
        else:
            report.hits.append(hit)
    return report


def render(report: Report, source: str) -> str:
    lines = [
        f"# Citation report — {source}",
        "",
        "Form only, for a memo written to English citation practice: neutral citations, the main law reports, and ibid.",
        "It does not confirm that a case exists, or that the pinpoint is right. A US reporter is flagged because it is the wrong form here, not because the case was read.",
        "",
        "## Counts",
        "",
        "| | |",
        "| --- | --- |",
        f"| neutral or law report | {len(report.parsed)} |",
        f"| malformed | {len(report.malformed)} |",
        f"| ibid with no antecedent | {len(report.ibid_no_antecedent)} |",
        f"| repeated | {len(report.repeated)} |",
        f"| US reporter | {len(report.us_reporter)} |",
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
