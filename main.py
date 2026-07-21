"""X Connector extension — entry point with module hot-reload."""
from __future__ import annotations

import sys
import os

_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _dir)

for _m in list(sys.modules):
    if _m in ("app", "api_client", "params", "response_models",
              "handlers_oauth", "handlers_posts", "handlers_reads", "handlers_trends"):
        del sys.modules[_m]

from app import ext, chat  # noqa: E402, F401

import handlers_oauth   # noqa: E402, F401
import handlers_posts   # noqa: E402, F401
import handlers_reads   # noqa: E402, F401
import handlers_trends  # noqa: E402, F401
