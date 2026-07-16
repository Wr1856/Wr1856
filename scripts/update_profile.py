#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PROJECTS_FILE = ROOT / "projects.json"
PROFILE = ROOT / "profile"
PROFILE.mkdir(exist_ok=True)

BG = "#0A0E16"
GOLD = "#D6C48B"
TEXT = "#E7E0D0"
MUTED = "#AAB5C8"


def github_json(url: str) -> Any:
    token = os.getenv("GITHUB_TOKEN", "")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "wm-profile-generator",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def metric_svg(label: str, value: str, width: int = 202) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="30" viewBox="0 0 {width} 30" role="img" aria-label="{esc(label)}: {esc(value)}">
  <rect width="{width}" height="30" rx="4" fill="{BG}"/>
  <rect x="1" y="1" width="{width-2}" height="28" rx="3" fill="none" stroke="{GOLD}" stroke-opacity=".28"/>
  <path d="M11 19L14 10L20 16L25 8L30 16L36 10L39 19Z" fill="none" stroke="{GOLD}" stroke-width="1.3"/>
  <text x="48" y="19.5" fill="{MUTED}" font-family="Arial, sans-serif" font-size="10" font-weight="700">{esc(label)}</text>
  <text x="{width-12}" y="19.5" text-anchor="end" fill="{TEXT}" font-family="Arial, sans-serif" font-size="11" font-weight="700">{esc(value)}</text>
</svg>"""


def activity_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="202" height="30" viewBox="0 0 202 30" role="img" aria-label="Abrir estatísticas do GitHub">
  <rect width="202" height="30" rx="4" fill="{BG}"/>
  <rect x="1" y="1" width="200" height="28" rx="3" fill="none" stroke="{GOLD}" stroke-opacity=".28"/>
  <path d="M12 20V14M18 20V10M24 20V6M30 20V12" stroke="{GOLD}" stroke-width="1.5"/>
  <text x="43" y="19.5" fill="{MUTED}" font-family="Arial, sans-serif" font-size="10" font-weight="700">ESTATÍSTICAS</text>
  <text x="190" y="19.5" text-anchor="end" fill="{TEXT}" font-family="Arial, sans-serif" font-size="11" font-weight="700">ABRIR</text>
</svg>"""


def overview_svg(stats: dict[str, int]) -> str:
    labels = [
        ("REPOSITÓRIOS", stats["repos"]),
        ("SEGUIDORES", stats["followers"]),
        ("ESTRELAS", stats["stars"]),
        ("FORKS", stats["forks"]),
    ]
    positions = [105, 295, 485, 675]
    columns = []
    for x, (label, value) in zip(positions, labels):
        columns.append(
            f'<text x="{x}" y="69" text-anchor="middle" fill="{GOLD}" font-family="Georgia, serif" font-size="27">{value}</text>'
            f'<text x="{x}" y="95" text-anchor="middle" fill="{MUTED}" font-family="Arial, sans-serif" font-size="10" font-weight="700" letter-spacing="1">{label}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="780" height="126" viewBox="0 0 780 126" role="img">
  <rect x="1" y="1" width="778" height="124" rx="10" fill="{BG}" stroke="{GOLD}" stroke-opacity=".24"/>
  <path d="M20 20H80M20 20V50M760 76V106H700" fill="none" stroke="{GOLD}" stroke-opacity=".16"/>
  <text x="28" y="31" fill="{MUTED}" font-family="Arial, sans-serif" font-size="10" font-weight="700" letter-spacing="1.3">ATIVIDADE PÚBLICA / PUBLIC ACTIVITY</text>
  {''.join(columns)}
</svg>"""


def fetch_stats(owner: str) -> dict[str, int]:
    user = github_json(f"https://api.github.com/users/{owner}")
    repos = []
    page = 1
    while True:
        batch = github_json(f"https://api.github.com/users/{owner}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    own = [repo for repo in repos if not repo.get("fork", False)]
    return {
        "followers": int(user.get("followers", 0)),
        "repos": int(user.get("public_repos", len(repos))),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in own),
        "forks": sum(int(repo.get("forks_count", 0)) for repo in own),
    }


def render_project(project: dict[str, Any], owner: str) -> str:
    repo_url = f"https://github.com/{owner}/{project['repository']}"
    stack = " · ".join(f"`{item}`" for item in project.get("stack", []))
    bullets = [f"  - {item}" for item in project.get("highlights_pt", [])]
    bullets += [f"  - {item}" for item in project.get("highlights_en", [])]

    links = [f"[Repositório / Repository]({repo_url})"]
    if project.get("demo"):
        links.append(f"[Demonstração / Live demo]({project['demo']})")

    return f"""<details>
  <summary><strong>♛ {project['title']}</strong> — {project['summary_pt']} / {project['summary_en']}</summary>

  <br />

  **PT-BR**

  {project['description_pt']}

  **EN**

  {project['description_en']}

  **Stack**

  {stack}

  **Destaques / Highlights**

{chr(10).join(bullets)}

  **Links**

  {' · '.join(links)}

</details>"""


def update_projects() -> None:
    config = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    owner = config.get("owner", "Wr1856")
    generated = "\n\n<br />\n\n".join(
        render_project(project, owner) for project in config["projects"]
    )

    readme = README.read_text(encoding="utf-8")
    pattern = re.compile(r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->", re.DOTALL)
    replacement = f"<!-- PROJECTS:START -->\n{generated}\n<!-- PROJECTS:END -->"
    updated, count = pattern.subn(replacement, readme)
    if count != 1:
        raise RuntimeError("Marcadores PROJECTS não foram encontrados.")
    README.write_text(updated, encoding="utf-8")


def main() -> None:
    config = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    owner = config.get("owner", "Wr1856")

    try:
        stats = fetch_stats(owner)
    except Exception as exc:
        print(f"Aviso: falha ao consultar GitHub: {exc}")
        stats = {"followers": 0, "repos": 0, "stars": 0, "forks": 0}

    (PROFILE / "followers.svg").write_text(metric_svg("SEGUIDORES", str(stats["followers"])), encoding="utf-8")
    (PROFILE / "repositories.svg").write_text(metric_svg("REPOSITÓRIOS", str(stats["repos"])), encoding="utf-8")
    (PROFILE / "activity.svg").write_text(activity_svg(), encoding="utf-8")
    (PROFILE / "overview.svg").write_text(overview_svg(stats), encoding="utf-8")
    update_projects()


if __name__ == "__main__":
    main()
