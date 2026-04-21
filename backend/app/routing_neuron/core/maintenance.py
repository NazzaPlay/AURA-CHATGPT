"""Canonical maintenance facade for Routing Neuron V1.x.

This module keeps the canonical namespace stable while maintenance logic still
rides on the legacy `agents.routing_maintenance` backplane.
"""

from agents.routing_maintenance import *  # noqa: F401,F403
