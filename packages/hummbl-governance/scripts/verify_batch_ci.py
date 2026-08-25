#!/usr/bin/env python3
"""Post-execution CI verification for batch PR operations.

After creating/updating PRs in batch, this script:
1. Waits for CI to queue (default 30s)
2. Checks CI status on a sample of PR branches
3. Flags any that show startup_failure
4. Reports summary

Usage:
  python verify_batch_ci.py --title "fix: pin GitHub Actions to commit SHAs for org policy compliance"
  python verify_batch_ci.py --title "..." --sample 10  # Check 10 random PRs
  python verify_batch_ci.py --title "..." --wait 60    # Wait 60s before checking
"""
import argparse
import json
import random
import subprocess
import sys
import time


def get_prs_by_title(title, owner='hummbl-io'):
    """Find open PRs matching title across org."""
    r = subprocess.run(
        ['gh', 'search', 'prs', title,
         '--owner', owner, '--state', 'open', '--limit', '200',
         '--json', 'repository', 'number', 'title'],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        print(f"ERROR: {r.stderr[:200]}")
        return []
    
    try:
        results = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []
    
    prs = []
    for item in results:
        if item.get('title', '') != title:
            continue
        repo = item.get('repository', {}).get('nameWithOwner', '')
        if repo:
            prs.append({'repo': repo, 'number': item['number']})
    return prs


def check_ci_status(repo, number):
    """Check CI status on a PR. Returns (has_startup_failure, has_real_failure, summary)."""
    r = subprocess.run(
        ['gh', 'pr', 'view', str(number), '--repo', repo,
         '--json', 'statusCheckRollup'],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        return None, None, "error checking"
    
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, None, "parse error"
    
    checks = data.get('statusCheckRollup', [])
    startup_failures = 0
    real_failures = 0
    passing = 0
    pending = 0
    
    for check in checks:
        status = check.get('status', 'COMPLETED')
        conclusion = check.get('conclusion', '')
        
        if status == 'COMPLETED':
            if conclusion == 'SUCCESS':
                passing += 1
            elif conclusion == 'STARTUP_FAILURE':
                startup_failures += 1
            elif conclusion in ('FAILURE', 'CANCELLED', 'TIMED_OUT'):
                real_failures += 1
            elif conclusion in ('NEUTRAL', 'SKIPPED'):
                passing += 1
        elif status in ('IN_PROGRESS', 'QUEUED', 'PENDING'):
            pending += 1
    
    summary = f"{passing} passing, {pending} pending"
    if startup_failures > 0:
        summary += f", {startup_failures} startup_failure"
    if real_failures > 0:
        summary += f", {real_failures} real_failure"
    
    return startup_failures > 0, real_failures > 0, summary


def main():
    parser = argparse.ArgumentParser(description='Post-execution CI verification')
    parser.add_argument('--title', type=str, required=True, help='PR title to search for')
    parser.add_argument('--sample', type=int, default=5, help='Number of PRs to sample (default 5)')
    parser.add_argument('--wait', type=int, default=30, help='Seconds to wait before checking (default 30)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("POST-EXECUTION CI VERIFICATION")
    print(f"  Title: {args.title[:60]}...")
    print(f"  Sample: {args.sample} PRs")
    print(f"  Wait: {args.wait}s")
    print("=" * 60)
    
    prs = get_prs_by_title(args.title)
    print(f"\nFound {len(prs)} open PRs matching title")
    
    if not prs:
        print("No PRs to verify.")
        sys.exit(0)
    
    # Sample
    if len(prs) > args.sample:
        sample = random.sample(prs, args.sample)
        print(f"Sampling {args.sample} of {len(prs)} PRs")
    else:
        sample = prs
        print(f"Checking all {len(prs)} PRs")
    
    print(f"\nWaiting {args.wait}s for CI to queue...")
    time.sleep(args.wait)
    
    startup_failure_count = 0
    real_failure_count = 0
    clean_count = 0
    pending_count = 0
    
    for i, pr in enumerate(sample):
        repo = pr['repo']
        number = pr['number']
        
        has_startup, has_real, summary = check_ci_status(repo, number)
        
        if has_startup is None:
            print(f"  [{i+1}/{len(sample)}] {repo}#{number} — ERROR")
            continue
        
        status = "CLEAN"
        if has_startup:
            status = "STARTUP_FAILURE"
            startup_failure_count += 1
        elif has_real:
            status = "REAL_FAILURE"
            real_failure_count += 1
        elif 'pending' in summary:
            status = "PENDING"
            pending_count += 1
        else:
            clean_count += 1
        
        print(f"  [{i+1}/{len(sample)}] {repo}#{number} — {status} ({summary})")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  Sampled:           {len(sample)}")
    print(f"  Clean:             {clean_count}")
    print(f"  Pending:           {pending_count}")
    print(f"  Startup failures:  {startup_failure_count}")
    print(f"  Real failures:     {real_failure_count}")
    
    if startup_failure_count > 0:
        print(f"\n  WARNING: {startup_failure_count} PRs still have startup_failure!")
        print("  The batch fix may be incomplete. Check for missed workflow files.")
        sys.exit(1)
    elif real_failure_count > 0:
        print(f"\n  NOTE: {real_failure_count} PRs have real CI failures (unrelated to SHA-pinning).")
        sys.exit(0)
    else:
        print("\n  RESULT: No startup_failures detected in sample.")
        sys.exit(0)


if __name__ == '__main__':
    main()
