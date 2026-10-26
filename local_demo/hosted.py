"""Cloudflare inference. Credentials stay on the backend; no automatic retries."""
from __future__ import annotations

import json
import os
import re

import httpx
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

MODEL = "@cf/openai/gpt-oss-20b"


class CloudflareModel:
    def __init__(self):
        self.account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
        self.gateway = os.environ.get("CLOUDFLARE_GATEWAY_ID", "").strip()
        self._token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
        self.enabled = os.environ.get("CATALOG_CHAT_ENABLED", "false").lower() == "true"
        self.limits_confirmed = os.environ.get("CATALOG_CLOUD_LIMITS_CONFIRMED", "false").lower() == "true"
        self.last_success = False

    @property
    def configured(self):
        return bool(re.fullmatch(r"[a-fA-F0-9]{32}", self.account)
                    and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", self.gateway) and self._token)

    @property
    def ready(self):
        return self.configured and self.enabled and self.limits_confirmed

    def status(self):
        # Health checks never generate tokens or transmit questions/documents.
        return {"provider": "cloudflare", "model": MODEL, "configured": self.configured,
                "enabled": self.ready, "reachable": self.last_success, "installed": self.configured,
                "verified": self.last_success}

    async def structured(self, system, context, schema):
        if not self.ready:
            raise ValueError("Hosted chat is not enabled")
        # The model-in-path API is required for Workers AI prepaid Gateway billing.
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account}/ai/run/{MODEL}"
        body = {"stream": False, "max_tokens": 2048, "temperature": 0,
                "response_format": {"type": "json_schema", "json_schema": schema},
                "messages": [{"role": "system", "content": "Reasoning: low\n" + system},
                             {"role": "user", "content": json.dumps(context, ensure_ascii=False)}]}
        headers = {"Authorization": "Bearer " + self._token, "cf-aig-gateway-id": self.gateway,
                   "cf-aig-collect-log": "true", "cf-aig-collect-log-payload": "false",
                   "cf-aig-max-attempts": "1"}
        try:
            async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                         timeout=httpx.Timeout(90, connect=5)) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
            payload = response.json()
            if payload.get("success") is False:
                raise ValueError("Provider rejected the request")
            result = payload.get("result", payload)
            value = parse_result(result)
            Draft202012Validator(schema).validate(value)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, ValidationError):
            self.last_success = False
            # Do not propagate remote bodies, headers, credentials or account details.
            raise ValueError("Hosted model unavailable or returned invalid JSON") from None
        self.last_success = True
        return value


def parse_result(result):
    """Accept native response and Responses-style assistant text, never reasoning."""
    if not isinstance(result, dict):
        raise ValueError("Invalid provider response")
    if result.get("status") == "incomplete" or result.get("finish_reason") == "length":
        raise ValueError("Truncated response")
    if "response" in result:
        value = result["response"]
    elif "choices" in result:
        choice = result["choices"][0]
        if choice.get("finish_reason") != "stop":
            raise ValueError("Incomplete response")
        value = choice["message"]["content"]
    else:
        text = [c["text"] for item in result.get("output", [])
                if item.get("type") == "message" and item.get("role") == "assistant"
                for c in item.get("content", []) if c.get("type") == "output_text"]
        if not text:
            raise ValueError("No assistant response")
        value = "".join(text)
    return json.loads(value) if isinstance(value, str) else value
