# Codex Authorship Check

Date: 2026-06-08

Purpose: verify that a repo commit can be authored and committed as Codex so
GitHub shows Codex in the commit metadata.

This commit intentionally uses:

```text
Author: Codex <codex@iris.local>
Commit: Codex <codex@iris.local>
```

Note: GitHub links commits to profiles only when the commit email belongs to a
GitHub account. This local Codex identity is visible as metadata but is not a
clickable GitHub profile unless Khalid creates or provides a GitHub bot identity
for it.
