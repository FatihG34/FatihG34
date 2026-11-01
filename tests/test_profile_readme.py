import tempfile
import unittest
from pathlib import Path
from typing import Any

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from profile_readme import (  # noqa: E402
    END_MARKER,
    START_MARKER,
    has_profile_data,
    render_section,
    update_readme,
)

README_TEMPLATE = "# Profile\n\n{start}\nOLD CONTENT\n{end}\n\n## Next Section\n"

FULL_STATS: dict[str, Any] = {
    "public_repositories": 3, "stars": 7, "forks": 2, "followers": 5,
    "languages": [{"name": "Python", "bytes": 100, "percentage": 100.0}],
    "contributions": {"total": 10},
}

EMPTY_STATS: dict[str, Any] = {
    "public_repositories": 0, "stars": 0, "forks": 0, "followers": 0,
    "languages": [],
    "contributions": {"total": 0},
}


class HasProfileDataTests(unittest.TestCase):
    def test_full_stats_have_data(self):
        self.assertTrue(has_profile_data(FULL_STATS))

    def test_empty_stats_have_no_data(self):
        self.assertFalse(has_profile_data(EMPTY_STATS))

    def test_any_single_metric_counts_as_data(self):
        for key, value in [
            ("public_repositories", 1), ("stars", 1), ("forks", 1), ("followers", 1),
        ]:
            with self.subTest(key=key):
                self.assertTrue(has_profile_data({**EMPTY_STATS, key: value}))
        self.assertTrue(has_profile_data({**EMPTY_STATS, "languages": [{"name": "Go"}]}))
        self.assertTrue(has_profile_data({**EMPTY_STATS, "contributions": {"total": 1}}))


class RenderSectionTests(unittest.TestCase):
    def test_renders_heading_and_pictures_with_data(self):
        section = render_section(FULL_STATS)
        self.assertIn("## GitHub Overview", section)
        self.assertIn("./assets/statistics/overview-light.svg", section)
        self.assertIn("./assets/statistics/languages-light.svg", section)

    def test_renders_nothing_without_data(self):
        self.assertEqual(render_section(EMPTY_STATS), "")

    def test_skips_languages_picture_without_languages(self):
        stats = {**FULL_STATS, "languages": []}
        section = render_section(stats)
        self.assertIn("overview-light.svg", section)
        self.assertNotIn("languages", section)


class UpdateReadmeTests(unittest.TestCase):
    def write_readme(self, root: Path) -> None:
        (root / "README.md").write_text(
            README_TEMPLATE.format(start=START_MARKER, end=END_MARKER), encoding="utf-8"
        )

    def test_removes_whole_section_when_no_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_readme(root)
            self.assertTrue(update_readme(root, EMPTY_STATS))
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertNotIn("## GitHub Overview", text)
            self.assertNotIn("OLD CONTENT", text)
            self.assertIn(START_MARKER, text)
            self.assertIn(END_MARKER, text)
            self.assertIn("## Next Section", text)

    def test_rewrites_section_with_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_readme(root)
            update_readme(root, FULL_STATS)
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("## GitHub Overview", text)
            self.assertNotIn("OLD CONTENT", text)

    def test_is_idempotent_when_content_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_readme(root)
            update_readme(root, FULL_STATS)
            self.assertFalse(update_readme(root, FULL_STATS))

    def test_skips_when_markers_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Profile without markers\n", encoding="utf-8")
            self.assertFalse(update_readme(root, EMPTY_STATS))

    def test_skips_when_readme_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(update_readme(Path(directory), EMPTY_STATS))


if __name__ == "__main__":
    unittest.main()
