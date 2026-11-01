import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_svgs


class SvgGenerationTests(unittest.TestCase):
    def test_generates_valid_light_and_dark_svgs(self):
        stats = {
            "generated_at": "2026-11-01T00:00:00+00:00",
            "public_repositories": 3, "stars": 7, "forks": 2, "followers": 5,
            "languages": [{"name": "Python", "bytes": 100, "percentage": 100.0}],
            "contributions": {
                "total": 10, "commits": 8, "issues": 1, "pull_requests": 1,
                "days": [{"date": "2026-10-31", "weekday": 6, "contributionCount": 2}],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(generate_svgs, "OUT", Path(directory)):
                generate_svgs.generate_all(stats, width=920)
            generated = list(Path(directory).glob("*.svg"))
            self.assertEqual(len(generated), 6)
            for svg in generated:
                ET.parse(svg)


if __name__ == "__main__":
    unittest.main()
