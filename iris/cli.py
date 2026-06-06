"""Command-line validation harness for Iris."""

from __future__ import annotations

import argparse
import sys

from iris.engine import IrisEngine
from iris.errors import IrisError


DEFAULT_IDEAS = [
    "An app that reminds elderly people to take their medication.",
    "A marketplace for renting tools between neighbors.",
    "A study tool that turns lecture notes into flashcards.",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Iris constraint spiral on one or more ideas."
    )
    parser.add_argument(
        "ideas",
        nargs="*",
        help="Idea(s) to validate. If omitted, use the seeded Day 1 ideas.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the seeded Day 1 validation ideas.",
    )
    parser.add_argument(
        "--rings",
        type=int,
        default=4,
        help="Number of pressure rings before the center distillation.",
    )
    args = parser.parse_args(argv)

    if args.rings < 1:
        parser.error("--rings must be at least 1")

    ideas = DEFAULT_IDEAS if args.all or not args.ideas else args.ideas
    engine = IrisEngine()

    for index, idea in enumerate(ideas, start=1):
        print_spiral_header(index, len(ideas), idea)
        try:
            run_spiral(engine, idea, args.rings)
        except IrisError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    return 0


def run_spiral(engine: IrisEngine, idea: str, rings: int) -> None:
    constraints: list[str] = []

    for depth in range(1, rings + 1):
        result = engine.pressure(idea, constraints, depth, rings)
        constraints.append(result.as_constraint())
        print(f"Ring {depth}/{rings}")
        print(f"Pressure: {result.pressure}")
        print(f"Why it bites: {result.why_it_bites}")
        print()

    center = engine.distill(idea, constraints)
    print("Center")
    print(f"Next step: {center.next_step}")
    print()


def print_spiral_header(index: int, total: int, idea: str) -> None:
    print("=" * 72)
    print(f"Spiral {index}/{total}")
    print(f"Idea: {idea}")
    print("=" * 72)


if __name__ == "__main__":
    raise SystemExit(main())
