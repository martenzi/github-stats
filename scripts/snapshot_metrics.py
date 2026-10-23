#!/usr/bin/env python3
"""Append daily account + repo metrics to CSVs on the data branch.

Captures what GHRS doesn't: followers, subscribers (real "watching"),
release asset download counts, open issues, stars/forks counters —
enough to derive unstar events and adoption over time.
"""
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OWNER = "martenzi"
REPOS = ["ChatVault", "chat2md", "obsidian-text-extractor", "elixira", "openclaw"]
OUT = Path("metrics")


def api(path):
    # gh is preinstalled on GitHub-hosted runners and handles auth + TLS
    # via GH_TOKEN / its own keyring.
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def append(path, fieldnames, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if new:
            w.writeheader()
        w.writerow(row)


ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

user = api(f"/users/{OWNER}")
total_stars = 0
for repo in REPOS:
    d = api(f"/repos/{OWNER}/{repo}")
    downloads = sum(
        a["download_count"]
        for rel in api(f"/repos/{OWNER}/{repo}/releases?per_page=100")
        for a in rel["assets"]
    )
    total_stars += d["stargazers_count"]
    append(
        OUT / "repos.csv",
        ["timestamp", "repo", "stars", "forks", "subscribers", "open_issues", "release_downloads"],
        {
            "timestamp": ts,
            "repo": repo,
            "stars": d["stargazers_count"],
            "forks": d["forks_count"],
            "subscribers": d["subscribers_count"],
            "open_issues": d["open_issues_count"],
            "release_downloads": downloads,
        },
    )

append(
    OUT / "profile.csv",
    ["timestamp", "followers", "following", "public_repos", "total_stars"],
    {
        "timestamp": ts,
        "followers": user["followers"],
        "following": user["following"],
        "public_repos": user["public_repos"],
        "total_stars": total_stars,
    },
)
print(f"snapshot written for {ts}")
