import unittest
from pathlib import Path

from citation_check.parser import parse_memo, render

MEMO = Path("samples/memo.md").read_text()

class ParserTests(unittest.TestCase):
    def test_missing_year_and_leading_id(self):
        report = parse_memo(MEMO)
        self.assertTrue(any(h.kind == "malformed" and "88 F. Supp. 2d 12" in h.text for h in report.hits))
        self.assertGreaterEqual(len(report.id_no_antecedent), 1)
        self.assertTrue(report.id_no_antecedent[0].start < report.parsed[0].start)

    def test_full_cite_and_following_id(self):
        report = parse_memo(MEMO)
        full = report.parsed[0]
        self.assertEqual(full.volume, "512")
        self.assertEqual(full.reporter, "F.3d")
        self.assertEqual(full.page, "840")
        self.assertEqual(full.year, "2008")
        self.assertIn("9th Cir.", full.court)
        following = [h for h in report.hits if h.kind == "id" and h.detail.startswith("antecedent")]
        self.assertTrue(following)

    def test_repeated(self):
        report = parse_memo(MEMO)
        self.assertEqual(len(report.repeated), 1)

    def test_sample_report_matches_renderer(self):
        report = parse_memo(MEMO)
        expected = Path("samples/citation-report.md").read_text()
        self.assertEqual(expected, render(report, "memo.md"))

if __name__ == "__main__":
    unittest.main()
