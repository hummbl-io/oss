#!/usr/bin/env python3
"""Gap-7: Fleet-wide branch protection audit.

Enumerates all non-archived hummbl-io repos, checks branch protection
on main, and reports which repos are unprotected or allow force-pushes.

Read-only — no mutations. Outputs JSON for the audit report.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def gh_api(path, timeout=15):
    """Call gh api and return (status_code, json_or_none)."""
    try:
        r = subprocess.run(
            ["gh", "api", path, "--silent"],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0:
            return 200, None
        # 404 = no protection, 403 = no access
        if "404" in r.stderr or "Not Found" in r.stderr:
            return 404, None
        if "403" in r.stderr or "Forbidden" in r.stderr:
            return 403, None
        return r.returncode, None
    except subprocess.TimeoutExpired:
        return -1, None
    except Exception:
        return -2, None


def check_repo(name):
    """Check branch protection status for a repo's main branch."""
    code, _ = gh_api(f"repos/hummbl-io/{name}/branches/main/protection")

    # Also check if main branch exists
    if code == 404:
        # Could be no protection OR no main branch — check branch existence
        bc, _ = gh_api(f"repos/hummbl-io/{name}/branches/main")
        if bc == 404:
            return {"repo": name, "status": "no-main-branch"}
        return {"repo": name, "status": "unprotected"}

    if code == 200:
        # Protected — check force_push setting via detailed query
        try:
            r = subprocess.run(
                ["gh", "api", f"repos/hummbl-io/{name}/branches/main/protection",
                 "--jq", ".allow_force_pushes.enabled"],
                capture_output=True, text=True, timeout=15
            )
            force_push = r.stdout.strip() == "true"
            return {"repo": name, "status": "protected",
                    "force_push_allowed": force_push}
        except Exception:
            return {"repo": name, "status": "protected", "force_push_allowed": "unknown"}

    if code == 403:
        return {"repo": name, "status": "access-denied"}

    return {"repo": name, "status": f"error-{code}"}


def main():
    # Get all non-archived repos
    r = subprocess.run(
        ["gh", "repo", "list", "hummbl-io", "--limit", "500",
         "--json", "name,isArchived",
         "--jq", '[.[] | select(.isArchived==false) | .name]'],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        print(f"ERROR listing repos: {r.stderr}", file=sys.stderr)
        sys.exit(1)

    repos = json.loads(r.stdout)
    print(f"Checking {len(repos)} non-archived repos...", file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(check_repo, name): name for name in repos}
        for i, fut in enumerate(as_completed(futures)):
            res = fut.result()
            results.append(res)
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(repos)}...", file=sys.stderr)

    # Sort by repo name
    results.sort(key=lambda x: x["repo"])

    # Summary
    summary = {}
    for r in results:
        s = r["status"]
        summary[s] = summary.get(s, 0) + 1

    output = {"total": len(results), "summary": summary, "repos": results}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
