"""Promotion ladder helpers for Routing Neuron V1."""

from __future__ import annotations

from dataclasses import dataclass

from .registry import PROMOTION_STAGES, RoutingNeuronCandidate


@dataclass(frozen=True)
class PromotionPath:
    current_stage: str
    next_stage: str | None
    first_strong_promotion: str
    reversible_default: bool


def resolve_next_promotion_stage(current_stage: str) -> str | None:
    try:
        index = PROMOTION_STAGES.index(current_stage)
    except ValueError:
        return PROMOTION_STAGES[0]

    if index >= len(PROMOTION_STAGES) - 1:
        return None

    return PROMOTION_STAGES[index + 1]


def describe_promotion_path(candidate: RoutingNeuronCandidate) -> PromotionPath:
    return PromotionPath(
        current_stage=candidate.promotion_stage,
        next_stage=resolve_next_promotion_stage(candidate.promotion_stage),
        first_strong_promotion=PROMOTION_STAGES[0],
        reversible_default=PROMOTION_STAGES[0] == "specialized_prompt",
    )
