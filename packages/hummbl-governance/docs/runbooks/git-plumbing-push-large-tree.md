# Git Plumbing Push for Large Working Trees

## When to use

Use this runbook when a repository's working tree is impractically large to
check out on your current machine (e.g., 840K+ files, millions of objects,
or a long-running feature branch that has diverged significantly). The
standard `git checkout` + edit + `git commit` + `git push` workflow hangs
or takes tens of minutes. This approach uses git plumbing commands to
stage and commit a single file change **without checking out the working
tree**.

## Prerequisites

- `git` installed and authenticated to the remote
- The target repo cloned (or at least `.git` present) — the working tree
  does NOT need to be checked out
- `gh` CLI for creating the PR
- Know the base branch (usually `main`) and your target branch name

## Worked example

**Repo:** `hummbl-io/hummbl-skills`
**Problem:** 840K+ files in the working tree from a long-running feature
branch (`feat/devin/skills-to-1000`). `git checkout main` hangs for 10+
minutes. A single SKILL.md file needs a one-line platform note.
**Commit:** `eeada4c2cd5` (worked example reference)

## Step-by-step

### 1. Create a worktree from the base branch

A git worktree gives you a clean, separate working directory without
disturbing the main clone's working tree. This is the key to avoiding the
large-tree problem.

```powershell
# From the repo root (or anywhere with .git)
git worktree add -b <your-branch> <worktree-path> origin/main
```

Example:
```powershell
cd /path/to/projects/hummbl-skills
git worktree add -b fix/devin/goal-cycle-platform-note-v2 /path/to/projects/hummbl-skills-worktree origin/main
```

This creates a new branch from `origin/main` and checks it out in a
separate directory. The worktree only has the files from `main`, not the
840K files from the feature branch.

### 2. Make your edit in the worktree

```powershell
cd <worktree-path>
# Edit the file(s) you need to change
```

The worktree is a normal working directory — use any editor or tool to
make your changes.

### 3. Commit normally

Because the worktree only has `main`'s files, `git add` and `git commit`
work normally:

```powershell
git add <changed-file>
git commit -m "your commit message"
```

### 4. Push and create PR

```powershell
git push origin <your-branch>
gh pr create --repo <org/repo> --head <your-branch> --base main --title "..." --body "..."
```

### 5. Clean up the worktree

After the PR is created (or merged), remove the worktree:

```powershell
cd <original-repo-root>
git worktree remove <worktree-path>
git branch -d <your-branch>  # only if merged; otherwise skip
```

## Alternative: pure plumbing (no worktree)

If even a worktree is too slow (extremely rare), use raw git plumbing to
stage a single file change without any working tree:

```powershell
# 1. Create a tree from HEAD with one file replaced
git read-tree HEAD
git cat-file -p HEAD:<path/to/file> > /tmp/oldfile  # backup
# ... edit /tmp/oldfile or create new content ...
git hash-object -w /tmp/newfile  # returns <new-blob-sha>
git update-index --cacheinfo 0644 <new-blob-sha> <path/to/file>
TREE_SHA=$(git write-tree)
PARENT=$(git rev-parse HEAD)
COMMIT_SHA=$(git commit-tree $TREE_SHA -p $PARENT -m "your message")
git push origin $COMMIT_SHA:refs/heads/<your-branch>
```

This is the pure plumbing approach — no working tree, no worktree, just
object database manipulation. Use only if the worktree approach also
fails.

## Verification

After pushing, verify the commit is on the remote:

```powershell
git ls-remote origin <your-branch>
# Should show the SHA you pushed
```

Then verify the PR was created:

```powershell
gh pr view <PR-number> --repo <org/repo>
```

## Common pitfalls

- **Wrong branch in worktree**: Always specify `origin/main` (or the
  correct base) when creating the worktree. If you omit it, the worktree
  may inherit the current branch's tree (which could be the 840K-file
  branch you're trying to avoid).
- **Forgetting to push the branch**: `git commit` only creates the commit
  locally. You must `git push origin <branch>` before creating the PR.
- **Worktree not cleaned up**: Worktrees persist until explicitly removed.
  Run `git worktree list` to check for stale worktrees and
  `git worktree remove <path>` to clean them up.
- **Branch already exists**: If `<your-branch>` already exists, use a
  different name or `git worktree add --detach` and then create the branch
  manually.

## See also

- [git-worktree documentation](https://git-scm.com/docs/git-worktree)
- [git-plumbing documentation](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)

---

Origin: 2026-08-18 session — hummbl-skills working tree had 840K+ files
from `feat/devin/skills-to-1000` branch. `git checkout main` hung for
10+ minutes. Worktree approach solved it in seconds. Worked example:
commit `eeada4c2cd5` on branch `fix/devin/goal-cycle-platform-note-v2`,
PR #52 on `hummbl-io/hummbl-skills`.
