# -*- coding: utf-8 -*-
"""
USMC - United Shared Memory Client
==================================

Cross-agent memory sharing with a local SQLite database.

Client usage:
    from usmc import USMCClient

    client = USMCClient(db_path="usmc_memory.db", agent_id="opus")
    client.add_fact("system", "os", "Windows 11")
    facts = client.get_facts()

High-level API usage:
    from usmc import api

    api.init(agent_id="opus")
    api.fact("system", "os", "Windows 11")
    api.note("Current task")
    print(api.context())

CLI:
    usmc status
    usmc fact system os "Windows 11"
    usmc note "My note"
    usmc context
"""

from .client import USMCClient
from . import api

__version__ = "0.1.0"
__all__ = ["USMCClient", "api"]
