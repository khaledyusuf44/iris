"""Shared spiral runner for CLI and validation gate flows."""

from __future__ import annotations

from dataclasses import dataclass

from iris.engine import DistillResult, IrisEngine, PressureResult


@dataclass(frozen=True)
class SpiralRun:
    idea: str
    pressures: list[PressureResult]
    center: DistillResult


def run_spiral(engine: IrisEngine, idea: str, rings: int) -> SpiralRun:
    constraints: list[str] = []
    pressures: list[PressureResult] = []

    for depth in range(1, rings + 1):
        result = engine.pressure(idea, constraints, depth, rings)
        pressures.append(result)
        constraints.append(result.as_constraint())

    center = engine.distill(idea, constraints)
    return SpiralRun(idea=idea, pressures=pressures, center=center)
