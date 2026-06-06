# AGENTS.md

Instructions for Codex and other AI contributors working on Iris.

## Operating Mode

- Read the relevant files before editing.
- Keep changes scoped to the request and the current project phase.
- Do not overwrite user changes or unrelated work.
- Prefer existing project patterns once source files are added.
- Use ASCII text unless a file already uses another character set.
- Run `./scripts/check_repo.sh` before committing.
- When a real tech stack exists, also run the stack-specific formatter, linter,
  and tests.

## Project Context

- Project name: Iris.
- Repository owner: `khaledyusuf44`.
- Core AI contributor: Codex.
- Current phase: Day 1 constraint-engine validation.
- Implementation stack: Python validation engine now; Gradio UI later.
- Source files: `iris/` package. Local task prompts stay untracked.

## Expected Workflow

1. Check `git status --short --branch`.
2. Read `README.md`, `CONTRIBUTING.md`, and relevant files in `docs/`.
3. Make the smallest useful change that moves the project forward.
4. Add or update tests when behavior changes.
5. Update `docs/CODEX_LOG.md` for substantive work.
6. Run repository checks.
7. Commit only intentional files.

## Codex Logging

For each substantive Codex change, add a short entry to `docs/CODEX_LOG.md` with:

- Date.
- Commit hash, once available.
- What changed.
- Validation or test result.
- Whether the Iris quality gate passed or failed.

Do not put secrets, private prompts, local-only handoff notes, or raw API keys in
the Codex log.

## Source File Intake

When source files arrive:

- Identify the framework, package manager, runtime, and build commands.
- Move files into the stack's normal structure.
- Add install, run, test, and build commands to `README.md`.
- Update `docs/ARCHITECTURE.md` with the actual modules and data flow.
- Add CI around real project checks.
- Keep secrets in local environment files, not committed files.

## Iris Product Rule

The model applies pressure; it does not solve the user's idea. Any output that
becomes a finished idea, plan, or generic advice is a product bug.

## Commit Style

Use short imperative commit messages, for example:

```text
Bootstrap project structure
Add initial app shell
Wire API client tests
```
