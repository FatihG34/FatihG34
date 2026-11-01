"""Generate self-hosted, GitHub Light/Dark compatible SVG cards."""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, TypedDict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "statistics"
class Palette(TypedDict):
    bg: str
    panel: str
    text: str
    muted: str
    border: str
    levels: list[str]


PALETTES: dict[str, Palette] = {
    "light": {"bg": "#ffffff", "panel": "#f6f8fa", "text": "#1f2328", "muted": "#656d76", "border": "#d1d9e0", "levels": ["#ebedf0", "#aceebb", "#4ac26b", "#2da44e", "#116329"]},
    "dark": {"bg": "#0d1117", "panel": "#161b22", "text": "#e6edf3", "muted": "#9198a1", "border": "#30363d", "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]},
}


def svg_document(width: int, height: int, body: str, palette: Palette, title: str) -> str:
    style = (
        f"text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}"
        f".title{{font-size:17px;font-weight:700;fill:{palette['text']}}}"
        f".label{{font-size:12px;fill:{palette['muted']}}}"
        f".value{{font-size:25px;font-weight:700;fill:{palette['text']}}}"
        f".small{{font-size:11px;fill:{palette['muted']}}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f'<title>{escape(title)}</title>'
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="14" fill="{palette["bg"]}" stroke="{palette["border"]}"/>'
        f'<style>{style}</style>{body}</svg>'
    )


def card(x: int, y: int, width: int, height: int, label: str, value: str, palette: Palette) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="{palette["panel"]}" stroke="{palette["border"]}"/>'
        f'<text x="{x+16}" y="{y+25}" class="label">{escape(label)}</text>'
        f'<text x="{x+16}" y="{y+59}" class="value">{escape(value)}</text>'
    )


def overview(stats: dict[str, Any], theme: str, width: int) -> str:
    palette = PALETTES[theme]
    items = [
        ("PUBLIC REPOSITORIES", stats["public_repositories"]),
        ("STARS RECEIVED", stats["stars"]),
        ("FORKS", stats["forks"]),
        ("FOLLOWERS", stats["followers"]),
        ("CONTRIBUTIONS · 12 MONTHS", stats["contributions"]["total"]),
        ("COMMITS · 12 MONTHS", stats["contributions"]["commits"]),
    ]
    gap, margin, top, height = 14, 20, 54, 76
    columns = 3
    box_width = (width - margin * 2 - gap * (columns - 1)) // columns
    body = '<text x="20" y="30" class="title">GITHUB OVERVIEW</text>'
    for index, (label, value) in enumerate(items):
        x = margin + (index % columns) * (box_width + gap)
        y = top + (index // columns) * (height + gap)
        body += card(x, y, box_width, height, label, f"{value:,}", palette)
    body += f'<text x="20" y="246" class="small">Public data only · Updated {escape(stats["generated_at"][:10])}</text>'
    return svg_document(width, 265, body, palette, "GitHub public profile overview")


def languages_svg(stats: dict[str, Any], theme: str, width: int) -> str:
    palette = PALETTES[theme]
    languages = stats.get("languages", [])
    body = '<text x="20" y="30" class="title">PUBLIC REPOSITORY LANGUAGES</text>'
    if not languages:
        body += '<text x="20" y="75" class="label">No language data available.</text>'
    else:
        colors = ["#3178c6", "#f1e05a", "#3572A5", "#e34c26", "#563d7c", "#00ADD8", "#178600", "#dea584"]
        bar_x, bar_y, bar_width, bar_height = 20, 52, width - 40, 13
        total = sum(item["bytes"] for item in languages) or 1
        cursor = bar_x
        for index, item in enumerate(languages):
            segment = bar_width * item["bytes"] / total
            body += f'<rect x="{cursor:.2f}" y="{bar_y}" width="{segment:.2f}" height="{bar_height}" fill="{colors[index % len(colors)]}"/>'
            cursor += segment
        column_width = (width - 40) / 2
        for index, item in enumerate(languages):
            column, row = index % 2, index // 2
            x, y = 20 + column * column_width, 94 + row * 31
            color = colors[index % len(colors)]
            body += f'<circle cx="{x+5}" cy="{y-4}" r="5" fill="{color}"/>'
            body += f'<text x="{x+17}" y="{y}" class="label">{escape(item["name"])}</text>'
            body += f'<text x="{x+column_width-8}" y="{y}" text-anchor="end" class="label">{item["percentage"]:.1f}%</text>'
    return svg_document(width, 220, body, palette, "Programming language distribution in public repositories")


def contributions_svg(stats: dict[str, Any], theme: str, width: int) -> str:
    palette = PALETTES[theme]
    days = stats.get("contributions", {}).get("days", [])
    body = '<text x="20" y="30" class="title">PUBLIC CONTRIBUTION ACTIVITY · LAST 12 MONTHS</text>'
    if not days:
        body += '<text x="20" y="75" class="label">Contribution calendar is not available.</text>'
    else:
        cell, gap, start_x, start_y = 9, 3, 20, 48
        # GitHub-style calendar: 53 week columns by 7 weekday rows.
        from datetime import date
        first_date = date.fromisoformat(days[0]["date"])
        first_weekday = (first_date.weekday() + 1) % 7  # Sunday = row 0
        for day in days[-365:]:
            day_date = date.fromisoformat(day["date"])
            day_offset = (day_date - first_date).days + first_weekday
            week_column, weekday_row = divmod(day_offset, 7)
            x = start_x + week_column * (cell + gap)
            y = start_y + weekday_row * (cell + gap)
            if x + cell > width - 18:
                continue
            count = int(day.get("contributionCount", 0))
            level = 0 if count == 0 else 1 if count < 3 else 2 if count < 6 else 3 if count < 10 else 4
            body += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{palette["levels"][level]}"><title>{escape(day["date"])}: {count} public contributions</title></rect>'
        contribution = stats["contributions"]
        body += f'<text x="20" y="148" class="label">{contribution["total"]:,} public contributions in the selected period</text>'
        body += f'<text x="20" y="172" class="small">Commits: {contribution["commits"]:,} · Issues: {contribution["issues"]:,} · Pull requests: {contribution["pull_requests"]:,}</text>'
        # body += '<text x="20" y="195" class="small">Each square represents one day. Private contributions are excluded.</text>'
    return svg_document(width, 215, body, palette, "Public GitHub contribution activity")


def generate_all(stats: dict[str, Any], width: int = 920) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    generators = {"overview": overview, "languages": languages_svg, "contributions": contributions_svg}
    for name, generator in generators.items():
        for theme in ("light", "dark"):
            (OUT / f"{name}-{theme}.svg").write_text(generator(stats, theme, width), encoding="utf-8")
