"""Fetch public GitHub data and render local SVG assets."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from github_client import GitHubClient  # noqa: E402
from statistics import collect_statistics  # noqa: E402
from generate_svgs import generate_all  # noqa: E402
from profile_readme import update_readme  # noqa: E402


def main() -> int:
    config = json.loads((ROOT / "config" / "profile.json").read_text(encoding="utf-8"))
    username = os.getenv("GITHUB_USERNAME", config["username"])
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required. Set it in your environment or GitHub Actions secret.")
    stats = collect_statistics(GitHubClient(token), username, config)
    generate_all(stats, int(config.get("svg_width", 920)))
    output = ROOT / "assets" / "statistics" / "stats.json"
    output.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated profile statistics for {username} at {stats['generated_at']}")
    print(f"Public repositories: {stats['public_repositories']} | Stars: {stats['stars']} | Contributions: {stats['contributions']['total']}")
    if update_readme(ROOT, stats):
        print("Updated README GitHub Overview section.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
