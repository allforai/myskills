#!/usr/bin/env python3
"""Shared utilities for product-design pre-built scripts.

All Phase 4-8 scripts import this module for:
- Field constants (single source of truth for field names across layers)
- Data loaders (defensive loading with FileNotFoundError handling)
- Pipeline-decisions writer (append with phase-level deduplication)
- Utility functions (timestamps, JSON writing, directory creation)
"""

import json
import os
import datetime
import sys
import re
import urllib.request
import urllib.error
import time

# ── Field Constants ───────────────────────────────────────────────────────────

# business-flows.json uses "nodes" (NOT "steps")
FLOW_NODES_FIELD = "nodes"


def get_flow_nodes(flow):
    """Get node list from a flow object, using the canonical 'nodes' field."""
    return flow.get(FLOW_NODES_FIELD, [])


def ensure_list(data, *keys):
    """Extract a list from data that may be a list or a dict wrapping one.

    If data is already a list, return it directly.
    If data is a dict, try each key in order, returning the first list found.
    Otherwise return [].
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            v = data.get(k)
            if isinstance(v, list):
                return v
        # If dict has no matching key, try common wrapper patterns
        for k in ("items", "data", "results", "tasks", "gaps", "decisions"):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


# ── Review Server Ports ───────────────────────────────────────────────────────

REVIEW_PORTS = {
    "review-hub": int(os.environ.get("REVIEW_HUB_PORT", "18900")),
}


def kill_other_review_servers(my_port):
    """Kill any review server running on the review-hub port (18900).

    Only one review-hub server should run at a time.
    """
    import signal
    import socket

    port = REVIEW_PORTS["review-hub"]
    if port == my_port:
        return  # already running on the target port, nothing to kill

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(0.3)
        result = sock.connect_ex(("localhost", port))
        if result == 0:
            try:
                import subprocess
                out = subprocess.check_output(
                    ["lsof", "-ti", f":{port}"], text=True
                ).strip()
                for pid_str in out.split("\n"):
                    pid = int(pid_str.strip())
                    os.kill(pid, signal.SIGTERM)
                    print(f"  Stopped previous review-hub server (port {port}, pid {pid})")
                import time as _t
                _t.sleep(0.3)
            except Exception:
                pass
    except Exception:
        pass
    finally:
        sock.close()


# ── Timestamp ─────────────────────────────────────────────────────────────────

def now_iso():
    """Return current UTC time in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── File Utilities ────────────────────────────────────────────────────────────

def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def write_json(path, data):
    """Write data as formatted JSON with UTF-8 encoding."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_json(path):
    """Load JSON from path, return None if file not found or invalid."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def require_json(path, label="file"):
    """Load JSON from path, exit with error if not found."""
    data = load_json(path)
    if data is None:
        print(f"ERROR: {label} not found or invalid: {path}", file=sys.stderr)
        sys.exit(1)
    return data


# ── Data Loaders ──────────────────────────────────────────────────────────────

def _normalize_task(task):
    """Ensure task has both 'task_name'/'name' and 'owner_role'/'role_id' fields.

    Source data may use either variant. This normalizer ensures both fields
    exist so downstream code never hits KeyError regardless of which it accesses.
    """
    # name ↔ task_name
    tn = task.get("task_name", "")
    n = task.get("name", "")
    if tn and not n:
        task["name"] = tn
    elif n and not tn:
        task["task_name"] = n
    elif not tn and not n:
        task["task_name"] = task.get("id", "")
        task["name"] = task.get("id", "")
    # owner_role ↔ role_id
    or_ = task.get("owner_role", "")
    ri = task.get("role_id", "")
    if or_ and not ri:
        task["role_id"] = or_
    elif ri and not or_:
        task["owner_role"] = ri
    return task


def load_task_inventory(base, category=None):
    """Load task-inventory.json, return dict keyed by task ID.

    Handles both list format (canonical: [task, ...]) and dict format
    ({task_id: task, ...}) that LLM-generated scripts sometimes produce.

    Args:
        base: .allforai base path
        category: None (all), "basic", or "core" — filter by task category
    """
    inv = require_json(
        os.path.join(base, "product-map/task-inventory.json"),
        "task-inventory.json"
    )
    raw_tasks = inv["tasks"]
    # Normalize: dict-keyed format → list format
    if isinstance(raw_tasks, dict):
        tasks = []
        for tid, t in raw_tasks.items():
            if isinstance(t, dict):
                if "id" not in t:
                    t["id"] = tid
                tasks.append(t)
    else:
        tasks = raw_tasks
    if category:
        tasks = [t for t in tasks if t.get("category") == category]
    return {t["id"]: _normalize_task(t) for t in tasks}


def load_task_index(base):
    """Load task-index.json, return data or None."""
    return load_json(os.path.join(base, "product-map/task-index.json"))


def load_role_profiles(base):
    """Load role-profiles.json, return {role_id: role_name} map."""
    roles = require_json(
        os.path.join(base, "product-map/role-profiles.json"),
        "role-profiles.json"
    )
    return {r["id"]: r["name"] for r in roles["roles"]}


def load_role_profiles_full(base):
    """Load role-profiles.json, return full roles list."""
    roles = require_json(
        os.path.join(base, "product-map/role-profiles.json"),
        "role-profiles.json"
    )
    return roles["roles"]


def load_business_flows(base):
    """Load business-flows.json, return flows list."""
    fd = load_json(os.path.join(base, "product-map/business-flows.json"))
    if fd is None:
        return []
    return fd.get("flows", [])


def load_flow_index(base):
    """Load flow-index.json, return data or None."""
    return load_json(os.path.join(base, "product-map/flow-index.json"))


def load_product_concept(base):
    """Load product-concept.json, return data or None."""
    return load_json(os.path.join(base, "product-concept/product-concept.json"))


# ── experience-map loaders ────────────────────────────────────────────────────

def load_journey_emotion(base):
    """Load journey-emotion-map.json, return journey_lines list.

    Handles schema variations:
    - Canonical: {"journey_lines": [...]} with emotion_nodes/source_flow fields
    - Variant:   {"journeys": [...]} with nodes/id fields (LLM-generated scripts)
    Normalizes variant format to canonical on load.
    """
    data = load_json(os.path.join(base, "experience-map/journey-emotion-map.json"))
    if data is None:
        return []
    # Try canonical key first, then variant
    lines = ensure_list(data, "journey_lines")
    if not lines:
        lines = ensure_list(data, "journeys")
    # Normalize variant fields to canonical schema
    for line in lines:
        # nodes → emotion_nodes
        if "emotion_nodes" not in line and "nodes" in line:
            line["emotion_nodes"] = line.pop("nodes")
        # Ensure source_flow exists (use id as fallback)
        if "source_flow" not in line:
            line["source_flow"] = line.get("id", "")
        # Normalize emotion_nodes entries: seq → step, task_name → action
        for node in line.get("emotion_nodes", []):
            if "step" not in node and "seq" in node:
                node["step"] = node.pop("seq")
            if "action" not in node and "task_name" in node:
                node["action"] = node.get("task_name", "")
    return lines


def load_experience_map(base):
    """Load experience-map.json, return (operation_lines list, screen_index dict, loaded bool)."""
    data = load_json(os.path.join(base, "experience-map/experience-map.json"))
    if data is None:
        return [], {}, False
    lines = ensure_list(data, "operation_lines")
    index = data.get("screen_index", {}) if isinstance(data, dict) else {}
    return lines, index, True


def build_node_by_id(operation_lines):
    """Build {node_id: node_object} mapping from operation_lines."""
    result = {}
    for line in operation_lines:
        for node in line.get("nodes", []):
            result[node["id"]] = node
    return result


def build_screen_by_id_from_lines(operation_lines):
    """Build {screen_id: screen_object} mapping from all nodes in all operation lines."""
    result = {}
    for line in operation_lines:
        for node in line.get("nodes", []):
            for s in node.get("screens", []):
                result[s["id"]] = s
    return result


def build_task_screen_map_from_lines(operation_lines):
    """Build {task_id: [screen_ids]} by collecting screen.tasks across all nodes."""
    result = {}
    for line in operation_lines:
        for node in line.get("nodes", []):
            for s in node.get("screens", []):
                for tid in s.get("tasks", []):
                    result.setdefault(tid, []).append(s["id"])
    return result


def get_node_screens(node):
    """Return screen list from a node object."""
    return node.get("screens", [])


def load_interaction_gate(base):
    """Load interaction-gate.json, return gate data dict or None."""
    return load_json(os.path.join(base, "experience-map/interaction-gate.json"))


def load_entity_model(base):
    """Load entity-model.json, return entities list and relationships list."""
    data = load_json(os.path.join(base, "product-map/entity-model.json"))
    if data is None:
        return [], []
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    return entities, relationships


def load_api_contracts(base):
    """Load api-contracts.json, return endpoints list."""
    data = load_json(os.path.join(base, "product-map/api-contracts.json"))
    if data is None:
        return []
    return data.get("endpoints", [])


def load_view_objects(base):
    """Load view-objects.json, return view_objects list."""
    data = load_json(os.path.join(base, "product-map/view-objects.json"))
    if data is None:
        return []
    return data.get("view_objects", [])


# ── Flow-Task References ─────────────────────────────────────────────────────

def collect_flow_task_refs(flows):
    """Collect all task IDs referenced by flow nodes."""
    refs = set()
    for flow in flows:
        for node in get_flow_nodes(flow):
            if isinstance(node, str):
                refs.add(node)
            elif isinstance(node, dict):
                refs.add(node.get("task_ref", ""))
    return refs


# ── Pipeline Decisions ────────────────────────────────────────────────────────

def append_pipeline_decision(base, phase, detail, decision="auto_confirmed", shard=None):
    """Append a decision to pipeline-decisions.json, dedup by phase name.

    If an entry with the same 'phase' already exists, it is replaced
    (prevents duplicate entries on re-runs).

    Args:
        shard: If set, write to pipeline-decisions-{shard}.json instead of
               the main file (avoids race conditions during parallel execution).
    """
    filename = f"pipeline-decisions-{shard}.json" if shard else "pipeline-decisions.json"
    pipe_path = os.path.join(base, filename)
    pipe = []
    if os.path.exists(pipe_path):
        try:
            with open(pipe_path) as f:
                pipe = json.load(f)
        except (json.JSONDecodeError, IOError):
            pipe = []

    # Remove existing entry with same phase (dedup)
    pipe = [p for p in pipe if p.get("phase") != phase]

    pipe.append({
        "phase": phase,
        "decision": decision,
        "detail": detail,
        "decided_at": now_iso()
    })

    write_json(pipe_path, pipe)
    return pipe_path


# ── CLI Base Path Resolution ─────────────────────────────────────────────────

def resolve_base_path():
    """Resolve BASE path from CLI argument or default to .allforai/ in cwd."""
    if len(sys.argv) >= 2:
        base = sys.argv[1]
    else:
        base = os.path.join(os.getcwd(), ".allforai")

    if not os.path.isdir(base):
        print(f"ERROR: Base path does not exist: {base}", file=sys.stderr)
        sys.exit(1)

    return base


def parse_args():
    """Parse common CLI arguments: <BASE_PATH> [--mode auto] [--extra value].

    Returns (base_path, args_dict).
    """
    base = resolve_base_path()

    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--") and i + 1 < len(sys.argv):
            key = sys.argv[i][2:]
            args[key] = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    return base, args


# ── Split File Writer ─────────────────────────────────────────────────────────

def write_split_files(base, subdir, prefix, split_by, splits, extra_meta=None):
    """Write human-friendly split files using a unified wrapper schema.

    Args:
        base: .allforai base path
        subdir: output subdirectory under base (e.g. "screen-map")
        prefix: filename prefix (e.g. "screen-map" → "screen-map-R001.json")
        split_by: dimension name (e.g. "role", "priority")
        splits: dict {split_value: {"label": str, "description": str, "items": list}}
        extra_meta: optional dict of extra top-level fields to merge into each file
    """
    out_dir = os.path.join(base, subdir)
    ensure_dir(out_dir)
    ts = now_iso()
    written = []
    for split_value, info in splits.items():
        wrapper = {
            "split_by": split_by,
            "split_value": split_value,
            "split_label": info["label"],
            "description": info["description"],
            "generated_at": ts,
            "count": len(info["items"]),
            "items": info["items"],
        }
        if extra_meta:
            wrapper.update(extra_meta)
        fname = f"{prefix}-{split_value}.json"
        path = write_json(os.path.join(out_dir, fname), wrapper)
        written.append(path)
    return written


# ── XV Cross-model Validation ─────────────────────────────────────────────────
# Direct OpenRouter API calls — no MCP dependency.

XV_ROUTING = {
    # Phase 4 (use-case)
    "edge_case_generation": "deepseek",
    "acceptance_criteria_review": "gpt",
    # Phase 5 (feature-gap)
    "journey_validation": "gemini",
    "gap_prioritization": "gpt",
    # Phase 7 (ui-design)
    "design_review": "gemini",
    "visual_consistency": "gpt",
    # Phase 8 (design-audit)
    "cross_layer_validation": "deepseek",
    "coverage_analysis": "gpt",
    # Wireframe XV
    "wireframe_usability_review": "gemini",
    "wireframe_completeness_check": "deepseek",
    "wireframe_consistency_check": "gpt",
    # Experience map
    "screen_enrichment": "gemini",
}

# Family search prefixes — used to find the latest model via OpenRouter API.
# Each family maps to a vendor prefix; _resolve_model() picks the newest match.
XV_FAMILY_SEARCH = {
    "gpt": "openai/gpt-",
    "gemini": "google/gemini-",
    "deepseek": "deepseek/deepseek-",
}

# Runtime cache: family → resolved model ID (populated on first xv_call)
_xv_model_cache = {}

# File-based cache path + 24-hour TTL
_XV_CACHE_FILE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "xv-model-cache.json")
_XV_CACHE_TTL = 86400  # 24 hours


def _resolve_api_key(key_name):
    """Resolve an API key from environment variable.

    Users should export keys in their shell profile (~/.zshrc, ~/.bashrc).
    .mcp.json uses ${VAR} references to pick up the same env vars for MCP servers.
    """
    return os.environ.get(key_name, "")


def xv_available():
    """Check if OPENROUTER_API_KEY is available via environment variable."""
    return bool(_resolve_api_key("OPENROUTER_API_KEY"))


def xv_call(task_type, prompt, system_prompt=None, temperature=0.3):
    """Send XV request directly to OpenRouter API.

    Uses task→family routing from defaults.ts (Python mirror).
    Resolves family→model dynamically via OpenRouter /models API (cached).
    Returns dict: {response, model_used, family, task_type}.
    429 → sleep 3s → retry once → raise on failure.
    """
    api_key = _resolve_api_key("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found — export it in ~/.zshrc or ~/.bashrc")

    family = XV_ROUTING.get(task_type, "gpt")
    model = _resolve_model(family, api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/product-design-skill",
    }

    last_err = None
    for attempt in range(2):
        if attempt > 0:
            time.sleep(3)
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            return {
                "response": content,
                "model_used": body.get("model", model),
                "family": family,
                "task_type": task_type,
            }
        except urllib.error.HTTPError as e:
            last_err = e
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:200]
            except Exception:
                err_body = "(body unreadable)"
            if e.code == 429 and attempt == 0:
                print(f"  XV: 429 rate-limited, retrying in 3s...")
                continue
            raise RuntimeError(
                f"XV call failed ({task_type}): HTTP {e.code} — {err_body}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"XV call failed ({task_type}): {e}") from e

    raise RuntimeError(f"XV call failed after retry ({task_type}): {last_err}")


def _resolve_model(family, api_key):
    """Resolve family to the latest model ID via OpenRouter /models API.

    Queries once per session, caches results. Picks the newest non-preview
    model matching the family prefix; falls back to newest preview if no
    stable release exists.
    """
    if family in _xv_model_cache:
        return _xv_model_cache[family]

    # Try loading from file cache (24h TTL)
    if not _xv_model_cache:
        _load_file_cache()

    if family in _xv_model_cache:
        return _xv_model_cache[family]

    # File cache miss or expired — fetch from API
    _populate_model_cache(api_key)

    if family in _xv_model_cache:
        return _xv_model_cache[family]

    # Ultimate fallback
    fallback = {"gpt": "openai/gpt-4o", "gemini": "google/gemini-2.5-flash",
                "deepseek": "deepseek/deepseek-chat"}
    model = fallback.get(family, "openai/gpt-4o")
    _xv_model_cache[family] = model
    return model


def _load_file_cache():
    """Load model cache from disk if fresh (< 24h old)."""
    global _xv_model_cache
    try:
        if not os.path.exists(_XV_CACHE_FILE):
            return
        age = time.time() - os.path.getmtime(_XV_CACHE_FILE)
        if age > _XV_CACHE_TTL:
            return  # expired
        with open(_XV_CACHE_FILE) as f:
            cached = json.load(f)
        if isinstance(cached, dict) and cached:
            _xv_model_cache.update(cached)
            for k, v in cached.items():
                print(f"  XV: {k} → {v} (cached)")
    except Exception:
        pass  # corrupted cache, will re-fetch


def _save_file_cache():
    """Persist model cache to disk."""
    try:
        with open(_XV_CACHE_FILE, "w") as f:
            json.dump(_xv_model_cache, f)
    except Exception:
        pass


def _populate_model_cache(api_key):
    """Fetch OpenRouter /models, then ask an LLM to pick the best model per family.

    Steps:
    1. GET /models → filter text-output candidates per family
    2. Send candidate list to a cheap LLM to select the best general-purpose model
    3. Cache result to disk for 24h reuse
    """
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = data.get("data", [])
    except Exception as e:
        print(f"  XV: failed to fetch /models, using fallbacks: {e}")
        return

    # Build candidate summaries per family
    family_candidates = {}
    for family, prefix in XV_FAMILY_SEARCH.items():
        candidates = [m for m in models if m.get("id", "").startswith(prefix)]
        # Filter to text-output capable
        candidates = [m for m in candidates
                      if "text" in str(m.get("architecture", {}).get("output_modalities", []))]
        if not candidates:
            continue
        # Sort newest first, take top 15
        candidates.sort(key=lambda m: m.get("created", 0), reverse=True)
        family_candidates[family] = [
            {"id": m["id"], "name": m.get("name", ""), "created": m.get("created", 0)}
            for m in candidates[:15]
        ]

    if not family_candidates:
        return

    # Ask LLM to pick the best model per family (single call, all families)
    prompt_lines = [
        "Below are model lists from OpenRouter API, sorted by release date "
        "(NEWEST FIRST). For each family, pick the ONE best model for "
        "general-purpose TEXT chat and analysis.",
        "",
        "Rules:",
        "- Pick the NEWEST model that supports general text chat",
        "- EXCLUDE: image-generation, embedding, audio-only, distilled, lite/mini variants",
        "- Model names you don't recognize are fine — trust the release date ordering",
        "- Respond with ONLY a JSON object: {\"family\": \"model_id\", ...}",
        ""
    ]
    for family, cands in family_candidates.items():
        prompt_lines.append(f"=== {family} ===")
        for c in cands:
            # Convert unix timestamp to readable date
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(c["created"], tz=timezone.utc).strftime("%Y-%m-%d")
            prompt_lines.append(f"  {c['id']}  (released: {dt}, name: {c['name']})")
        prompt_lines.append("")

    try:
        # Use the cheapest available model for this meta-selection
        selector_model = "openai/gpt-4o-mini"
        payload = json.dumps({
            "model": selector_model,
            "messages": [{"role": "user", "content": "\n".join(prompt_lines)}],
            "temperature": 0,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/product-design-skill",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        raw = body["choices"][0]["message"]["content"]
        picks = xv_parse_json(raw)

        for family, model_id in picks.items():
            if family in family_candidates:
                # Validate the pick exists in candidates
                valid_ids = {c["id"] for c in family_candidates[family]}
                if model_id in valid_ids:
                    _xv_model_cache[family] = model_id
                    print(f"  XV: {family} → {model_id}")
                else:
                    print(f"  XV: {family} → LLM picked '{model_id}' not in candidates, skipping")
    except Exception as e:
        print(f"  XV: LLM model selection failed: {e}, using newest per family")
        # Fallback: just pick newest text-output model per family
        for family, cands in family_candidates.items():
            if cands and family not in _xv_model_cache:
                _xv_model_cache[family] = cands[0]["id"]
                print(f"  XV: {family} → {cands[0]['id']} (fallback: newest)")

    # Persist to disk for 24h reuse
    if _xv_model_cache:
        _save_file_cache()


def xv_review(reviews_list):
    """Build cross_model_review wrapper.

    Returns {"generated_at": ..., "reviews": reviews_list}.
    """
    return {
        "generated_at": now_iso(),
        "reviews": reviews_list,
    }


def xv_parse_json(raw_text):
    """Parse JSON from XV response, handling markdown fences, trailing commas, and truncation."""
    import re
    text = raw_text.strip()

    # Strip ```json ... ``` wrapper
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    # Remove trailing commas before } or ] (common LLM output issue)
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Remove single-line // comments (some models add them)
    text = re.sub(r'//[^\n]*', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: try to extract the outermost JSON object
    match = re.search(r'\{', text)
    if match:
        # Find the balanced closing brace
        depth = 0
        start = match.start()
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    # Last resort: truncated JSON — close all open brackets
    cleaned = text.rstrip()
    # Count unclosed brackets
    open_braces = cleaned.count('{') - cleaned.count('}')
    open_brackets = cleaned.count('[') - cleaned.count(']')
    # Strip trailing comma
    cleaned = cleaned.rstrip(',').rstrip()
    # Close unclosed structures
    cleaned += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return json.loads(cleaned)


# ── Interaction type inference ────────────────────────────────────────────────


def infer_interaction_type(task, crud_type="", audience_type=""):
    """Infer interaction_type from task name, category, and audience_type.

    Returns (interaction_type, crud_type) tuple.
    Uses generic keyword patterns applicable to any product domain.
    The *crud_type* parameter is accepted for backward compat but ignored;
    CRUD is inferred from keywords.
    """
    name = task.get("name", "").lower()
    main_flow = task.get("main_flow", [])
    main_flow_text = " ".join(str(s).lower() for s in main_flow)

    # ── SY: System/Onboarding ──
    if re.search(r"引导|onboard|welcome|tutorial", name):
        return "SY1", "R"
    if re.search(r"注册|signup|register", name):
        return "SY2", "C"
    if re.search(r"登录|登出|login|logout|sign.?in|sign.?out", name):
        return "SY2", "R"
    if re.search(r"重置密码|reset.?password|forgot", name):
        return "SY2", "U"

    # ── MG4: Approval/Review (before generic MG) ──
    if re.search(r"审核|审批|approve|review|verify", name) and audience_type == "professional":
        return "MG4", "U"

    # ── MG7: Dashboard/Analytics/Monitoring ──
    if re.search(r"统计|仪表|监控|数据|报表|分析|dashboard|analytics|monitor|stats|trend", name):
        return "MG7", "R"

    # ── MG8: Configuration/Settings ──
    if re.search(r"配置|设置|设定|偏好|config|setting|preference", name):
        return "MG8", "U"

    # ── MG3: State management / publish / archive ──
    if re.search(r"发布|上下架|归档|清理|处理.*异常|处理.*告警|publish|archive|cleanup", name):
        return "MG3", "U"

    # ── Consumer-specific patterns ──
    if audience_type == "consumer":
        if re.search(r"浏览|列表|推荐|发现|explore|browse|discover|feed|管理已下载", name):
            return "CT1", "R"
        if re.search(r"复习|测试|练习|闪卡|quiz|review|practice|flashcard|swipe", name):
            return "CT4", "R"
        if re.search(r"学习|阅读|查看.*详|沉浸|扮演|内容|read|learn|immerse|content|detail", name):
            return "CT2", "R"
        if re.search(r"付费|订阅|支付|购买|subscribe|pay|purchase|checkout", name):
            return "EC2", "C"
        if re.search(r"提交|反馈|submit|feedback|report", name):
            return "MG2-C", "C"
        if re.search(r"查看.*状态|查看.*账单|查看.*订阅|view.*status", name):
            return "CT2", "R"
        if re.search(r"管理|manage", name):
            return "CT1", "R"
        return "CT2", "R"

    # ── Professional-specific patterns ──
    if audience_type == "professional":
        if re.search(r"生成|创建|新增|添加|create|generate|add|new", name):
            return "MG2-C", "C"
        if re.search(r"管理|列表|查看.*列表|list|manage|browse", name):
            return "MG2-L", "R"
        if re.search(r"日志|审计|log|audit", name):
            return "MG2-L", "R"
        if re.search(r"编辑|修改|更新|edit|update|modify", name):
            return "MG2-E", "U"
        if re.search(r"查看|详情|view|detail", name):
            return "MG1", "R"
        return "MG1", "R"

    # ── Sync/background tasks ──
    if re.search(r"同步|sync|background", name):
        return "MG1", "R"

    return "MG1", "R"


def refine_view_type(task, crud_type):
    """Infer view_types list from task and CRUD type."""
    itype, _ = infer_interaction_type(task, crud_type)
    view_type_map = {
        "CT1": ["list_item"],
        "CT2": ["detail"],
        "CT4": ["list_item"],
        "MG1": ["detail"],
        "MG2-L": ["list_item"],
        "MG2-C": ["create_form"],
        "MG2-E": ["edit_form"],
        "MG3": ["state_action"],
        "MG4": ["detail", "state_action"],
        "MG7": ["detail"],
        "MG8": ["edit_form"],
        "EC2": ["create_form"],
        "SY1": ["detail"],
        "SY2": ["create_form"],
    }
    return view_type_map.get(itype, ["list_item"])


# ── Full Context ──────────────────────────────────────────────────────────────


class FullContext:
    """One-shot container for ALL .allforai artifacts.

    Loaded by load_full_context(base). Each field is None or empty when the
    corresponding artifact file is missing. Methods provide filtered views.
    """

    __slots__ = (
        "tasks", "roles", "roles_full", "flows",
        "entity_model", "api_contracts", "view_objects",
        "experience_map", "screens", "task_screen_map",
        "interaction_gate", "pattern_catalog", "behavioral_standards",
        "concept", "xv_findings", "constraints",
    )

    def __init__(self):
        self.tasks = {}                  # {task_id: task_dict}
        self.roles = {}                  # {role_id: role_name}
        self.roles_full = []             # [role_dict, ...]
        self.flows = []                  # [flow_dict, ...]
        self.entity_model = None         # full dict or None
        self.api_contracts = []          # [endpoint_dict, ...]
        self.view_objects = []           # [vo_dict, ...]
        self.experience_map = None       # raw data dict or None
        self.screens = {}                # {screen_id: screen_dict}
        self.task_screen_map = {}        # {task_id: [screen_ids]}
        self.interaction_gate = None     # gate data dict or None
        self.pattern_catalog = None      # pattern catalog data or None
        self.behavioral_standards = None # behavioral standards data or None
        self.concept = None              # product concept data or None
        self.xv_findings = []            # [{source_phase, ...}, ...]
        self.constraints = []            # [{constraint from file, ...}, ...]

    # -- Filtered accessors ------------------------------------------------

    def get_constraints(self, target):
        """Return constraints whose 'target' field matches *target*."""
        return [c for c in self.constraints
                if c.get("target") == target]

    def get_xv_findings(self, source_phase):
        """Return XV findings originating from *source_phase*."""
        return [f for f in self.xv_findings
                if f.get("_source_phase") == source_phase]

    def vo_for_screen(self, screen_id):
        """Return view objects relevant to *screen_id* via screen_id match or task intersection."""
        # Direct screen_id match (primary)
        direct = [vo for vo in self.view_objects if vo.get("screen_id") == screen_id]
        if direct:
            return direct
        # Fallback: task intersection
        screen = self.screens.get(screen_id)
        if not screen:
            return []
        screen_tasks = set(screen.get("tasks", []))
        if not screen_tasks:
            return []
        return [vo for vo in self.view_objects
                if screen_tasks & set(vo.get("task_refs", []))]

    def api_for_screen(self, screen_id):
        """Return API endpoints relevant to *screen_id* via VO api_ref or task intersection."""
        # Via VO actions (primary — VOs link screen_id → api_ref → endpoint)
        vos = self.vo_for_screen(screen_id)
        if vos:
            api_ids = set()
            for vo in vos:
                for act in vo.get("vo_actions", []):
                    ref = act.get("api_ref", "")
                    if ref:
                        api_ids.add(ref)
            if api_ids:
                ep_map = {ep.get("api_id") or ep.get("id", ""): ep for ep in self.api_contracts}
                return [ep_map[aid] for aid in api_ids if aid in ep_map]
        # Fallback: task intersection
        screen = self.screens.get(screen_id)
        if not screen:
            return []
        screen_tasks = set(screen.get("tasks", []))
        if not screen_tasks:
            return []
        return [ep for ep in self.api_contracts
                if screen_tasks & set(ep.get("task_refs", []))]


def _collect_xv_findings(base):
    """Scan subdirs of *base* for \\*-xv-review.json files.

    Each file is expected to have a ``reviews`` list. Every review entry
    is tagged with ``_source_phase`` (the subdirectory name) so callers
    can filter by origin.
    """
    findings = []
    if not os.path.isdir(base):
        return findings
    for entry in sorted(os.listdir(base)):
        subdir = os.path.join(base, entry)
        if not os.path.isdir(subdir):
            continue
        for fname in sorted(os.listdir(subdir)):
            if fname.endswith("-xv-review.json"):
                data = load_json(os.path.join(subdir, fname))
                if data and isinstance(data.get("reviews"), list):
                    for review in data["reviews"]:
                        tagged = dict(review)
                        tagged["_source_phase"] = entry
                        findings.append(tagged)
    return findings


def _collect_constraints(base):
    """Load all .json files from ``<base>/constraints/`` directory.

    Each file wraps a list: ``{"source_tab": "...", "constraints": [...]}``.
    The function flattens all constraint entries into a single list.
    """
    cdir = os.path.join(base, "constraints")
    results = []
    if not os.path.isdir(cdir):
        return results
    for fname in sorted(os.listdir(cdir)):
        if fname.endswith(".json"):
            data = load_json(os.path.join(cdir, fname))
            if data is not None:
                constraints = data.get("constraints", [])
                if isinstance(constraints, list):
                    results.extend(constraints)
    return results


def load_full_context(base):
    """Create a FullContext by loading ALL artifacts from *base*.

    Every load is defensive — missing files result in None or empty defaults.
    """
    ctx = FullContext()

    # -- product-map artifacts --
    inv_data = load_json(os.path.join(base, "product-map/task-inventory.json"))
    if inv_data and inv_data.get("tasks"):
        raw = inv_data["tasks"]
        if isinstance(raw, dict):
            # dict-keyed format → normalize to list
            task_list = []
            for tid, t in raw.items():
                if isinstance(t, dict):
                    if "id" not in t:
                        t["id"] = tid
                    task_list.append(t)
        else:
            task_list = raw
        ctx.tasks = {t["id"]: _normalize_task(t) for t in task_list}

    roles_data = load_json(os.path.join(base, "product-map/role-profiles.json"))
    if roles_data and isinstance(roles_data.get("roles"), list):
        ctx.roles = {r["id"]: r["name"] for r in roles_data["roles"]}
        ctx.roles_full = roles_data["roles"]

    flows_data = load_json(os.path.join(base, "product-map/business-flows.json"))
    if flows_data:
        ctx.flows = flows_data.get("flows", [])

    em_data = load_json(os.path.join(base, "product-map/entity-model.json"))
    if em_data:
        ctx.entity_model = em_data

    api_data = load_json(os.path.join(base, "product-map/api-contracts.json"))
    if api_data:
        ctx.api_contracts = api_data.get("endpoints", [])

    vo_data = load_json(os.path.join(base, "product-map/view-objects.json"))
    if vo_data:
        ctx.view_objects = vo_data.get("view_objects", [])

    # -- experience-map artifacts --
    exp_data = load_json(os.path.join(base, "experience-map/experience-map.json"))
    if exp_data:
        ctx.experience_map = exp_data
        op_lines = ensure_list(exp_data, "operation_lines")
        ctx.screens = build_screen_by_id_from_lines(op_lines)
        ctx.task_screen_map = build_task_screen_map_from_lines(op_lines)

    ctx.interaction_gate = load_json(
        os.path.join(base, "experience-map/interaction-gate.json"))

    # -- pattern & behavioral data (now read from experience-map screen nodes) --
    ctx.pattern_catalog = None  # deprecated: merged into experience-map screen._pattern* fields
    ctx.behavioral_standards = None  # deprecated: merged into experience-map screen._behavioral* fields
    ctx.concept = load_json(
        os.path.join(base, "product-concept/product-concept.json"))

    # -- cross-cutting --
    ctx.xv_findings = _collect_xv_findings(base)
    ctx.constraints = _collect_constraints(base)

    return ctx


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("_common.py loaded successfully")
    print(f"  FLOW_NODES_FIELD = {FLOW_NODES_FIELD!r}")
    print(f"  now_iso() = {now_iso()}")
    print("All imports OK")
