# Architecture

## Current State

Iris has not selected a final implementation stack yet. This document will track
the real architecture as source files are added.

## Initial Structure

```text
src/      Application source files
tests/    Automated tests
docs/     Project documentation and decisions
scripts/  Local maintenance and validation scripts
```

## Architecture Principles

- Keep the first version small and easy to run locally.
- Prefer conventional structure for the chosen stack.
- Separate source code, tests, scripts, and docs.
- Document runtime requirements as soon as they are known.
- Keep configuration explicit and keep secrets out of Git.

## Source Intake Checklist

- Runtime and version identified.
- Package manager identified.
- Install command documented.
- Run command documented.
- Test command documented.
- Build command documented, if applicable.
- Deployment target documented, if known.
