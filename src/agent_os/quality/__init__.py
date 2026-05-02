"""Quality flywheel — thin invocations of vendor/agi-1 skills.

Hermes calls these on demand and on a nightly cron:
    /agi-audit    score the day's outputs
    /agi-council  3-agent critique deliberation
    /agi-research Karpathy autoresearch — evolve prompts against assertions
"""
from agent_os.quality.invocations.audit import audit
from agent_os.quality.invocations.council import council
from agent_os.quality.invocations.research import research

__all__ = ["audit", "council", "research"]
__version__ = "0.1.0"
