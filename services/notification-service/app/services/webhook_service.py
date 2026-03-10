"""
Webhook delivery service — sends events to tenant-configured HTTP endpoints.
Uses HMAC-SHA256 signing for security.
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


def _sign_payload(secret: str, payload_str: str) -> str:
    """HMAC-SHA256 signature for webhook verification."""
    return hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()


def deliver_webhook(url: str, event: str, payload: Dict[str, Any],
                    secret: Optional[str] = None, timeout: int = 10) -> dict:
    """
    Deliver a webhook to a URL with optional HMAC signing.
    Returns delivery result dict.
    """
    body = json.dumps({
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload
    })

    headers = {
        "Content-Type": "application/json",
        "X-StockPilot-Event": event,
        "X-StockPilot-Timestamp": str(int(time.time())),
    }
    if secret:
        headers["X-StockPilot-Signature"] = f"sha256={_sign_payload(secret, body)}"

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, content=body, headers=headers)
        duration_ms = (time.time() - start) * 1000
        logger.info(f"Webhook {event} → {url}: {resp.status_code} ({duration_ms:.0f}ms)")
        return {
            "status": "success" if resp.status_code < 400 else "failed",
            "http_status": resp.status_code,
            "response_body": resp.text[:500],
            "duration_ms": round(duration_ms, 2),
        }
    except httpx.TimeoutException:
        logger.error(f"Webhook {event} → {url}: TIMEOUT")
        return {"status": "failed", "error": "timeout", "duration_ms": timeout * 1000}
    except Exception as e:
        logger.error(f"Webhook {event} → {url}: {e}")
        return {"status": "failed", "error": str(e)}


def deliver_to_all_endpoints(endpoints: list, event: str, payload: Dict[str, Any]) -> list:
    """Deliver webhook event to all active registered endpoints for this event."""
    results = []
    for endpoint in endpoints:
        if event not in (endpoint.events or []) and "*" not in (endpoint.events or []):
            continue
        result = deliver_webhook(
            url=endpoint.url,
            event=event,
            payload=payload,
            secret=endpoint.secret,
        )
        results.append({"endpoint_id": str(endpoint.id), "url": endpoint.url, **result})
    return results
