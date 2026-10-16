"""Shared CADFEM route configuration. CLI performs a read-only catalog check."""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "cvpr2027/configs/cadfem-astra-api.json"


def load_route():
    route = json.loads(CONFIG.read_text())
    allowed = {
        "explabs": "https://api.experientiallabs.ai/v1",
        "openai": "https://api.openai.com/v1",
    }
    if allowed.get(route["provider"]) != route["base_url"]:
        raise ValueError("Unapproved provider/base URL combination")
    if route["model"] != "gpt-6-astra" or route["automatic_retries"] != 0:
        raise ValueError("This benchmark route requires Astra and zero automatic retries")
    if route.get("fallback_to_direct_openai"):
        raise ValueError("Cross-provider fallback requires an explicit configuration change")
    return route


def read_credential(route):
    variable = route["api_key_env"]
    value = os.environ.get(variable)
    if value:
        return value
    path = ROOT / route["credential_file"]
    if path.stat().st_mode & 0o077:
        raise ValueError("Credential file must be readable only by its owner")
    for line in path.read_text().splitlines():
        name, separator, value = line.strip().removeprefix("export ").partition("=")
        if separator and name == variable:
            value = value.strip().strip("\"'")
            if value:
                return value
    raise ValueError("Missing credential: " + variable)


def budget_status(route, reservation=0.):
    ledger = json.loads((ROOT / route["budget_ledger"]).read_text())
    ceiling = min(float(route["budget_ceiling_usd"]), float(ledger["budget_usd"]))
    spent = float(ledger["session_cost_upper_bound_usd"])
    if not all(math.isfinite(x) and x >= 0 for x in (ceiling, spent, reservation)):
        raise ValueError("Invalid budget accounting")
    if route.get("free_only") and reservation > 0:
        raise ValueError("Free-only mode blocks priced inference; no request was sent")
    if spent + reservation > ceiling:
        raise ValueError("Request exceeds remaining authorized budget")
    return {"budget_usd": ceiling, "accounted_usd": spent,
            "remaining_usd": ceiling - spent, "ledger": route["budget_ledger"]}


def redact(text, credential=""):
    if credential:
        text = text.replace(credential, "[REDACTED]")
    return re.sub(r"(?:xpl_|sk-)[A-Za-z0-9_-]+", "[REDACTED]", text)


def check_access():
    route = load_route()
    key = read_credential(route)
    result = {
        "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "provider": route["provider"], "base_url": route["base_url"],
        "model": route["model"], "method": "GET /models only",
        "inference_requests": 0, "inference_spend_usd": 0,
        "budget": budget_status(route), "inference_access_verified": False,
    }
    request = urllib.request.Request(route["base_url"] + "/models", headers={
        "Authorization": "Bearer " + key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.load(response)
            result["http_status"] = response.status
        models = body.get("data", [])
        entry = next((m for m in models if m.get("id") == route["model"]), None)
        result.update(authenticated=True, model_count=len(models), astra_listed=entry is not None)
        if entry:
            result["catalog_pricing"] = entry.get("pricing")
            result["supported_reasoning_efforts"] = entry.get("supported_reasoning_efforts")
    except urllib.error.HTTPError as error:
        result.update(authenticated=False, http_status=error.code,
                      error=redact(error.read().decode(errors="replace"), key)[:500])
    except Exception as error:
        result.update(authenticated=False, error_type=type(error).__name__)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True,
                        help="Authenticated GET /models; never creates inference")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = check_access()
    serialized = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized)
    print(serialized, end="")
    raise SystemExit(0 if result.get("authenticated") and result.get("astra_listed") else 1)
