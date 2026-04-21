"""Canonical registry facade for Routing Neuron V1.x.

This module is the canonical import path for registry operations, even while the
data backplane still lives in the legacy `agents.routing_neuron_registry`
implementation for compatibility.
"""

from agents.routing_neuron_registry import *  # noqa: F401,F403
