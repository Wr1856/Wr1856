#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "profile" / "overview.svg"
USERNAME = "Wr1856"

BG = "#0A0E16"
GOLD = "#D6C48B"
TEXT = "#E7E0D0"
MUTED = "#AAB5C8"


def github_json(url: str) -> Any:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "wm-profile-metrics",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch_stats() -> dict[str, int]:
    user = github_json(f"https://api.github.com/users/{USERNAME}")
    repos: list[dict[str, Any]] = []
    page = 1

    while True:
        batch = github_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=owner"
        )
        if not batch:
            break

        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    authored = [repo for repo in repos if not repo.get("fork", False)]

    return {
        "repositorios": int(user.get("public_repos", len(repos))),
        "seguidores": int(user.get("followers", 0)),
        "estrelas": sum(int(repo.get("stargazers_count", 0)) for repo in authored),
        "forks": sum(int(repo.get("forks_count", 0)) for repo in authored),
    }


def build_svg(stats: dict[str, int]) -> str:
    values = [
        ("REPOSITÓRIOS", stats["repositorios"]),
        ("SEGUIDORES", stats["seguidores"]),
        ("ESTRELAS", stats["estrelas"]),
        ("FORKS", stats["forks"]),
    ]
    positions = [105, 295, 485, 675]
    columns = []

    for x, (label, value) in zip(positions, values):
        columns.append(
            f'<text x="{x}" y="72" text-anchor="middle" '
            f'fill="{GOLD}" font-family="Georgia, serif" '
            f'font-size="29">{value}</text>'
            f'<text x="{x}" y="98" text-anchor="middle" '
            f'fill="{MUTED}" font-family="Arial, sans-serif" '
            f'font-size="10" font-weight="700" '
            f'letter-spacing="1">{label}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
  width="780" height="128" viewBox="0 0 780 128"
  role="img" aria-label="Resumo da atividade pública no GitHub">

  <rect x="1" y="1" width="778" height="126" rx="10"
    fill="{BG}" stroke="{GOLD}" stroke-opacity=".24"/>

  <path d="M20 20H80M20 20V49M760 79V108H700"
    fill="none" stroke="{GOLD}" stroke-opacity=".16"/>

  <text x="28" y="31"
    fill="{MUTED}" font-family="Arial, sans-serif"
    font-size="10" font-weight="700" letter-spacing="1.3">
    RESUMO DA ATIVIDADE PÚBLICA
  </text>

  {''.join(columns)}
</svg>"""


def main() -> None:
    stats = fetch_stats()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(stats), encoding="utf-8")


if __name__ == "__main__":
    main()
