"""Retell AI phone + Instantly.ai email channel runtime.

Both outbound channels share one COO Specialist brain. The dispatch branch
is selected by job tag:

  phone / outbound-phone  → Retell AI API (POST /v2/calls)
  email / outbound-email  → Instantly.ai API (POST /api/v1/lead/add + campaign trigger)

Tier 3 hard-stop (explicit YES required) is enforced by tier_classifier
before this module is ever reached — no re-check needed here.

Usage (from job_router):
    from agent_os.runtimes.retell_channel import invoke
    result = await invoke.run(job)
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any

import httpx

from agent_os.orchestrator.adapters.job_router import Job
from agent_os.bus.nats_publisher import publish_event

logger = logging.getLogger(__name__)

_RETELL_API_KEY = os.getenv("RETELL_API_KEY", "")
_RETELL_AGENT_ID = os.getenv("RETELL_AGENT_ID", "")
_RETELL_BASE_URL = "https://api.retellai.com"

_INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY", "")
_INSTANTLY_BASE_URL = "https://api.instantly.ai/api/v1"


async def run(job: Job) -> dict[str, Any]:
    """Route job to Retell AI (phone) or Instantly.ai (email)."""
    task_id = str(uuid.uuid4())
    t0 = time.monotonic()
    tags = {tag.lower() for tag in job.tags}

    publish_event("agents.coo-specialist.task.started", {
        "task_id": task_id,
        "prompt": job.prompt[:200],
        "runtime": "retell_channel",
        "tags": list(tags),
    })

    if tags & {"phone", "outbound-phone", "retell"}:
        result = await _retell_call(job, task_id, t0)
    elif tags & {"email", "outbound-email", "instantly"}:
        result = await _instantly_email(job, task_id, t0)
    else:
        result = _error_result(
            task_id,
            f"retell_channel: no matching channel for tags {tags!r}. "
            "Use 'phone'/'outbound-phone' or 'email'/'outbound-email'.",
            t0,
        )

    event = "agents.coo-specialist.task.completed" if result["status"] == "completed" \
        else "agents.coo-specialist.task.failed"
    publish_event(event, {
        "task_id": task_id,
        "elapsed_seconds": result["elapsed_seconds"],
        "channel": result.get("channel", "unknown"),
    })

    return result


# ---------------------------------------------------------------------------
# Retell AI — phone channel
# ---------------------------------------------------------------------------

async def _retell_call(job: Job, task_id: str, t0: float) -> dict[str, Any]:
    """Initiate an outbound call via Retell AI.

    Retell accepts a `retell_llm_dynamic_variables` dict so we can inject
    the COO Specialist's prompt as context without modifying the deployed
    Retell agent config.
    """
    if not _RETELL_API_KEY:
        logger.warning("RETELL_API_KEY not set — returning dev stub for phone call")
        return _stub_result(task_id, "phone", t0)

    phone_number = _extract_meta(job, "phone_number")
    from_number = _extract_meta(job, "from_number", os.getenv("RETELL_FROM_NUMBER", ""))
    agent_id = _extract_meta(job, "retell_agent_id", _RETELL_AGENT_ID)

    if not phone_number:
        return _error_result(task_id, "retell_channel: 'phone_number' required in job metadata", t0)
    if not agent_id:
        return _error_result(task_id, "retell_channel: RETELL_AGENT_ID not set", t0)

    payload: dict[str, Any] = {
        "agent_id": agent_id,
        "to_number": phone_number,
        "retell_llm_dynamic_variables": {
            "task_prompt": job.prompt,
            "task_id": task_id,
        },
    }
    if from_number:
        payload["from_number"] = from_number

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{_RETELL_BASE_URL}/v2/call",
                json=payload,
                headers={
                    "Authorization": f"Bearer {_RETELL_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Retell AI call initiation failed: %s", exc)
            return _error_result(task_id, str(exc), t0)

    data = resp.json()
    call_id = data.get("call_id", "")
    logger.info("Retell AI call initiated: call_id=%s to=%s", call_id, phone_number)

    return {
        "status": "completed",
        "channel": "phone",
        "task_id": task_id,
        "call_id": call_id,
        "to_number": phone_number,
        "elapsed_seconds": time.monotonic() - t0,
        "retell_response": data,
    }


# ---------------------------------------------------------------------------
# Instantly.ai — cold email channel
# ---------------------------------------------------------------------------

async def _instantly_email(job: Job, task_id: str, t0: float) -> dict[str, Any]:
    """Add a lead to an Instantly.ai campaign and trigger send.

    Workflow:
      1. POST /lead/add  — upsert the lead record
      2. POST /lead/resume-sending — start/resume the campaign for this lead
    """
    if not _INSTANTLY_API_KEY:
        logger.warning("INSTANTLY_API_KEY not set — returning dev stub for email")
        return _stub_result(task_id, "email", t0)

    campaign_id = _extract_meta(job, "campaign_id")
    to_email = _extract_meta(job, "to_email")
    to_name = _extract_meta(job, "to_name", "")
    company = _extract_meta(job, "company", "")
    personalization = _extract_meta(job, "personalization", job.prompt[:500])

    if not campaign_id:
        return _error_result(task_id, "retell_channel: 'campaign_id' required in job metadata", t0)
    if not to_email:
        return _error_result(task_id, "retell_channel: 'to_email' required in job metadata", t0)

    lead_payload = {
        "api_key": _INSTANTLY_API_KEY,
        "campaign_id": campaign_id,
        "email": to_email,
        "first_name": to_name.split()[0] if to_name else "",
        "last_name": " ".join(to_name.split()[1:]) if to_name else "",
        "company_name": company,
        "personalization": personalization,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: add lead
        try:
            add_resp = await client.post(
                f"{_INSTANTLY_BASE_URL}/lead/add",
                json=lead_payload,
            )
            add_resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Instantly.ai lead add failed: %s", exc)
            return _error_result(task_id, str(exc), t0)

        # Step 2: resume sending for this lead
        try:
            resume_resp = await client.post(
                f"{_INSTANTLY_BASE_URL}/lead/resume-sending",
                json={
                    "api_key": _INSTANTLY_API_KEY,
                    "campaign_id": campaign_id,
                    "email": to_email,
                },
            )
            resume_resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Instantly.ai resume-sending failed (lead added): %s", exc)
            # Non-fatal: lead was added, sending may resume on Instantly's schedule

    logger.info("Instantly.ai email queued: campaign=%s to=%s", campaign_id, to_email)

    return {
        "status": "completed",
        "channel": "email",
        "task_id": task_id,
        "campaign_id": campaign_id,
        "to_email": to_email,
        "elapsed_seconds": time.monotonic() - t0,
        "lead_response": add_resp.json(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_meta(job: Job, key: str, default: str = "") -> str:
    """Pull a value from job.metadata, falling back to default."""
    val = job.metadata.get(key, default)
    return str(val) if val else default


def _stub_result(task_id: str, channel: str, t0: float) -> dict[str, Any]:
    return {
        "status": "completed",
        "channel": channel,
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "note": f"dev stub — {channel} API key not set",
    }


def _error_result(task_id: str, error: str, t0: float) -> dict[str, Any]:
    return {
        "status": "error",
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "error": error,
    }
