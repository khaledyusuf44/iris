# Codex Git Commit Check

Date: 2026-06-08

Purpose: verify that Codex can stage, commit, and push from this repo after
enabling `codex_git_commit = true` in the local Codex config.

Expected check:

```bash
git show -s --format=fuller HEAD
```

The commit metadata should show which author and committer Git used for the
Codex-created commit.
