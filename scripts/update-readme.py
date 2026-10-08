#!/usr/bin/env python3
"""
Generates the organization profile README.md by querying the GitHub API
for all repositories, their topics, and contributors.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ORG = "RH-EMEA-LaunchTeam"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "profile", "README.md")

TOPIC_COLORS = {
    # Red Hat products
    "openshift": "EE0000",
    "acs": "EE0000",
    "acm": "EE0000",
    "devspaces": "EE0000",
    "service-mesh": "EE0000",
    "gitops": "EE0000",
    "tekton": "FD495C",
    "pipelines": "FD495C",
    "serverless": "EE0000",
    "quay": "EE0000",
    "ansible": "EE0000",
    "aap": "EE0000",
    "rhel": "CC0000",
    "rhacm": "EE0000",
    "rhacs": "EE0000",
    "oadp": "EE0000",
    "mtv": "EE0000",
    "mta": "EE0000",
    "3scale": "EE0000",
    "amq": "EE0000",
    "fuse": "EE0000",
    "codeready": "EE0000",
    "cost-management": "EE0000",
    "insights": "EE0000",
    "satellite": "EE0000",
    "stackrox": "EE0000",
    "operator": "CC0000",
    # Ecosystem & CNCF
    "kubernetes": "326CE5",
    "argocd": "EF7B4D",
    "istio": "466BB0",
    "helm": "0F1689",
    "containers": "2496ED",
    "podman": "892CA0",
    "multi-cluster": "326CE5",
    # Languages & frameworks
    "java": "F89820",
    "quarkus": "4695EB",
    "spring-boot": "6DB33F",
    "python": "3776AB",
    "go": "00ADD8",
    "nodejs": "339933",
    # Categories
    "security": "E97627",
    "air-gapped": "555555",
    "workshop": "8B5CF6",
    "demo": "10B981",
    "hands-on": "8B5CF6",
    "ai": "FF6F00",
    "machine-learning": "FF6F00",
}

DEFAULT_COLOR = "1A73E8"


def github_api(endpoint):
    """Make an authenticated request to the GitHub API."""
    url = f"https://api.github.com{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Warning: API request failed for {endpoint}: {e}", file=sys.stderr)
        return None


def get_all_repos():
    """Fetch all public repositories in the organization (paginated)."""
    repos = []
    page = 1
    while True:
        data = github_api(
            f"/orgs/{ORG}/repos?per_page=100&page={page}&type=public&sort=full_name"
        )
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_topics(repo_name):
    """Fetch topics for a repository."""
    data = github_api(f"/repos/{ORG}/{repo_name}/topics")
    if data:
        return data.get("names", [])
    return []


def get_contributors(repo_name):
    """Fetch contributors for a repository."""
    data = github_api(f"/repos/{ORG}/{repo_name}/contributors")
    if data and isinstance(data, list):
        return [c for c in data if c.get("type") == "User"]
    return []


def make_badge(topic):
    """Generate a shields.io badge URL for a topic."""
    color = TOPIC_COLORS.get(topic.lower(), DEFAULT_COLOR)
    label = topic.replace("-", "%20")
    return (
        f'<img src="https://img.shields.io/badge/{label}-{color}?style=flat-square" '
        f'alt="{topic}">'
    )


def make_contributor_avatar(contributor):
    """Generate an avatar image link for a contributor."""
    login = contributor["login"]
    avatar = contributor["avatar_url"]
    profile = contributor["html_url"]
    return (
        f'<a href="{profile}" title="{login}">'
        f'<img src="{avatar}&s=40" width="40" height="40" '
        f'style="border-radius:50%" alt="{login}">'
        f"</a>"
    )


def humanize_name(repo_name):
    """Convert a repo-name-like-this into a human-readable title."""
    return repo_name.replace("-", " ").title()


def generate_readme(repos):
    """Generate the full README markdown content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        '<h1 align="center">',
        "  🚀 RH EMEA Launch Team",
        "</h1>",
        "",
        '<p align="center">',
        "  <strong>Workshops, demos, and hands-on labs from the Red Hat EMEA Launch Team</strong>",
        "</p>",
        "",
        '<p align="center">',
        f'  <a href="https://github.com/orgs/{ORG}/repositories">',
        f'    <img src="https://img.shields.io/badge/workshops-{len(repos)}-EE0000?style=for-the-badge&logo=redhat&logoColor=white" alt="Total workshops">',
        "  </a>",
        "</p>",
        "",
        "---",
        "",
        "## 📚 Workshop Catalog",
        "",
    ]

    if not repos:
        lines.append("*No workshops found yet.*")
        lines.append("")
    else:
        lines.append("<table>")
        lines.append("  <thead>")
        lines.append("    <tr>")
        lines.append('      <th align="left">Workshop</th>')
        lines.append('      <th align="left">Topics</th>')
        lines.append('      <th align="center">Contributors</th>')
        lines.append("    </tr>")
        lines.append("  </thead>")
        lines.append("  <tbody>")

        for repo in sorted(repos, key=lambda r: r["name"].lower()):
            name = repo["name"]
            url = repo["html_url"]
            description = repo.get("description") or ""

            topics = get_topics(name)
            contributors = get_contributors(name)

            workshop_cell = f'<a href="{url}"><strong>{humanize_name(name)}</strong></a>'
            if description:
                workshop_cell += f"<br/><sub>{description}</sub>"

            if topics:
                badges_html = " ".join(make_badge(t) for t in topics)
            else:
                badges_html = "<sub><i>No topics set</i></sub>"

            if contributors:
                avatars_html = " ".join(
                    make_contributor_avatar(c) for c in contributors[:10]
                )
            else:
                avatars_html = "<sub><i>—</i></sub>"

            lines.append("    <tr>")
            lines.append(f"      <td>{workshop_cell}</td>")
            lines.append(f"      <td>{badges_html}</td>")
            lines.append(f'      <td align="center">{avatars_html}</td>')
            lines.append("    </tr>")

        lines.append("  </tbody>")
        lines.append("</table>")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "<details>",
            "<summary>ℹ️ How this page works</summary>",
            "",
            "This README is **automatically generated** by a GitHub Actions workflow that runs:",
            "",
            "- **Daily** at 06:00 UTC",
            "- **On every push** to the `main` branch of this repo",
            f"- Whenever a **repository is created, deleted, or made public** in the [{ORG}](https://github.com/{ORG}) organization",
            "",
            "### Adding topics to your workshop",
            "",
            "Topics appear as labels in the table above. To add them to your repo:",
            "",
            "1. Go to your repository on GitHub",
            "2. Click the ⚙️ gear icon next to **About** (top-right of the repo page)",
            '3. Add relevant topics (e.g. `acs`, `acm`, `service-mesh`, `gitops`, `tekton`, `devspaces`, `openshift`)',
            "4. This page will update automatically on the next run",
            "",
            "</details>",
            "",
            f'<sub>Last updated: {now} · <a href="https://github.com/{ORG}/.github/actions">View workflow runs</a></sub>',
            "",
        ]
    )

    return "\n".join(lines)


def main():
    print(f"Fetching repositories for {ORG}...")
    all_repos = get_all_repos()

    workshop_repos = [
        r
        for r in all_repos
        if r["name"] != ".github" and not r.get("archived", False)
    ]

    print(f"Found {len(workshop_repos)} workshop(s)")

    readme_content = generate_readme(workshop_repos)

    output = os.path.abspath(OUTPUT_PATH)
    os.makedirs(os.path.dirname(output), exist_ok=True)

    with open(output, "w") as f:
        f.write(readme_content)

    print(f"README written to {output}")


if __name__ == "__main__":
    main()
