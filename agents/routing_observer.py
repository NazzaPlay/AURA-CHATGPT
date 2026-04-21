"""Legacy compatibility wrapper for the canonical Routing Neuron observer."""

from backend.app.routing_neuron.core.observer import (
    build_task_signature,
    infer_neuron_type,
    ingest_routing_observation,
    maybe_birth_candidate_from_pattern,
    observe_routing_pattern,
    record_routing_evidence,
)

__all__ = [
    "build_task_signature",
    "infer_neuron_type",
    "ingest_routing_observation",
    "maybe_birth_candidate_from_pattern",
    "observe_routing_pattern",
    "record_routing_evidence",
]
