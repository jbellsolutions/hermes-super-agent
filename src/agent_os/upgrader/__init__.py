"""Auto-update daemon. 10 nightly streams.

Each stream pulls upstream, runs smoke, promotes if green or quarantines if red.
"""
from agent_os.upgrader.daemon import run_nightly

__all__ = ["run_nightly"]
__version__ = "0.1.0"
