"""Keep the README GitHub Overview section in sync with collected statistics.

The block between the PROFILE_STATS markers is regenerated on every run.
When the public profile exposes no meaningful data at all, the whole section
(including the "## GitHub Overview" heading) is dropped so the README never
shows an empty statistics block.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

START_MARKER = "<!-- PROFILE_STATS:START -->"
END_MARKER = "<!-- PROFILE_STATS:END -->"

_PICTURE = (
    "<picture>\n"
    '  <source media="(prefers-color-scheme: dark)" srcset="./assets/statistics/{slug}-dark.svg">\n'
    '  <source media="(prefers-color-scheme: light)" srcset="./assets/statistics/{slug}-light.svg">\n'
    '  <img src="./assets/statistics/{slug}-light.svg" alt="{alt}">\n'
    "</picture>"
)


def has_profile_data(stats: dict[str, Any]) -> bool:
    """True when the public profile exposes anything worth displaying."""
    contributions = stats.get("contributions") or {}
    return bool(
        stats.get("public_repositories")
        or stats.get("stars")
        or stats.get("forks")
        or stats.get("followers")
        or contributions.get("total")
        or stats.get("languages")
    )


def render_section(stats: dict[str, Any]) -> str:
    """Render the full section, or an empty string when there is no data."""
    lines: list[str] = []
    if has_profile_data(stats):
        lines += ["## GitHub Overview", ""]
        lines.append(_PICTURE.format(slug="overview", alt="GitHub public profile overview"))
    if stats.get("languages"):
        if lines:
            lines.append("")
        lines.append(_PICTURE.format(slug="languages", alt="Public repository language distribution"))
    return "\n".join(lines)


def update_readme(root: Path, stats: dict[str, Any]) -> bool:
    """Rewrite the marked block in place. Returns True when the file changed."""
    readme = root / "README.md"
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Could not read README.md; skipped README update ({error}).", file=sys.stderr)
        return False
    if START_MARKER not in text or END_MARKER not in text:
        print("PROFILE_STATS markers missing in README.md; skipped README update.", file=sys.stderr)
        return False

    start = text.index(START_MARKER)
    content_start = start + len(START_MARKER)
    end = text.index(END_MARKER, content_start)
    updated = text[:content_start] + "\n" + render_section(stats) + "\n" + text[end:]
    if updated == text:
        print("README GitHub Overview section is unchanged.")
        return False
    readme.write_text(updated, encoding="utf-8")
    return True
