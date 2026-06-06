# Contributing to Iris

Thanks for helping build Iris. This repo is still early, so the contribution
process is intentionally lightweight.

## Setup

```bash
git clone https://github.com/khaledyusuf44/iris.git
cd iris
./scripts/check_repo.sh
```

## Branches

- `main` should stay clean and working.
- Use focused branches for larger changes, such as `codex/bootstrap-docs` or
  `feature/app-shell`.
- Keep commits small enough to review.

## Quality Checks

Run this before committing:

```bash
./scripts/check_repo.sh
```

After the source stack is added, this section should include the real formatter,
linter, test, and build commands.

## Codex Contributions

Codex is the core AI contributor for this project. Substantive Codex work should
also update `docs/CODEX_LOG.md` so the repo keeps a readable build and validation
history alongside Git commits.

## Source File Handoff

When adding starter files or copied project files:

- Say whether the files are new, replacements, or partial references.
- Include any required runtime version and package manager.
- Include expected run and build commands.
- Do not commit secrets, tokens, private keys, or production credentials.

## Pull Requests

Include:

- What changed.
- How it was tested.
- Any follow-up decisions needed.
