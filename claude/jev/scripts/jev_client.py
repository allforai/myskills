"""One Jev call over HTTP (OpenRouter's /v1/systemone), with retry on 429/5xx/network errors."""
import json
import os
import time
import urllib.error
import urllib.request

RETRY_STATUS = {429, 500, 502, 503, 504}


class JevError(Exception):
    pass


def call_jev(state, questions, *, model, base_url, api_key, timeout, retries, sleep=time.sleep):
    url = base_url.rstrip("/") + "/v1/systemone"
    body = json.dumps({"state": state, "model": model, "questions": questions}).encode("utf-8")
    for attempt in range(retries + 1):
        last = attempt == retries
        request = urllib.request.Request(url, data=body, method="POST", headers={
            "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code in RETRY_STATUS and not last:
                sleep(0.5 * 2 ** attempt)
                continue
            raise JevError(f"HTTP {e.code}") from None
        except OSError as e:  # URLError, timeouts, connection resets
            if not last:
                sleep(0.5 * 2 ** attempt)
                continue
            raise JevError(f"network: {type(e).__name__}") from None
        except ValueError:
            raise JevError("response is not JSON") from None
        if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
            raise JevError("response has no answers object")
        return {"answers": data["answers"], "usage": data.get("usage") or {}, "model": data.get("model")}
    raise JevError("unreachable")


def make_caller(cfg, *, timeout, retries=None, sleep=time.sleep):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise JevError("OPENROUTER_API_KEY is not set")
    base_url = os.environ.get("JEV_BASE_URL") or cfg["base_url"]
    tries = cfg["retries"] if retries is None else retries

    def ask(state, questions):
        return call_jev(state, questions, model=cfg["model"], base_url=base_url, api_key=api_key,
                        timeout=timeout, retries=tries, sleep=sleep)
    return ask
