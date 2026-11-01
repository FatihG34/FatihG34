"""Collect public-only GitHub profile statistics."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from github_client import GitHubClient

CONTRIBUTIONS_QUERY = """
query PublicProfileContributions($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalRepositoryContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
  }
}
"""


def collect_statistics(client: GitHubClient, username: str, config: dict[str, Any]) -> dict[str, Any]:
    user = client.get(f"/users/{username}")
    # This public-user endpoint returns public repositories only. No private
    # repository listing endpoint or private repository scope is used.
    repos = client.get_paginated(f"/users/{username}/repos?type=owner&sort=updated&per_page=100")
    repos = [repo for repo in repos if not repo.get("archived", False)]
    include_forks = bool(config.get("include_forks_in_repository_totals", True))
    counted_repos = repos if include_forks else [repo for repo in repos if not repo.get("fork")]

    language_bytes: Counter[str] = Counter()
    for repo in repos:
        if repo.get("fork"):
            continue
        for language, byte_count in (client.get(f"/repos/{repo['full_name']}/languages") or {}).items():
            language_bytes[language] += int(byte_count)

    now = datetime.now(timezone.utc)
    period_days = int(config.get("stats_period_days", 365))
    start = now - timedelta(days=period_days - 1)
    data = client.graphql(
        CONTRIBUTIONS_QUERY,
        {
            "login": username,
            "from": start.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z"),
            "to": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        },
    )
    account = data.get("user")
    if not account:
        raise RuntimeError(f"GitHub GraphQL could not find user '{username}'")
    contribution = account["contributionsCollection"]
    calendar = contribution["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    cutoff = (now - timedelta(days=int(config.get("contribution_calendar_days", 365)) - 1)).date().isoformat()
    days = [day for day in days if day["date"] >= cutoff]

    top_languages = [
        {"name": name, "bytes": count}
        for name, count in language_bytes.most_common(int(config.get("language_top_n", 7)))
    ]
    total_bytes = sum(language_bytes.values())
    for language in top_languages:
        language["percentage"] = round(language["bytes"] * 100 / total_bytes, 1) if total_bytes else 0

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "username": username,
        "name": user.get("name") or username,
        "bio": user.get("bio") or "",
        "profile_url": user.get("html_url", f"https://github.com/{username}"),
        "followers": int(user.get("followers", 0)),
        "following": int(user.get("following", 0)),
        "public_repositories": len(counted_repos),
        "original_public_repositories": sum(1 for repo in repos if not repo.get("fork")),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in counted_repos),
        "forks": sum(int(repo.get("forks_count", 0)) for repo in counted_repos),
        "languages": top_languages,
        "contributions": {
            "period_days": period_days,
            "total": int(calendar.get("totalContributions", 0)),
            "commits": int(contribution.get("totalCommitContributions", 0)),
            "issues": int(contribution.get("totalIssueContributions", 0)),
            "pull_requests": int(contribution.get("totalPullRequestContributions", 0)),
            "repositories": int(contribution.get("totalRepositoryContributions", 0)),
            "days": days,
        },
        "visibility": "public-only",
    }
