"""
GitHub Research Scraper
========================
Search GitHub for repos, code, users, and topics.
Saves results to organised folders.

Usage:
  python scraper.py --search "polymarket trading bot"
  python scraper.py --search "crypto arbitrage python" --type code
  python scraper.py --search "prediction market" --type repos --limit 50
  python scraper.py --search "kalshi bot" --save

Types:
  repos  — search repositories (default)
  code   — search code files
  users  — search user profiles
"""
import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")   # optional — add to .env for higher rate limits
BASE_URL      = "https://api.github.com"
RESULTS_DIR   = Path(__file__).parent / "results"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# ── API helpers ───────────────────────────────────────────────────────

def _get(endpoint: str, params: dict = None) -> dict:
    url  = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if resp.status_code == 403:
        reset = resp.headers.get("X-RateLimit-Reset", "")
        print(f"  Rate limited. Add GITHUB_TOKEN to .env for more requests. Reset: {reset}")
        sys.exit(1)
    if resp.status_code == 422:
        print(f"  Bad query: {resp.json().get('message', '')}")
        return {}
    resp.raise_for_status()
    return resp.json()


def _rate_limit_info():
    data      = _get("/rate_limit")
    core      = data.get("resources", {}).get("search", {})
    remaining = core.get("remaining", "?")
    limit     = core.get("limit", "?")
    reset_ts  = core.get("reset", 0)
    reset_dt  = datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S") if reset_ts else "?"
    return f"{remaining}/{limit} requests left (resets {reset_dt})"


# ── Search functions ──────────────────────────────────────────────────

def search_repos(query: str, limit: int = 30, sort: str = "stars") -> list:
    """Search GitHub repositories."""
    print(f"\n🔍 Searching repos: '{query}' (top {limit} by {sort})\n")
    results = []
    page    = 1
    per_page = min(limit, 30)

    while len(results) < limit:
        data = _get("/search/repositories", {
            "q":        query,
            "sort":     sort,
            "order":    "desc",
            "per_page": per_page,
            "page":     page,
        })
        items = data.get("items", [])
        if not items:
            break

        for repo in items:
            results.append({
                "name":        repo["full_name"],
                "url":         repo["html_url"],
                "description": repo.get("description") or "",
                "stars":       repo["stargazers_count"],
                "forks":       repo["forks_count"],
                "language":    repo.get("language") or "Unknown",
                "updated":     repo["updated_at"][:10],
                "topics":      repo.get("topics", []),
                "license":     (repo.get("license") or {}).get("name", ""),
            })
            if len(results) >= limit:
                break

        page += 1
        if len(items) < per_page:
            break
        time.sleep(0.5)

    return results


def search_code(query: str, limit: int = 30) -> list:
    """Search GitHub code files."""
    print(f"\n🔍 Searching code: '{query}' (top {limit})\n")
    results = []
    page    = 1
    per_page = min(limit, 30)

    while len(results) < limit:
        data = _get("/search/code", {
            "q":        query,
            "per_page": per_page,
            "page":     page,
        })
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            results.append({
                "file":       item["name"],
                "path":       item["path"],
                "repo":       item["repository"]["full_name"],
                "repo_url":   item["repository"]["html_url"],
                "file_url":   item["html_url"],
                "raw_url":    item.get("url", ""),
            })
            if len(results) >= limit:
                break

        page += 1
        if len(items) < per_page:
            break
        time.sleep(1)  # code search is stricter on rate limits

    return results


def search_users(query: str, limit: int = 20) -> list:
    """Search GitHub users/orgs."""
    print(f"\n🔍 Searching users: '{query}' (top {limit})\n")
    results = []
    data    = _get("/search/users", {
        "q":        query,
        "sort":     "followers",
        "order":    "desc",
        "per_page": min(limit, 30),
    })
    for user in data.get("items", [])[:limit]:
        profile = _get(f"/users/{user['login']}")
        results.append({
            "username":   user["login"],
            "url":        user["html_url"],
            "type":       user["type"],
            "name":       profile.get("name") or "",
            "bio":        profile.get("bio") or "",
            "followers":  profile.get("followers", 0),
            "repos":      profile.get("public_repos", 0),
            "location":   profile.get("location") or "",
        })
        time.sleep(0.3)
    return results


def get_repo_readme(full_name: str) -> str:
    """Fetch README content for a repo."""
    try:
        import base64
        data    = _get(f"/repos/{full_name}/readme")
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")[:3000]
    except Exception:
        return ""


# ── Display ───────────────────────────────────────────────────────────

def print_repos(results: list):
    print(f"{'#':<4} {'Repo':<45} {'⭐':>6} {'Lang':<12} {'Updated':<12} Description")
    print("─" * 110)
    for i, r in enumerate(results, 1):
        desc = r["description"][:50] if r["description"] else ""
        lang = r["language"][:10]
        print(f"{i:<4} {r['name']:<45} {r['stars']:>6} {lang:<12} {r['updated']:<12} {desc}")


def print_code(results: list):
    print(f"{'#':<4} {'File':<30} {'Repo':<40} Path")
    print("─" * 100)
    for i, r in enumerate(results, 1):
        print(f"{i:<4} {r['file']:<30} {r['repo']:<40} {r['path'][:40]}")
        print(f"     → {r['file_url']}")


def print_users(results: list):
    print(f"{'#':<4} {'Username':<25} {'Followers':>10} {'Repos':>6} {'Name':<25} Bio")
    print("─" * 100)
    for i, r in enumerate(results, 1):
        bio = r["bio"][:40] if r["bio"] else ""
        print(f"{i:<4} {r['username']:<25} {r['followers']:>10} {r['repos']:>6} {r['name']:<25} {bio}")


# ── Save ──────────────────────────────────────────────────────────────

def save_results(query: str, search_type: str, results: list):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    slug      = query.replace(" ", "_").replace("/", "-")[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base      = RESULTS_DIR / f"{search_type}_{slug}_{timestamp}"

    # Always save JSON
    json_file = Path(str(base) + ".json")
    output = {
        "query":       query,
        "type":        search_type,
        "count":       len(results),
        "searched_at": datetime.now().isoformat(),
        "results":     results,
    }
    json_file.write_text(json.dumps(output, indent=2))

    # Always save human-readable .txt
    txt_file = Path(str(base) + ".txt")
    lines = [
        f"GitHub Search Results",
        f"=====================",
        f"Query:   {query}",
        f"Type:    {search_type}",
        f"Found:   {len(results)}",
        f"Date:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
    ]
    for i, r in enumerate(results, 1):
        if search_type == "repos":
            lines += [
                f"#{i} {r['name']}",
                f"   URL:     {r['url']}",
                f"   Stars:   {r['stars']}  Forks: {r['forks']}  Lang: {r['language']}",
                f"   Updated: {r['updated']}",
                f"   Desc:    {r['description']}",
                f"   Topics:  {', '.join(r['topics']) if r['topics'] else 'none'}",
                f"",
            ]
        elif search_type == "code":
            lines += [
                f"#{i} {r['file']} — {r['repo']}",
                f"   Path:    {r['path']}",
                f"   URL:     {r['file_url']}",
                f"",
            ]
        elif search_type == "users":
            lines += [
                f"#{i} @{r['username']} — {r['name']}",
                f"   URL:       {r['url']}",
                f"   Followers: {r['followers']}  Repos: {r['repos']}",
                f"   Bio:       {r['bio']}",
                f"",
            ]
    txt_file.write_text("\n".join(lines))

    print(f"\n📁 Results saved to folder: {RESULTS_DIR}")
    print(f"   JSON: {json_file.name}")
    print(f"   TXT:  {txt_file.name}")
    return json_file


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GitHub Research Scraper")
    parser.add_argument("--search", "-s", required=True,  help="Search query")
    parser.add_argument("--type",   "-t", default="repos",
                        choices=["repos", "code", "users"],
                        help="What to search (default: repos)")
    parser.add_argument("--limit",  "-l", type=int, default=30, help="Max results")
    parser.add_argument("--sort",         default="stars",
                        choices=["stars", "forks", "updated", "best-match"],
                        help="Sort order for repos (default: stars)")
    parser.add_argument("--save",   "-o", action="store_true", help="(always saves automatically)")
    parser.add_argument("--readme", "-r", action="store_true",
                        help="Fetch README for top 3 repos (repos only)")
    parser.add_argument("--rate",         action="store_true", help="Show rate limit info")
    args = parser.parse_args()

    if args.rate:
        print(f"Rate limit: {_rate_limit_info()}")
        return

    if args.type == "repos":
        results = search_repos(args.search, args.limit, args.sort)
        print_repos(results)

        if args.readme and results:
            print("\n\n── READMEs (top 3) ──────────────────────────────────\n")
            for repo in results[:3]:
                readme = get_repo_readme(repo["name"])
                if readme:
                    print(f"\n{'='*60}")
                    print(f"  {repo['name']}")
                    print(f"{'='*60}")
                    print(readme[:1500])

    elif args.type == "code":
        results = search_code(args.search, args.limit)
        print_code(results)

    elif args.type == "users":
        results = search_users(args.search, args.limit)
        print_users(results)

    else:
        results = []

    print(f"\n✅ Found {len(results)} results | {_rate_limit_info()}")

    # Always save — no flag needed
    save_results(args.search, args.type, results)


if __name__ == "__main__":
    main()
