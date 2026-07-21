"""Production `model_call` for alert extraction, two flavors:

1. `make_cli_call` — shell out to the local Claude Code CLI (`claude -p`).
   This is the preferred path in the scheduled cloud routine: the environment
   already IS a Claude agent, so no API key exists to manage or leak.
2. `make_model_call` — direct Anthropic API via urllib (stdlib-only), keyed by
   ANTHROPIC_API_KEY. Fallback for environments without the CLI.

`resolve_model_call` picks the best available at runtime; None means alerts are
skipped (build.main() handles that). Pure helpers are split out for tests."""

import json
import os
import shutil
import subprocess
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5"
MAX_TOKENS = 4096
TIMEOUT_SECONDS = 60
CLI_BINARY = "claude"
CLI_TIMEOUT_SECONDS = 300


def make_cli_call(binary=CLI_BINARY, runner=subprocess.run):
    """Return a `model_call(prompt) -> str` that runs `claude -p <prompt>`.

    `runner` is injectable for tests. Raises on a non-zero exit so a broken CLI
    surfaces as a skipped-alerts day (build.main() isolates the failure) rather
    than silently extracting nothing."""

    def model_call(prompt):
        result = runner([binary, "-p", prompt], capture_output=True, text=True,
                        timeout=CLI_TIMEOUT_SECONDS)
        if result.returncode != 0:
            raise RuntimeError(
                "claude CLI failed (%d): %s" % (result.returncode,
                                                (result.stderr or "")[:200]))
        return result.stdout

    return model_call


def build_request(prompt, api_key, model=DEFAULT_MODEL):
    """A POST urllib.Request to the Messages API for a single user prompt."""
    body = json.dumps({
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "content-type": "application/json",
    }
    return urllib.request.Request(API_URL, data=body, headers=headers, method="POST")


def parse_response(payload):
    """Join the text blocks of an Anthropic Messages response dict into a string."""
    blocks = payload.get("content") or []
    return "".join(b.get("text", "") for b in blocks
                   if isinstance(b, dict) and b.get("type") == "text")


def make_model_call(api_key=None, model=None, opener=urllib.request.urlopen):
    """Return a `model_call(prompt) -> str` bound to the given key/model.

    Falls back to ANTHROPIC_API_KEY / ALERT_MODEL from the environment. Raises
    if no key is available, so a misconfigured run fails loudly rather than
    silently extracting nothing."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    mdl = model or os.environ.get("ALERT_MODEL") or DEFAULT_MODEL
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set; cannot extract alert listings")

    def model_call(prompt):
        req = build_request(prompt, key, mdl)
        with opener(req, timeout=TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return parse_response(payload)

    return model_call


def resolve_model_call(which=shutil.which, env=os.environ):
    """Best available extraction path, or None (alerts skipped):
    claude CLI on PATH > ANTHROPIC_API_KEY > nothing."""
    if which(CLI_BINARY):
        return make_cli_call()
    key = env.get("ANTHROPIC_API_KEY")
    if key:
        return make_model_call(api_key=key)
    return None
