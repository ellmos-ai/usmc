# -*- coding: utf-8 -*-
"""Kein Test darf die echte ~/.usmc/usmc_memory.db oeffnen.

Anlass (S1 Vereinigungsschema): test_lazy_init oeffnete ohne USMC_DB den
Standardpfad; mit USMC_MEMORY_UNION=1 haette die Suite die Live-DB umgestellt.
"""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="usmc-tests-")
os.environ["USMC_DB"] = os.path.join(_TMP, "usmc_memory.db")
