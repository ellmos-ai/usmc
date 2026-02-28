# -*- coding: utf-8 -*-
"""
USMC - United Shared Memory Client
===================================

Cross-Agent Memory Sharing mit eigener SQLite-DB.

Verwendung (Client):
    from usmc import USMCClient

    client = USMCClient(db_path="usmc_memory.db", agent_id="opus")
    client.add_fact("system", "os", "Windows 11")
    facts = client.get_facts()

Verwendung (High-Level API):
    from usmc import api

    api.init(agent_id="opus")
    api.fact("system", "os", "Windows 11")
    api.note("Aktueller Task")
    print(api.context())

CLI:
    usmc status
    usmc fact system os "Windows 11"
    usmc note "Meine Notiz"
    usmc context
"""

from .client import USMCClient
from . import api

__version__ = "0.1.0"
__all__ = ["USMCClient", "api"]
