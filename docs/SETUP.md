# GitHub Profile Engineering System — Setup

This project generates profile statistics using GitHub's own REST and GraphQL APIs, then stores the resulting SVG files in the profile repository. It does not use GitHub Readme Stats, Streak Stats, Shields.io, or any third-party statistics API.

## 1. Repository requirement

Use the special public profile repository:

- Owner: `FatihG34`
- Repository: `FatihG34`
- Default branch: `main`
- Repository visibility: public

Copy the project into the repository root, preserving the directory structure.

## 2. Data scope and privacy

The collector uses `GET /users/{username}/repos`, which returns public repositories. It does not call authenticated private-repository listing endpoints and does not request private repository scopes.

The GraphQL query does not request the optional `read:user` scope, and the workflow uses only the repository-scoped `GITHUB_TOKEN`. GitHub documents that contributions from private and internal repositories are included only when the optional `read:user` scope is present. The query also does not request `restrictedContributionsCount`. Private repository names, metadata, languages, commits, and contribution counts are not collected.

`assets/statistics/stats.json` is committed to the public repository and contains public profile statistics and contribution aggregates. If you prefer not to publish a raw JSON snapshot, remove the `stats.json` write from `scripts/generate_profile.py`; SVG cards will continue to work.

## 3. GitHub Actions permissions

The workflow requests only:

```yaml
permissions:
  contents: write
```

This is needed to commit generated assets to the same repository. The built-in `secrets.GITHUB_TOKEN` is used; a manually created PAT is not required for this workflow.

Check `Settings → Actions → General → Workflow permissions` and ensure repository policy permits the workflow-level `contents: write` permission. Do not put tokens in `profile.json`, source code, README, or committed files.

## 4. Enable the workflow

1. Push the project to the `main` branch.
2. Open the repository's **Actions** tab.
3. Select **Update GitHub Profile Statistics**.
4. Select **Run workflow** for the first run.
5. Confirm the six SVG files and `stats.json` are generated under `assets/statistics/`.
6. Open the profile README and verify Light and Dark appearance.

The schedule is `17 3 * * *` (03:17 UTC daily). GitHub may delay scheduled workflows during high-load periods; this is not a strict execution-time guarantee.

## 5. Run locally (optional)

Requires Python 3.10+ and no third-party Python packages.

```bash
export GITHUB_TOKEN="YOUR_TOKEN"
export GITHUB_USERNAME="FatihG34"
python scripts/generate_profile.py
```

For local testing, use a token with access sufficient to read public profile and repository data only. Do not grant private repository access. The built-in Actions token is preferred for scheduled runs.

## 6. Generated files

```text
assets/statistics/
├── overview-light.svg
├── overview-dark.svg
├── languages-light.svg
├── languages-dark.svg
├── contributions-light.svg
├── contributions-dark.svg
└── stats.json
```

The generator also rewrites the README block between the `PROFILE_STATS:START` and `PROFILE_STATS:END` markers, including the `## GitHub Overview` heading. When the public profile exposes no meaningful data (no repositories, stars, forks, followers, contributions, or languages), the whole section is removed from the README instead of showing an empty statistics block; it reappears automatically on the first run that collects data again. Unchanged content produces no diff, so the daily workflow only commits the README when section visibility actually changes.

The README uses GitHub-supported HTML `<picture>` elements and the `prefers-color-scheme` media feature to select the Light or Dark SVG. GitHub documents this responsive-image approach in its profile README guide.

## 7. Metric definitions

- **Public repositories:** non-archived public repositories returned by the user repositories endpoint. Forks are included by default; set `include_forks_in_repository_totals` to `false` to exclude them from totals.
- **Original public repositories:** non-fork, non-archived public repositories.
- **Stars received:** sum of `stargazers_count` across selected public repositories.
- **Forks:** sum of `forks_count` across selected public repositories.
- **Followers / following:** public user profile counters.
- **Languages:** aggregate byte counts from the Languages API for original, non-archived public repositories. Percentages reflect reported source bytes, not time spent coding.
- **Public contributions:** GitHub's contribution collection for the configured rolling period, using the repository-scoped Actions token without the optional `read:user` scope, so private/internal contribution data is not made available to the collector. GitHub's contribution attribution rules apply.

## 8. Rate limits and troubleshooting

The workflow uses an authenticated `GITHUB_TOKEN`. The client handles pagination, retries transient network errors, and backs off on HTTP 403/429 responses. Avoid unnecessary per-repository API calls.

- **GraphQL error:** inspect the GraphQL error in the Actions log and verify the workflow token is present.
- **Permission denied on push:** check Actions workflow permissions and branch protection rules.
- **No SVG updates:** files may be unchanged; inspect the workflow log and `git status`.
- **GitHub Overview section disappeared:** the profile had no public data (all counters zero); it returns automatically once the APIs report data again.
- **Images not visible:** confirm SVGs exist on the default branch and README paths match.
- **Schedule did not run at the exact minute:** scheduled workflows can be delayed; use `workflow_dispatch` to run manually.

## 9. Security checklist

- Keep collection public-data-only.
- Do not add `read:user`, `repo`, or private repository permissions to a PAT.
- Never print token values in workflow logs.
- Keep workflow permissions limited to `contents: write`.
- Review `stats.json` before enabling the workflow if you prefer publishing visual SVGs only.
- Pin third-party GitHub Actions to full commit SHAs if your supply-chain policy requires immutable action references.

## 10. Maintenance

Edit `config/profile.json` to change the username, rolling statistics period, language count, or SVG width. Update the workflow's `GITHUB_USERNAME` value if the account changes.
