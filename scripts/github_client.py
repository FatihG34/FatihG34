"""Small, dependency-free GitHub REST and GraphQL client."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

API_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
API_VERSION = "2022-11-28"


class GitHubAPIError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "FatihG34-GitHub-Profile-Stats",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _request(self, url: str, payload: dict[str, Any] | None = None) -> tuple[Any, dict[str, str]]:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = dict(self.headers)
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=body, headers=headers)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    raw = response.read().decode("utf-8")
                    return (json.loads(raw) if raw else None,
                            {k.lower(): v for k, v in response.headers.items()})
            except urllib.error.HTTPError as exc:
                message = exc.read().decode("utf-8", errors="replace")
                if exc.code in (403, 429) and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    reset = exc.headers.get("X-RateLimit-Reset")
                    if retry_after:
                        delay = int(retry_after)
                    elif exc.headers.get("X-RateLimit-Remaining") == "0" and reset:
                        delay = max(1, int(reset) - int(time.time()))
                    else:
                        delay = 60 * (attempt + 1)
                    time.sleep(min(delay, 300))
                    continue
                raise GitHubAPIError(f"GitHub API returned HTTP {exc.code}: {message[:500]}") from exc
            except urllib.error.URLError as exc:
                if attempt == 3:
                    raise GitHubAPIError(f"Could not reach GitHub API: {exc}") from exc
                time.sleep(2 ** attempt)
        raise GitHubAPIError("GitHub API request failed after retries")

    def get(self, path: str) -> Any:
        url = path if path.startswith("https://") else f"{API_ROOT}{path}"
        data, _ = self._request(url)
        return data

    def get_paginated(self, path: str) -> list[Any]:
        results: list[Any] = []
        url = f"{API_ROOT}{path}"
        while url:
            data, headers = self._request(url)
            if not isinstance(data, list):
                raise GitHubAPIError(f"Expected a list from {url}")
            results.extend(data)
            url = ""
            for part in headers.get("link", "").split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1:part.find(">")]
                    break
        return results

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        data, _ = self._request(GRAPHQL_URL, {"query": query, "variables": variables})
        if data.get("errors"):
            raise GitHubAPIError("GraphQL error: " + json.dumps(data["errors"])[:800])
        return data["data"]
