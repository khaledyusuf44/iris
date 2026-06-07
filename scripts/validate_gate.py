#!/usr/bin/env python3
"""Run Iris seed spirals and print automated gate scores."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from iris.cli import print_spiral, print_spiral_header
from iris.engine import IrisEngine
from iris.errors import IrisError
from iris.gate import GateReport, score_spiral
from iris.seeds import DEFAULT_IDEAS
from iris.spiral import run_spiral


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Iris spirals and score the Day 1 validation gate."
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
    reports: list[GateReport] = []

    for index, idea in enumerate(ideas, start=1):
        print_spiral_header(index, len(ideas), idea)
        try:
            spiral = run_spiral(engine, idea, args.rings)
        except IrisError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        print_spiral(spiral)
        report = score_spiral(spiral)
        reports.append(report)
        print_gate_report(report)

    passed = sum(1 for report in reports if report.ok)
    print("=" * 72)
    status = "PASS" if passed == len(reports) else "FAIL"
    print(f"Overall gate: {status} ({passed}/{len(reports)} spirals passed)")
    return 0 if passed == len(reports) else 2


def print_gate_report(report: GateReport) -> None:
    status = "PASS" if report.ok else "FAIL"
    print("Gate")
    print(f"Result: {status} ({report.passed}/{report.total} criteria passed)")
    for criterion in report.criteria:
        criterion_status = "PASS" if criterion.ok else "FAIL"
        print(
            f"- {criterion.name}: {criterion_status} "
            f"({criterion.passed}/{criterion.total}) - {criterion.detail}"
        )
    print()


if __name__ == "__main__":
    raise SystemExit(main())
