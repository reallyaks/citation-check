import unittest
from pathlib import Path

from citation_check.parser import parse_memo, render

MEMO = Path("samples/memo.md").read_text()


class ParserTests(unittest.TestCase):
    def test_leading_ibid_and_missing_case_number(self):
        report = parse_memo(MEMO)
        self.assertGreaterEqual(len(report.ibid_no_antecedent), 1)
        self.assertTrue(report.ibid_no_antecedent[0].start < report.parsed[0].start)
        self.assertTrue(any(hit.kind == "malformed" and "EWHC" in hit.text for hit in report.hits))

    def test_neutral_citation_and_following_ibid(self):
        report = parse_memo(MEMO)
        neutral = next(hit for hit in report.parsed if hit.kind == "neutral")
        self.assertEqual(neutral.year, "2018")
        self.assertEqual(neutral.court.upper(), "EWCA CIV")
        self.assertEqual(neutral.number, "214")
        following = [hit for hit in report.hits if hit.kind == "ibid"]
        self.assertTrue(following)
        self.assertTrue(following[0].detail.startswith("follows"))

    def test_us_reporter_is_not_treated_as_authority(self):
        report = parse_memo(MEMO)
        self.assertEqual(len(report.us_reporter), 1)
        self.assertIn("F.3d", report.us_reporter[0].text)
        self.assertEqual(len(report.repeated), 1)

    def test_sample_report_matches_renderer(self):
        report = parse_memo(MEMO)
        self.assertEqual(Path("samples/citation-report.md").read_text(), render(report, "memo.md"))


if __name__ == "__main__":
    unittest.main()
