# Iris

Iris is the working repository for this project.

The repo is currently in bootstrap mode: core project files are in place, while
the product scope, implementation stack, and source files are still pending.

## Current Status

- Repository initialized on `main`.
- Remote: `https://github.com/khaledyusuf44/iris.git`.
- Source files: pending handoff.
- Project docs: see `docs/`.

## Repo Layout

```text
AGENTS.md                 AI/core contributor operating notes
CONTRIBUTING.md           Human contributor workflow
docs/                     Project planning, roadmap, and architecture notes
scripts/check_repo.sh     Lightweight repository health check
src/                      Application source files, once added
tests/                    Tests, once added
```

## Getting Started

```bash
git clone https://github.com/khaledyusuf44/iris.git
cd iris
./scripts/check_repo.sh
```

## Working Agreements

- Keep `main` clean and working.
- Add source files under `src/` unless the chosen stack requires a different
  conventional layout.
- Add tests under `tests/` or the stack-native test directory.
- Keep secrets out of Git. Use `.env.example` for documented configuration.
- Update `docs/ARCHITECTURE.md` when the project structure or runtime changes.

## Next Inputs Needed

- Product goal and target users.
- Source files or starter template.
- Preferred stack, if already chosen.
- Hosting/deployment target.
- Any API keys or credentials as local environment variables only, never in Git.
