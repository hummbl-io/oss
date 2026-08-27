#!/usr/bin/env python3
"""Gap-7: Enable branch protection on unprotected repos.

Enables branch protection on main for the 20 unprotected repos with:
- allow_force_pushes: false
- allow_deletions: false
- enforce_admins: false (don't lock out admins)
- required_status_checks: null (no CI requirement yet ΓÇö gap-8 will add)
- required_pull_request_reviews: null (no PR review requirement yet)

Mutates GitHub ΓÇö requires operator authorization (gap-7 remediation).
"""
import json
import subprocess
import sys
import time

UNPROTECTED = [
    "CODES", "_between", "agent-identity-kit", "awesome-stdlib",
    "base120-internal", "community-resource-hub-studio", "cyber",
    "delta-agents", "dirty-runtime-agent", "evidence-gate",
    "founder-mode-showcase", "grounding", "hummbl-120-agents",
    "hummbl-content-filter", "hummbl-formalization",
    "hummbl-interaction-control-plane", "lejepa", "search-space-lab",
    "vendor-skill-fleet", "wags",
]

# Branch protection payload ΓÇö minimal: block force-push + deletions
PAYLOAD = json.dumps({
    "allow_force_pushes": False,
    "allow_deletions": False,
    "enforce_admins": False,
    "required_status_checks": None,
    "required_pull_request_reviews": None,
    "restrictions": None,
})


def enable_protection(repo):
    """Enable branch protection on main for a repo."""
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/hummbl-io/{repo}/branches/main/protection",
             "-X", "PUT", "-H", "Accept: application/vnd.github+json",
             "--input", "-"],
            input=PAYLOAD, capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0:
            return {"repo": repo, "result": "protected"}
        else:
            err = r.stderr.strip()[:200]
            return {"repo": repo, "result": "error", "error": err}
    except Exception as e:
        return {"repo": repo, "result": "error", "error": str(e)[:200]}


def main():
    results = []
    for i, repo in enumerate(UNPROTECTED):
        res = enable_protection(repo)
        results.append(res)
        status = "OK" if res["result"] == "protected" else "FAIL"
        print(f"[{i+1}/{len(UNPROTECTED)}] {repo}: {status}", file=sys.stderr)
        if res["result"] != "protected":
            print(f"  error: {res.get('error','')}", file=sys.stderr)
        time.sleep(0.5)  # rate limit courtesy

    success = sum(1 for r in results if r["result"] == "protected")
    failed = sum(1 for r in results if r["result"] != "protected")
    print(f"\nDone: {success} protected, {failed} failed", file=sys.stderr)

    output = {"total": len(results), "success": success, "failed": failed,
              "results": results}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
