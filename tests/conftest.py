# -*- coding: utf-8 -*-
"""Isolate all database and home-directory paths before package imports."""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="usmc-tests-")
_HOME = os.path.join(_TMP, "home")
_TEMP = os.path.join(_TMP, "tmp")
_APPDATA = os.path.join(_HOME, "AppData", "Roaming")
_LOCALAPPDATA = os.path.join(_HOME, "AppData", "Local")
for _path in (_HOME, _TEMP, _APPDATA, _LOCALAPPDATA):
    os.makedirs(_path, exist_ok=True)

# Path.home() uses USERPROFILE on Windows and HOME on POSIX.
os.environ["USERPROFILE"] = _HOME
os.environ["HOME"] = _HOME
os.environ["APPDATA"] = _APPDATA
os.environ["LOCALAPPDATA"] = _LOCALAPPDATA
os.environ["TMP"] = _TEMP
os.environ["TEMP"] = _TEMP
os.environ["XDG_DATA_HOME"] = os.path.join(_HOME, ".local", "share")
os.environ["XDG_CONFIG_HOME"] = os.path.join(_HOME, ".config")
os.environ["USMC_DB"] = os.path.join(_TEMP, "usmc_memory.db")
os.environ["USMC_MEMORY_UNION"] = ""
