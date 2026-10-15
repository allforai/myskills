# jev 插件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建 Claude Code 插件 `claude/jev/`：选模型（按项目开关的 UserPromptSubmit hook + 本轮降档 skill + 照做与 token 统计）、批量分类与打分（`jev_batch.py` + `classify` skill，含校准审查、调阈值、裁决落地）、代码扫描（`code_chunks.py` + `code-scan` skill，含误报率回流），都经 OpenRouter 调 Jev。

**Architecture:** 三个功能共用 `jev_config.py`（配置、按项目开关、外发放行、日志路径）与 `jev_client.py`（一次 HTTP 调用 + 重试）。选模型是一个永不挡路的 hook：从 transcript 读出未被降档污染的会话模型，判出简单题时用 `additionalContext` 要求 Claude 先调用 frontmatter 带 `model` 的 tier skill；另一个 PostToolUse hook 记下 tier skill 是否真被调用。批量判断是一个可断点续跑的脚本：样本试跑 → `approve` 留审查记录 → 全量 → 按阈值分 auto / review / failed（`rebucket` 改阈值不重新请求）→ `resolve` 落地裁决 → `export` / `save-set`。代码扫描只负责把代码切成批量脚本的输入。

**Tech Stack:** Python 3.10+ 标准库（`urllib`、`concurrent.futures`；`http.server` 仅测试用），pytest。

**Spec:** `docs/superpowers/specs/2026-10-16-jev-plugin-design.md`

## Global Constraints

- 只用 Python 标准库；无第三方依赖、无构建步骤。
- 地址：`POST {base_url}/v1/systemone`，`base_url` 默认 `https://openrouter.ai/api`，环境变量 `JEV_BASE_URL` 覆盖；key 取 `OPENROUTER_API_KEY`。
- 模型 id 默认 `~typesafe/jev-latest`。
- 配置与状态目录：`${XDG_CONFIG_HOME:-~/.config}/jev/`；不写 `CLAUDE_PLUGIN_ROOT`。Claude transcript 目录：`${CLAUDE_CONFIG_DIR:-~/.claude}/projects/<项目路径中非字母数字字符换成 ->`。
- 选模型默认关，按项目开关（项目 = `cwd` 所在 git 仓库根，否则 `cwd`）；只降不升；阈值 0.8；客户端超时 3 秒；hook `timeout` 5 秒；prompt 超过 8000 字符不发；日志不记 prompt 原文；`route.assume_model` 默认不设。
- 会话模型 = transcript 里最后一条"不在已降档轮内"的 assistant 消息的模型；轮的边界是用户真正发出的消息（不是 tool_result、不是 `isMeta` 消息）。
- 批量：超过 50 行全量前必须有已 `approve` 的 `--sample`（默认 20）；题目哈希只含题目与模型、不含阈值；花费上限默认 1 美元；并发默认 8；noul 上下阈值默认 0.9 / 0.1；choice / score 默认阈值 0.8；`state` 超过 32000 字节标 `long_context`；规则已核实 ≥ 4 次且误报过半时 `save-set` 拒存。
- 外发放行不通过：零请求、退出码 3。
- 插件名 `jev`，安装为 `jev@jev`，版本 `0.1.0`。
- 不碰 CI；自动检查放 `.githooks/pre-commit`。提交直接在 main 上，用 pathspec 提交（`git commit -- <paths>`），一个任务一个提交；提交信息结尾带 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- 测试命令：`python3 -m pytest -q claude/jev/tests`。

## Review Focus

- transcript 不存在、有坏行、以 `<synthetic>` 结尾、或截取尾部时从一轮中间开始：不崩；读不出模型就不降档、不调用 Jev。→ Task 4 测试。
- `config.json` 不是合法 JSON：hook 零输出退出 0；批量脚本报出含文件路径的错误并退出 2，不发请求。→ Task 4、Task 6 测试。
- 输入 JSONL 有空行、坏行、重复 id、缺 `state`；裁决文件里有不存在的 id：在发请求 / 写文件之前报出行号并拒绝。→ Task 6 测试。
- 续跑时输出文件来自另一套题目：拒绝；只改了阈值：不算另一套题目。→ Task 6 测试。
- 在已打开项目的子目录、或经符号链接进入同一仓库：算同一个项目。→ Task 2 测试。

---

### Task 1: 三个探针（P1 真实调用 / P2 本轮降档与 transcript 形状 / P3 区分手打 prompt）

不写产品代码。结论写进 spec 末尾"探针结论"一节。P2 若不通过，**停下来告诉用户**，等用户确认后再按 spec 的降级方案改 Task 4。

**Files:**
- Modify: `docs/superpowers/specs/2026-10-16-jev-plugin-design.md`（"探针结论"一节）
- 临时文件全部放在会话 scratchpad 目录（下文记为 `$SCRATCH`），不进仓库。

- [ ] **Step 1: P1 — 真实调用一次**

```bash
curl -sS -w '\nHTTP %{http_code} in %{time_total}s\n' https://openrouter.ai/api/v1/systemone \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"~typesafe/jev-latest","state":"I have asked three times. Let me talk to a real person, the app keeps crashing when I pay.",
       "questions":{
         "dept":{"type":"choice","instructions":"Which team should handle this?","criteria":{"billing":"payments, refunds, invoices","technical":"bugs, crashes, errors"}},
         "anger":{"type":"score","instructions":"How frustrated is the customer?","criteria":["calm","annoyed","angry"]},
         "human":{"type":"noul","instructions":"Is the customer asking for a human agent?"}}}'
```

Expected：HTTP 200，JSON 里有 `answers.dept.choice`、`answers.anger.score`、`answers.human.noul`、`usage`。
记录：鉴权头是否就是 Bearer、`usage` 里有没有 `cost`、`model` 字段的值、耗时、`usage.input_tokens`。
若非 200：换 `X-API-Key` 头重试并记录；仍失败就停下报告用户。
用 `usage.cost / usage.input_tokens * 1e6` 算出每百万输入 token 的美元价；与 `0.042` 不同时，Task 2 的 `DEFAULTS["batch"]["input_usd_per_mtok"]` 用实测值。

- [ ] **Step 2: P2 — 准备一个只含 haiku skill 的临时插件**

```bash
mkdir -p "$SCRATCH/jevprobe/.claude-plugin" "$SCRATCH/jevprobe/skills/probe-tier"
cat > "$SCRATCH/jevprobe/.claude-plugin/plugin.json" <<'EOF'
{"name": "jevprobe", "version": "0.0.1", "description": "probe", "author": {"name": "dv"}}
EOF
cat > "$SCRATCH/jevprobe/skills/probe-tier/SKILL.md" <<'EOF'
---
name: probe-tier
description: Probe skill. Invoke only when the user explicitly asks for jevprobe:probe-tier.
model: haiku
---
Reply with the single word: switched.
EOF
```

- [ ] **Step 3: P2 — 在 Opus 会话里调用它，看模型与 transcript 形状**

```bash
cd "$SCRATCH" && claude -p --plugin-dir "$SCRATCH/jevprobe" --model opus --output-format json \
  "First invoke the Skill jevprobe:probe-tier. After it returns, run the Bash command 'echo after' and then reply 'done'." \
  > "$SCRATCH/p2.json"
SID=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['session_id'])" "$SCRATCH/p2.json")
T=$(ls ~/.claude/projects/*/"$SID".jsonl)
python3 - "$T" <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    e = json.loads(line)
    if e.get("type") not in ("user", "assistant"):
        continue
    m = e.get("message") or {}
    c = m.get("content")
    kinds = c[:60] if isinstance(c, str) else [
        (b.get("type"), b.get("name"), b.get("input")) if b.get("type") == "tool_use" else b.get("type") for b in c]
    print(e["type"], "isMeta" if e.get("isMeta") else "", m.get("model", ""), kinds)
EOF
```

Expected（通过）：Skill 调用之前的 assistant 消息是 opus 系，之后的是 haiku 系。
再跑一次 `claude -p --model opus --resume "$SID" "say hi"`，同法确认这一新轮恢复 opus。
**同时记录**：Skill 调用的 `tool_use` 是不是 `name == "Skill"`、`input` 里放 skill 名的键是不是 `skill`、值是不是 `jevprobe:probe-tier`；skill 正文是以什么形状进 transcript 的（`isMeta` 的 user 消息？tool_result？）。与 Task 4 的 `_is_tier_call` / `_starts_turn` 假设（`name == "Skill"`、`input.skill`、注入消息带 `isMeta`）不同时，Task 4 按实测改这两个函数与测试里的 `reply()` / `meta()` 构造。
**不通过**（调用后仍是 opus）：停下，告诉用户"本轮降档不可行"，等用户确认再继续；用户确认后，Task 4 改为 spec 的降级方案（注入文字只说明"本题判为简单，可委派给低档子 agent"，不发布 tier skill 与 `tier_seen.py`，Task 4、5、7 中与之相关的测试一并去掉）。

- [ ] **Step 4: P3 — 落盘 hook 的原始输入**

```bash
mkdir -p "$SCRATCH/jevprobe/hooks"
cat > "$SCRATCH/jevprobe/hooks/hooks.json" <<'EOF'
{"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "cat >> \"$HOME/jev-p3-dump.jsonl\"; echo >> \"$HOME/jev-p3-dump.jsonl\""}]}]}}
EOF
cd "$SCRATCH" && claude -p --plugin-dir "$SCRATCH/jevprobe" --output-format json \
  "Start the Bash command 'sleep 3; echo bg-finished' with run_in_background true. Wait until you are notified that it finished, then reply 'done'."
python3 -c "
import json,os
for l in open(os.path.expanduser('~/jev-p3-dump.jsonl')):
    l=l.strip()
    if l: d=json.loads(l); print(sorted(d), repr(d.get('prompt',''))[:120])
"
rm -f ~/jev-p3-dump.jsonl
```

Expected：至少两条输入——手打的那句、以及后台任务完成通知。对比两者的键与 prompt 开头。
有可区分的字段：记录字段名与取值，Task 4 的 `is_typed()` 先看该字段、再用标签规则兜底，并为该字段加一条测试。
没有：确认通知类 prompt 以 `<` 开头的 XML 风格标签起头，Task 4 用标签规则。

- [ ] **Step 5: 写结论并提交**

把 P1–P3 的结论替换进 spec 末尾"（实现计划第一个任务完成后填写。）"那一行：每个探针一小段，写实测值（HTTP 头、价格、耗时、P2 前后模型与 transcript 形状、P3 区分依据）。

```bash
git commit -m "docs(jev): 探针结论 P1–P3

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- docs/superpowers/specs/2026-10-16-jev-plugin-design.md
```

---

### Task 2: 插件骨架 + `jev_config.py`

**Files:**
- Create: `claude/jev/.claude-plugin/plugin.json`
- Create: `claude/jev/.claude-plugin/marketplace.json`
- Create: `claude/jev/scripts/jev_config.py`
- Create: `claude/jev/tests/conftest.py`
- Create: `claude/jev/tests/test_config.py`
- Modify: `shared/suites/suites.txt`
- Modify: `.githooks/pre-commit`

**Interfaces:**
- Produces（`jev_config`）：`DEFAULTS: dict`；`class ConfigError(Exception)`；`config_dir() -> Path`；`load_config() -> dict`；`read_json(path: Path, default)`；`write_json(path: Path, data) -> None`；`project_root(cwd: str) -> str`；`route_projects() -> list[str]`；`is_route_on(root: str) -> bool`；`set_route(root: str, on: bool) -> None`；`is_allowed(path: str) -> bool`；`log_path() -> Path`；`append_route_log(record: dict) -> None`；`calibrations_path() -> Path`；`question_sets_dir() -> Path`；`transcript_dir(root: str) -> Path`。
- Produces（`conftest`）：autouse fixture 隔离 `XDG_CONFIG_HOME`、`CLAUDE_CONFIG_DIR`，并删掉 `OPENROUTER_API_KEY` / `JEV_BASE_URL`；fixture `cfg_dir -> Path`；fixture `fake_jev`（属性 `url`、`requests: list[dict]`（每项 `{"path", "headers", "body"}`）、`responder: Callable[[dict], tuple[int, dict | bytes]]`）；函数 `default_answers(body) -> dict`；fixture `git_repo -> Path`（已 `git init` 的临时目录）。

- [ ] **Step 1: 写插件清单**

`claude/jev/.claude-plugin/plugin.json`：

```json
{
  "name": "jev",
  "description": "Hand judgment steps to Jev (TypeSafe's typed decision model, via OpenRouter): per-project model routing, batch classification and scoring, and code scanning.",
  "version": "0.1.0",
  "author": {
    "name": "dv"
  },
  "license": "MIT"
}
```

`claude/jev/.claude-plugin/marketplace.json`：

```json
{
  "name": "jev",
  "owner": {
    "name": "dv"
  },
  "plugins": [
    {
      "name": "jev",
      "version": "0.1.0",
      "source": "./",
      "description": "Per-project model routing, batch classification and code scanning with Jev via OpenRouter."
    }
  ]
}
```

- [ ] **Step 2: 写 conftest（假 Jev 服务与隔离）**

`claude/jev/tests/conftest.py`：

```python
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(autouse=True)
def cfg_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("JEV_BASE_URL", raising=False)
    return tmp_path / "xdg" / "jev"


def default_answers(body):
    answers = {}
    for qid, q in body["questions"].items():
        if q["type"] == "choice":
            opts = list(q["criteria"])
            answers[qid] = {"type": "choice", "choice": opts[0], "confidence": 1.0,
                            "probabilities": {o: (1.0 if i == 0 else 0.0) for i, o in enumerate(opts)}}
        elif q["type"] == "score":
            answers[qid] = {"type": "score", "score": 0.0, "confidence": 1.0, "probabilities": {"0": 1.0}}
        else:
            answers[qid] = {"type": "noul", "noul": 0.0}
    return {"model": "jev-test", "answers": answers,
            "usage": {"input_tokens": 10, "output_tokens": 1, "cost": 0.0001}}


class FakeJev:
    def __init__(self):
        self.url = ""
        self.requests = []
        self.lock = threading.Lock()
        self.responder = lambda body: (200, default_answers(body))


def _handler(fake):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with fake.lock:
                fake.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
            status, payload = fake.responder(body)
            raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass
    return Handler


@pytest.fixture
def fake_jev(monkeypatch):
    fake = FakeJev()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(fake))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    fake.url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("JEV_BASE_URL", fake.url)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-secret")
    yield fake
    server.shutdown()
    server.server_close()


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    return repo
```

- [ ] **Step 3: 写失败的测试**

`claude/jev/tests/test_config.py`：

```python
import json
import os

import pytest

import jev_config as C


def test_defaults_when_no_config_file():
    cfg = C.load_config()
    assert cfg["model"] == "~typesafe/jev-latest"
    assert cfg["route"]["threshold"] == 0.8
    assert cfg["route"]["assume_model"] is None
    assert cfg["batch"]["cost_cap_usd"] == 1.0


def test_override_keeps_sibling_defaults(cfg_dir):
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(json.dumps({"route": {"threshold": 0.5}}))
    cfg = C.load_config()
    assert cfg["route"]["threshold"] == 0.5
    assert cfg["route"]["timeout_s"] == 3.0


def test_malformed_config_raises_with_path(cfg_dir):
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text("{not json")
    with pytest.raises(C.ConfigError, match="config.json"):
        C.load_config()


def test_project_root_of_subdir_is_repo_root(git_repo):
    sub = git_repo / "a" / "b"
    sub.mkdir(parents=True)
    assert C.project_root(str(sub)) == os.path.realpath(git_repo)


def test_project_root_via_symlink_is_same_project(git_repo, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(git_repo)
    assert C.project_root(str(link)) == os.path.realpath(git_repo)


def test_project_root_outside_git_is_cwd(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert C.project_root(str(plain)) == os.path.realpath(plain)


def test_switch_is_per_project(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    C.set_route(a, True)
    assert C.is_route_on(a) and not C.is_route_on(b)
    C.set_route(a, False)
    assert not C.is_route_on(a)


def test_allowlist_matches_prefix_not_sibling(cfg_dir, tmp_path):
    data = tmp_path / "data"
    (data / "x").mkdir(parents=True)
    (tmp_path / "data2").mkdir()
    assert not C.is_allowed(str(data / "x"))
    C.write_json(cfg_dir / "allow.json", {"paths": [str(data)]})
    assert C.is_allowed(str(data / "x" / "rows.jsonl"))
    assert C.is_allowed(str(data))
    assert not C.is_allowed(str(tmp_path / "data2" / "rows.jsonl"))


def test_append_route_log_appends_lines():
    C.append_route_log({"a": 1})
    C.append_route_log({"b": "中"})
    assert [json.loads(l) for l in C.log_path().read_text(encoding="utf-8").splitlines()] == [{"a": 1}, {"b": "中"}]


def test_transcript_dir_encodes_project_path(tmp_path):
    assert C.transcript_dir("/Users/aa/workspace/my.skills") == tmp_path / "claude" / "projects" / "-Users-aa-workspace-my-skills"
```

- [ ] **Step 4: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_config.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'jev_config'`

- [ ] **Step 5: 实现 `jev_config.py`**

`claude/jev/scripts/jev_config.py`（若 Task 1 测出的价格不是 0.042，用实测值替换 `input_usd_per_mtok`）：

```python
"""Config defaults, per-project model-routing switch, outbound allowlist, and shared paths.

Everything jev writes lives under ${XDG_CONFIG_HOME:-~/.config}/jev/ — never in CLAUDE_PLUGIN_ROOT,
which is a versioned cache directory.
"""
import copy
import json
import os
import re
import subprocess
from pathlib import Path

DEFAULTS = {
    "model": "~typesafe/jev-latest",
    "base_url": "https://openrouter.ai/api",
    "retries": 3,
    "route": {
        "threshold": 0.8,
        "timeout_s": 3.0,
        "max_prompt_chars": 8000,
        "tiers": {"light": "haiku", "standard": "sonnet"},
        # Substring of a model id -> capability rank. Routing only ever moves to a lower rank.
        "model_rank": {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3},
        # Session model to assume before the first reply exists; None = never route a session's first prompt.
        "assume_model": None,
    },
    "batch": {
        "concurrency": 8,
        "sample": 20,
        "calibrate_over": 50,
        "cost_cap_usd": 1.0,
        "input_usd_per_mtok": 0.042,
        "default_threshold": 0.8,
        "noul_hi": 0.9,
        "noul_lo": 0.1,
        "long_context_bytes": 32000,
        "request_timeout_s": 30.0,
    },
}


class ConfigError(Exception):
    pass


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "jev"


def read_json(path: Path, default):
    if not path.exists():
        return copy.deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ConfigError(f"{path}: {e}") from None


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config() -> dict:
    path = config_dir() / "config.json"
    data = read_json(path, {})
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: must be a JSON object")
    return _merge(DEFAULTS, data)


def project_root(cwd: str) -> str:
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and out.stdout.strip():
            return os.path.realpath(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return os.path.realpath(cwd)


def _state_path() -> Path:
    return config_dir() / "state.json"


def route_projects() -> list[str]:
    return list(read_json(_state_path(), {"route_projects": []}).get("route_projects", []))


def is_route_on(root: str) -> bool:
    return root in route_projects()


def set_route(root: str, on: bool) -> None:
    projects = [p for p in route_projects() if p != root]
    if on:
        projects.append(root)
    write_json(_state_path(), {"route_projects": sorted(projects)})


def is_allowed(path: str) -> bool:
    target = Path(os.path.realpath(path))
    for entry in read_json(config_dir() / "allow.json", {"paths": []}).get("paths", []):
        prefix = Path(os.path.realpath(os.path.expanduser(entry)))
        if target.is_relative_to(prefix):
            return True
    return False


def log_path() -> Path:
    return config_dir() / "route-log.jsonl"


def append_route_log(record: dict) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def calibrations_path() -> Path:
    return config_dir() / "calibrations.json"


def question_sets_dir() -> Path:
    return config_dir() / "question-sets"


def transcript_dir(root: str) -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
    return Path(base) / "projects" / re.sub(r"[^A-Za-z0-9]", "-", root)
```

- [ ] **Step 6: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_config.py`
Expected: 10 passed

- [ ] **Step 7: 接进套件清单与 pre-commit**

在 `shared/suites/suites.txt` 的 `claude/grillstorm/skills/grillstorm/scripts` 一行之后加一行：

```text
claude/jev/tests
```

在 `.githooks/pre-commit` 的 `run_pytest pi/cross-exam` 一行之后加一行：

```bash
run_pytest claude/jev/tests                    # jev plugin: config, client, routing hook, batch engine (seconds)
```

Run: `python3 -m pytest -q shared/suites/test_suite_coverage.py`
Expected: 全部 passed

- [ ] **Step 8: 提交**

```bash
git add claude/jev/.claude-plugin claude/jev/scripts/jev_config.py claude/jev/tests/conftest.py claude/jev/tests/test_config.py shared/suites/suites.txt .githooks/pre-commit
git commit -m "feat(jev): 插件骨架与配置、按项目开关、外发放行

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev shared/suites/suites.txt .githooks/pre-commit
```

Expected：pre-commit 输出里能看到 `claude/jev/tests` 跑过并通过。

---

### Task 3: `jev_client.py`

**Files:**
- Create: `claude/jev/scripts/jev_client.py`
- Test: `claude/jev/tests/test_client.py`

**Interfaces:**
- Consumes: `jev_config.DEFAULTS` 的键 `model`、`base_url`、`retries`。
- Produces: `class JevError(Exception)`；`call_jev(state, questions: dict, *, model: str, base_url: str, api_key: str, timeout: float, retries: int, sleep=time.sleep) -> dict`，返回 `{"answers": dict, "usage": dict, "model": str | None}`；`make_caller(cfg: dict, *, timeout: float, retries: int | None = None, sleep=time.sleep) -> Callable[[state, questions], dict]`，没 key 时抛 `JevError`。

- [ ] **Step 1: 写失败的测试**

`claude/jev/tests/test_client.py`：

```python
import time

import pytest

import jev_config as C
from jev_client import JevError, make_caller

Q = {"is_spam": {"type": "noul", "instructions": "Is this spam?"}}


def caller(**kw):
    return make_caller(C.load_config(), timeout=kw.pop("timeout", 2.0), sleep=lambda s: None, **kw)


def test_sends_bearer_model_state_questions(fake_jev):
    out = caller()("hello", Q)
    req = fake_jev.requests[0]
    assert req["path"] == "/v1/systemone"
    assert req["headers"]["Authorization"] == "Bearer sk-test-secret"
    assert req["body"] == {"state": "hello", "model": "~typesafe/jev-latest", "questions": Q}
    assert out["answers"]["is_spam"]["noul"] == 0.0
    assert out["usage"]["cost"] == 0.0001
    assert out["model"] == "jev-test"


def test_retries_5xx_then_succeeds(fake_jev):
    from conftest import default_answers
    replies = [(503, {"error": "busy"}), (429, {"error": "slow down"})]
    fake_jev.responder = lambda body: replies.pop(0) if replies else (200, default_answers(body))
    assert "is_spam" in caller()("x", Q)["answers"]
    assert len(fake_jev.requests) == 3


def test_gives_up_after_retries(fake_jev):
    fake_jev.responder = lambda body: (503, {"error": "busy"})
    with pytest.raises(JevError, match="HTTP 503"):
        caller(retries=3)("x", Q)
    assert len(fake_jev.requests) == 4


def test_does_not_retry_other_4xx(fake_jev):
    fake_jev.responder = lambda body: (400, {"error": "bad"})
    with pytest.raises(JevError, match="HTTP 400"):
        caller()("x", Q)
    assert len(fake_jev.requests) == 1


@pytest.mark.parametrize("payload", [b"not json", {"no_answers": 1}, {"answers": []}])
def test_bad_response_is_error(fake_jev, payload):
    fake_jev.responder = lambda body: (200, payload)
    with pytest.raises(JevError):
        caller(retries=0)("x", Q)


def test_timeout_is_error(fake_jev):
    def slow(body):
        time.sleep(1.0)
        return 200, {"answers": {}}
    fake_jev.responder = slow
    started = time.monotonic()
    with pytest.raises(JevError):
        caller(timeout=0.2, retries=0)("x", Q)
    assert time.monotonic() - started < 0.9


def test_missing_key_raises():
    with pytest.raises(JevError, match="OPENROUTER_API_KEY"):
        caller()


def test_error_never_contains_key(fake_jev):
    fake_jev.responder = lambda body: (401, {"error": "bad key sk-test-secret"})
    with pytest.raises(JevError) as err:
        caller()("x", Q)
    assert "sk-test-secret" not in str(err.value)
```

- [ ] **Step 2: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_client.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'jev_client'`

- [ ] **Step 3: 实现**

`claude/jev/scripts/jev_client.py`：

```python
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
```

- [ ] **Step 4: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_client.py`
Expected: 10 passed

- [ ] **Step 5: 提交**

```bash
git add claude/jev/scripts/jev_client.py claude/jev/tests/test_client.py
git commit -m "feat(jev): Jev 调用客户端（重试、超时、不泄露 key）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev
```

---

### Task 4: 选模型 hook、tier skills、照做记录

若 Task 1 的 P2 不通过且用户已确认降级：`additionalContext` 文案改为"本题被 Jev 判为 {tier}（概率 p）。如果合适，可把它委派给 `model: {target}` 的子 agent。"，不建 `skills/tier-*`、`tier_seen.py` 与 hooks.json 的 PostToolUse 段，删掉断言 tier skill 名、`session_model` 降档轮、`tier_seen` 的测试；其余照做。
若 P2 测出的 transcript 形状与 `_is_tier_call` / `_starts_turn` 的假设不同：按实测改这两个函数，并改测试里 `reply()` / `meta()` / `tool_result()` 的构造。
若 P3 找到了可区分字段：`is_typed()` 先看该字段，再用标签规则兜底，并为该字段加一条测试。

**Files:**
- Create: `claude/jev/scripts/route.py`
- Create: `claude/jev/scripts/route_question.json`
- Create: `claude/jev/scripts/tier_seen.py`
- Create: `claude/jev/hooks/hooks.json`
- Create: `claude/jev/skills/tier-light/SKILL.md`
- Create: `claude/jev/skills/tier-standard/SKILL.md`
- Test: `claude/jev/tests/test_route.py`

**Interfaces:**
- Consumes: `jev_config.load_config/project_root/is_route_on/append_route_log/ConfigError`；`jev_client.make_caller/JevError`。
- Produces（`route`）：`TIER_SKILL_PREFIX = "jev:tier-"`；`is_typed(prompt: str) -> bool`；`model_rank(model: str | None, ranks: dict) -> int | None`；`read_tail(path) -> list[str]`；`walk_assistant(lines: list[str]) -> Iterator[tuple[dict, bool]]`（`(assistant_entry, in_routed_turn)`）；`real_model(entry: dict) -> str | None`；`session_model(transcript_path) -> str | None`；`decide(hook_input: dict, cfg: dict, ask, question: dict) -> tuple[dict | None, dict]`；`main(stdin, stdout) -> int`（永远 0）。
  路由日志行键：`ts`、`event`（`"route"`）、`session_id`、`project`、`prompt_len`、`sent`、`action`、`reason`，可选 `current_model`、`assumed_model`、`tier`、`prob`、`target`、`latency_ms`、`cost`、`error`。`reason` 取值：`not_typed`、`too_long`、`unknown_model`、`already_cheapest`、`no_key`、`error`、`bad_answer`、`heavy`、`low_confidence`、`not_lower`、`routed`。
- Produces（`tier_seen`）：`main(stdin) -> int`；写日志行 `{"ts", "event": "tier_invoked", "session_id", "project", "skill"}`。

- [ ] **Step 1: 写题目文件**

`claude/jev/scripts/route_question.json`：

```json
{
  "tier": {
    "type": "choice",
    "instructions": "This is one message a developer typed to an AI coding agent. How much model capability does handling it need?",
    "criteria": {
      "light": "A single lookup or mechanical step with no design judgment: find where a file or symbol is, show a function's parameters, convert text to a given format, rename something, answer a short factual question about the code.",
      "standard": "A routine change or explanation within a known scope: implement a small, clearly specified edit, write a test for given behavior, explain how a piece of code works, fix an obvious error with a clear message.",
      "heavy": "Needs design or deep reasoning: plan a feature, debug an unclear failure, change many files, weigh trade-offs, review a design, or anything ambiguous or open-ended."
    }
  }
}
```

- [ ] **Step 2: 写失败的测试**

`claude/jev/tests/test_route.py`：

```python
import io
import json
import time

import pytest

import jev_config as C
import route
import tier_seen
from jev_client import JevError

QUESTION = json.loads(route.QUESTION_FILE.read_text())


# ---- transcript builders (shapes confirmed by probe P2) ----

def user(text="hi"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result():
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def meta(text="skill body"):
    return {"type": "user", "isMeta": True, "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def reply(model, tier=None):
    content = [{"type": "text", "text": "..."}]
    if tier:
        content.append({"type": "tool_use", "id": "t1", "name": "Skill", "input": {"skill": f"jev:tier-{tier}"}})
    return {"type": "assistant", "message": {"model": model, "content": content}}


def write_transcript(tmp_path, entries, garbage=False):
    lines = [json.dumps(e) for e in entries]
    if garbage:
        lines.insert(1, "{broken")
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def transcript(tmp_path, *models, garbage=False):
    entries = [user()]
    for m in models:
        entries += [reply(m), user()]
    return write_transcript(tmp_path, entries, garbage)


ROUTED_TURN = [user("where is x"), reply("claude-opus-5-5", tier="light"), tool_result(), meta(),
               reply("claude-haiku-5-5")]


def answer(tier, p):
    others = {t: (1 - p) / 2 for t in ("light", "standard", "heavy") if t != tier}
    return {"answers": {"tier": {"type": "choice", "choice": tier, "confidence": p,
                                 "probabilities": {tier: p, **others}}},
            "usage": {"cost": 0.00002}, "model": "jev-test"}


class Ask:
    def __init__(self, result=None, error=None):
        self.calls, self.result, self.error = [], result, error

    def __call__(self, state, questions):
        self.calls.append(state)
        if self.error:
            raise self.error
        return self.result


def run(tmp_path, prompt, ask, models=("claude-opus-5-5",), **kw):
    hook = {"prompt": prompt, "transcript_path": transcript(tmp_path, *models, **kw)}
    return route.decide(hook, C.load_config(), ask, QUESTION)


# ---- decide() ----

def test_light_on_opus_routes_to_tier_light(tmp_path):
    out, log = run(tmp_path, "where is the deploy script?", Ask(answer("light", 0.93)))
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "jev:tier-light" in ctx and "Jev" in ctx
    assert out["systemMessage"] == "Jev → haiku (0.93)"
    assert log["reason"] == "routed" and log["target"] == "haiku"


def test_standard_on_fable_routes_to_sonnet(tmp_path):
    out, _ = run(tmp_path, "add a test", Ask(answer("standard", 0.9)), models=("claude-fable-5-1",))
    assert "jev:tier-standard" in out["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize("tier,p,reason", [("heavy", 0.99, "heavy"), ("light", 0.6, "low_confidence")])
def test_no_route(tmp_path, tier, p, reason):
    out, log = run(tmp_path, "x", Ask(answer(tier, p)))
    assert out is None and log["reason"] == reason


def test_never_routes_up_or_sideways(tmp_path):
    out, log = run(tmp_path, "x", Ask(answer("standard", 0.95)), models=("claude-sonnet-5-5",))
    assert out is None and log["reason"] == "not_lower"


def test_already_cheapest_does_not_call_jev(tmp_path):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, "x", ask, models=("claude-haiku-5-5",))
    assert out is None and ask.calls == [] and log["reason"] == "already_cheapest"


@pytest.mark.parametrize("models,garbage", [((), False), (("<synthetic>",), True), (("some-other-model",), False)])
def test_unknown_session_model_does_not_call_jev(tmp_path, models, garbage):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, "x", ask, models=models, garbage=garbage)
    assert out is None and ask.calls == [] and log["reason"] == "unknown_model"


def test_first_prompt_uses_assume_model_when_set(tmp_path, cfg_dir):
    C.write_json(cfg_dir / "config.json", {"route": {"assume_model": "claude-opus-5-5"}})
    out, log = run(tmp_path, "where is x", Ask(answer("light", 0.95)), models=())
    assert out is not None and log["assumed_model"] is True


def test_missing_transcript_is_unknown_model():
    ask = Ask(answer("light", 0.99))
    out, log = route.decide({"prompt": "x", "transcript_path": "/nope/t.jsonl"}, C.load_config(), ask, QUESTION)
    assert out is None and ask.calls == []


def test_transcript_skips_trailing_synthetic(tmp_path):
    assert route.session_model(transcript(tmp_path, "claude-opus-5-5", "<synthetic>")) == "claude-opus-5-5"


# ---- the session model is not polluted by our own routing ----

def test_routed_turn_does_not_change_session_model(tmp_path):
    assert route.session_model(write_transcript(tmp_path, ROUTED_TURN)) == "claude-opus-5-5"


def test_next_prompt_after_routed_turn_still_routes(tmp_path):
    hook = {"prompt": "rename foo to bar", "transcript_path": write_transcript(tmp_path, ROUTED_TURN)}
    out, log = route.decide(hook, C.load_config(), Ask(answer("light", 0.95)), QUESTION)
    assert out is not None and log["current_model"] == "claude-opus-5-5"


def test_user_model_switch_is_respected(tmp_path):
    path = write_transcript(tmp_path, ROUTED_TURN + [user("now on haiku"), reply("claude-haiku-5-5")])
    assert route.session_model(path) == "claude-haiku-5-5"
    ask = Ask(answer("standard", 0.99))
    out, log = route.decide({"prompt": "x", "transcript_path": path}, C.load_config(), ask, QUESTION)
    assert out is None and log["reason"] == "already_cheapest" and ask.calls == []


def test_walk_marks_replies_after_tier_call():
    lines = [json.dumps(e) for e in ROUTED_TURN]
    assert [(route.real_model(e), routed) for e, routed in route.walk_assistant(lines)] == [
        ("claude-opus-5-5", False), ("claude-haiku-5-5", True)]


# ---- what is never sent ----

@pytest.mark.parametrize("prompt", ["<task-notification>\n<task-id>1</task-id>", "  <system-reminder>hi"])
def test_non_typed_prompts_are_not_sent(tmp_path, prompt):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, prompt, ask)
    assert out is None and ask.calls == [] and log["reason"] == "not_typed"


def test_long_prompt_is_not_sent(tmp_path):
    ask = Ask(answer("light", 0.99))
    out, log = run(tmp_path, "x" * 8001, ask)
    assert out is None and ask.calls == [] and log["reason"] == "too_long"


def test_jev_error_means_no_output(tmp_path):
    out, log = run(tmp_path, "x", Ask(error=JevError("network: TimeoutError")))
    assert out is None and log["reason"] == "error" and log["sent"] is True


# ---- main(): the hook entry point ----

def hook_main(stdin_obj):
    stdout = io.StringIO()
    raw = stdin_obj if isinstance(stdin_obj, str) else json.dumps(stdin_obj)
    assert route.main(io.StringIO(raw), stdout) == 0
    return stdout.getvalue()


def test_switch_off_sends_nothing_and_logs_nothing(fake_jev, git_repo, tmp_path):
    out = hook_main({"prompt": "where is x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")})
    assert out == "" and fake_jev.requests == [] and not C.log_path().exists()


def test_switch_on_routes_and_log_has_no_prompt_text(fake_jev, git_repo, tmp_path):
    fake_jev.responder = lambda body: (200, answer("light", 0.95))
    C.set_route(C.project_root(str(git_repo)), True)
    sub = git_repo / "src"
    sub.mkdir()
    out = hook_main({"prompt": "where is the SECRET-PHRASE file", "cwd": str(sub), "session_id": "s1",
                     "transcript_path": transcript(tmp_path, "claude-opus-5-5")})
    assert json.loads(out)["systemMessage"].startswith("Jev → haiku")
    assert fake_jev.requests[0]["body"]["state"] == "where is the SECRET-PHRASE file"
    log = C.log_path().read_text()
    assert "SECRET-PHRASE" not in log
    entry = json.loads(log.splitlines()[-1])
    assert entry["event"] == "route" and entry["session_id"] == "s1"
    assert entry["project"] == C.project_root(str(git_repo))


def test_other_project_stays_off(fake_jev, git_repo, tmp_path):
    C.set_route(C.project_root(str(git_repo)), True)
    other = tmp_path / "other"
    other.mkdir()
    assert hook_main({"prompt": "x", "cwd": str(other), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""
    assert fake_jev.requests == []


def test_no_key_is_silent(git_repo, tmp_path):
    C.set_route(C.project_root(str(git_repo)), True)
    assert hook_main({"prompt": "x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""
    assert json.loads(C.log_path().read_text().splitlines()[-1])["reason"] == "no_key"


def test_slow_jev_is_silent(fake_jev, git_repo, tmp_path, cfg_dir):
    def slow(body):
        time.sleep(1.0)
        return 200, answer("light", 0.99)
    fake_jev.responder = slow
    C.write_json(cfg_dir / "config.json", {"route": {"timeout_s": 0.2}})
    C.set_route(C.project_root(str(git_repo)), True)
    assert hook_main({"prompt": "x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""


def test_malformed_config_is_silent(fake_jev, git_repo, tmp_path, cfg_dir):
    C.set_route(C.project_root(str(git_repo)), True)
    (cfg_dir / "config.json").write_text("{broken")
    assert hook_main({"prompt": "x", "cwd": str(git_repo), "transcript_path": transcript(tmp_path, "claude-opus-5-5")}) == ""
    assert fake_jev.requests == []


def test_garbage_stdin_is_silent():
    assert hook_main("not json at all") == ""


# ---- tier_seen: did Claude actually follow the suggestion ----

def test_tier_seen_logs_only_tier_skills(git_repo):
    tier_seen.main(io.StringIO(json.dumps({"tool_name": "Skill", "tool_input": {"skill": "jev:tier-light"},
                                           "session_id": "s1", "cwd": str(git_repo)})))
    tier_seen.main(io.StringIO(json.dumps({"tool_name": "Skill", "tool_input": {"skill": "jev:classify"},
                                           "cwd": str(git_repo)})))
    assert tier_seen.main(io.StringIO("garbage")) == 0
    lines = [json.loads(l) for l in C.log_path().read_text().splitlines()]
    assert len(lines) == 1
    assert {k: v for k, v in lines[0].items() if k != "ts"} == {
        "event": "tier_invoked", "session_id": "s1", "project": C.project_root(str(git_repo)), "skill": "jev:tier-light"}
```

- [ ] **Step 3: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_route.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'route'`

- [ ] **Step 4: 实现 `route.py`**

`claude/jev/scripts/route.py`：

```python
"""UserPromptSubmit hook: ask Jev how much model a typed prompt needs; when a cheaper tier
will do, ask Claude to load that tier's skill so the rest of this turn runs on it.

Never in the way: switch off, no key, error, timeout or bad config -> no output, exit 0.
The prompt text is sent to Jev but never written to the log.
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
from jev_client import JevError, make_caller  # noqa: E402

QUESTION_FILE = Path(__file__).resolve().parent / "route_question.json"
TIER_SKILL_PREFIX = "jev:tier-"
SYSTEM_TAG = re.compile(r"^\s*<[A-Za-z][\w-]*[\s>/]")
TAIL_BYTES = 512 * 1024


def is_typed(prompt: str) -> bool:
    return not SYSTEM_TAG.match(prompt)


def model_rank(model, ranks):
    if not model:
        return None
    name = model.lower()
    hits = [rank for key, rank in ranks.items() if key in name]
    return max(hits) if hits else None


def read_tail(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - TAIL_BYTES))
            return f.read().decode("utf-8", "replace").splitlines()
    except (OSError, TypeError):
        return []


def _is_tier_call(block):
    return (isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill"
            and str((block.get("input") or {}).get("skill", "")).startswith(TIER_SKILL_PREFIX))


def _starts_turn(entry):
    """A message the user actually sent — not a tool result, not a meta message Claude Code injected."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    return isinstance(content, str)


def walk_assistant(lines):
    """Yield (assistant_entry, in_routed_turn) in order. A turn is routed from the reply that
    calls a jev:tier-* skill onward, so the replies after it ran on the tier model, not the session's."""
    routed = False
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict):
            continue
        if _starts_turn(entry):
            routed = False
        elif entry.get("type") == "assistant":
            yield entry, routed
            content = (entry.get("message") or {}).get("content")
            if isinstance(content, list) and any(_is_tier_call(b) for b in content):
                routed = True


def real_model(entry):
    model = (entry.get("message") or {}).get("model")
    return model if isinstance(model, str) and model and not model.startswith("<") else None


def session_model(transcript_path):
    base = None
    for entry, routed in walk_assistant(read_tail(transcript_path)):
        if not routed and real_model(entry):
            base = real_model(entry)
    return base


def decide(hook_input, cfg, ask, question):
    rc = cfg["route"]
    ranks = rc["model_rank"]
    prompt = hook_input.get("prompt") or ""
    log = {"prompt_len": len(prompt), "sent": False, "action": "none"}
    if not is_typed(prompt):
        return None, {**log, "reason": "not_typed"}
    if len(prompt) > rc["max_prompt_chars"]:
        return None, {**log, "reason": "too_long"}
    current = session_model(hook_input.get("transcript_path"))
    if current is None and rc.get("assume_model"):
        current, log["assumed_model"] = rc["assume_model"], True
    cur_rank = model_rank(current, ranks)
    if cur_rank is None:
        return None, {**log, "reason": "unknown_model"}
    log["current_model"] = current
    tier_ranks = [r for r in (model_rank(m, ranks) for m in rc["tiers"].values()) if r is not None]
    if not tier_ranks or cur_rank <= min(tier_ranks):
        return None, {**log, "reason": "already_cheapest"}

    started = time.monotonic()
    try:
        result = ask(prompt, question)
    except JevError as e:
        return None, {**log, "sent": True, "reason": "error", "error": str(e),
                      "latency_ms": round((time.monotonic() - started) * 1000)}
    log.update(sent=True, latency_ms=round((time.monotonic() - started) * 1000),
               cost=(result.get("usage") or {}).get("cost"))

    ans = result["answers"].get("tier") or {}
    tier = ans.get("choice")
    prob = (ans.get("probabilities") or {}).get(tier)
    if not isinstance(prob, (int, float)):
        return None, {**log, "reason": "bad_answer"}
    log.update(tier=tier, prob=prob)
    target = rc["tiers"].get(tier)
    if target is None:
        return None, {**log, "reason": "heavy"}
    if prob < rc["threshold"]:
        return None, {**log, "reason": "low_confidence"}
    target_rank = model_rank(target, ranks)
    if target_rank is None or target_rank >= cur_rank:
        return None, {**log, "reason": "not_lower"}

    context = (f"[Jev 路由] Jev 判断这条请求属于 {tier} 档（概率 {prob:.2f}）。"
               f"先调用 Skill `{TIER_SKILL_PREFIX}{tier}`（本轮其余部分改用 {target}），再照原样处理用户的请求。"
               "这只是成本路由，不改变任务内容；若你判断这题其实需要更强的模型，可以不调用。")
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context},
           "systemMessage": f"Jev → {target} ({prob:.2f})"}
    return out, {**log, "action": f"tier-{tier}", "target": target, "reason": "routed"}


def main(stdin=sys.stdin, stdout=sys.stdout):
    try:
        hook_input = json.load(stdin)
        cfg = C.load_config()
        root = C.project_root(hook_input.get("cwd") or ".")
        if not C.is_route_on(root):
            return 0
        prompt = hook_input.get("prompt") or ""
        try:
            ask = make_caller(cfg, timeout=cfg["route"]["timeout_s"], retries=0)
        except JevError:
            out, log = None, {"prompt_len": len(prompt), "sent": False, "action": "none", "reason": "no_key"}
        else:
            question = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
            out, log = decide(hook_input, cfg, ask, question)
        if out:
            stdout.write(json.dumps(out, ensure_ascii=False))
        try:
            C.append_route_log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": "route",
                                "session_id": hook_input.get("session_id"), "project": root, **log})
        except OSError:
            pass
    except Exception:  # the hook must never get in the user's way
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 实现 `tier_seen.py`**

`claude/jev/scripts/tier_seen.py`：

```python
"""PostToolUse(Skill) hook: record that Claude actually loaded a jev tier skill, so /jev status
can tell suggested routes from followed ones. Silent; always exit 0."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
from route import TIER_SKILL_PREFIX  # noqa: E402


def main(stdin=sys.stdin):
    try:
        data = json.load(stdin)
        skill = str((data.get("tool_input") or {}).get("skill", ""))
        if data.get("tool_name") == "Skill" and skill.startswith(TIER_SKILL_PREFIX):
            C.append_route_log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "event": "tier_invoked", "session_id": data.get("session_id"),
                                "project": C.project_root(data.get("cwd") or "."), "skill": skill})
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_route.py`
Expected: 全部 passed（约 29 个）

- [ ] **Step 7: hooks.json 与 tier skills**

`claude/jev/hooks/hooks.json`：

```json
{
  "description": "Model routing: when /jev is on for this project, ask Jev how hard each typed prompt is and suggest a cheaper tier for this turn; record whether the tier skill was actually loaded. Silent on any failure.",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/scripts/route.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Skill",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/scripts/tier_seen.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

`claude/jev/skills/tier-light/SKILL.md`：

```markdown
---
name: tier-light
description: Switches the rest of this turn to the light-tier model. Invoke only when a "[Jev 路由]" note in this turn's context asks for jev:tier-light; never on your own.
model: haiku
---

继续照原样处理用户这一轮的请求。

做的过程中如果发现这题超出了你能稳妥处理的范围——需要设计取舍、要改多个文件、或你对结论没有把握——
停下，直接告诉用户：这一轮被 Jev 降到了较便宜的模型，建议重发这句话（下一轮会自动恢复原模型）。不要硬做。
```

`claude/jev/skills/tier-standard/SKILL.md`：

```markdown
---
name: tier-standard
description: Switches the rest of this turn to the standard-tier model. Invoke only when a "[Jev 路由]" note in this turn's context asks for jev:tier-standard; never on your own.
model: sonnet
---

继续照原样处理用户这一轮的请求。

做的过程中如果发现这题超出了你能稳妥处理的范围——需要深入设计、调试原因不明的问题、或你对结论没有把握——
停下，直接告诉用户：这一轮被 Jev 降到了较便宜的模型，建议重发这句话（下一轮会自动恢复原模型）。不要硬做。
```

- [ ] **Step 8: 提交**

```bash
git add claude/jev/scripts/route.py claude/jev/scripts/route_question.json claude/jev/scripts/tier_seen.py claude/jev/hooks claude/jev/skills/tier-light claude/jev/skills/tier-standard claude/jev/tests/test_route.py
git commit -m "feat(jev): 选模型 hook、本轮降档 skill、照做记录

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev
```

---

### Task 5: `/jev on|off|status`（含照做率与按轮 token 统计）

**Files:**
- Create: `claude/jev/scripts/jev_ctl.py`
- Create: `claude/jev/commands/jev.md`
- Test: `claude/jev/tests/test_ctl.py`

**Interfaces:**
- Consumes: `jev_config.project_root/set_route/route_projects/log_path/transcript_dir/ConfigError`；`route.walk_assistant/real_model`。
- Produces: `cmd_on(root) -> str`、`cmd_off(root) -> str`、`transcript_usage(root, since: datetime) -> dict[tuple[bool, str], list[int]]`（键 `(in_routed_turn, model)`，值 `[输入含缓存, 输出]`）、`cmd_status(root, now: datetime | None = None) -> str`、`main(argv: list[str]) -> int`。

- [ ] **Step 1: 写失败的测试**

`claude/jev/tests/test_ctl.py`：

```python
import json
from datetime import datetime, timedelta, timezone

import jev_config as C
import jev_ctl

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def log(**entry):
    C.append_route_log(entry)


def test_on_off_is_per_project(tmp_path):
    a = str(tmp_path / "a")
    msg = jev_ctl.cmd_on(a)
    assert a in msg and "原文" in msg
    assert C.is_route_on(a)
    jev_ctl.cmd_off(a)
    assert not C.is_route_on(a)


def test_status_counts_recent_entries_of_this_project(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    C.set_route(a, True)
    ts = (NOW - timedelta(days=1)).isoformat()
    old = (NOW - timedelta(days=8)).isoformat()
    log(ts=ts, event="route", project=a, sent=True, reason="routed", tier="light", target="haiku", latency_ms=200, cost=0.001)
    log(ts=ts, event="tier_invoked", project=a, skill="jev:tier-light")
    log(ts=ts, event="route", project=a, sent=True, reason="heavy", tier="heavy", latency_ms=400, cost=0.001)
    log(ts=ts, event="route", project=a, sent=True, reason="error", error="network: TimeoutError", latency_ms=3000)
    log(ts=ts, event="route", project=a, sent=False, reason="too_long")
    log(ts=old, event="route", project=a, sent=True, reason="routed", tier="light", target="haiku", latency_ms=1, cost=5.0)
    log(ts=ts, event="route", project=b, sent=True, reason="routed", tier="light", target="haiku", latency_ms=1, cost=5.0)
    out = jev_ctl.cmd_status(a, now=NOW)
    assert "本项目：开" in out
    assert "判断 3 句" in out and "未发送 1 句" in out
    assert "建议降档 1 次，照做 1 次" in out
    assert "超时 1" in out
    assert "$0.0020" in out


def test_status_reports_tokens_by_turn_kind(tmp_path):
    a = str(tmp_path / "a")
    d = C.transcript_dir(a)
    d.mkdir(parents=True)
    ts = (NOW - timedelta(hours=1)).isoformat()

    def reply(model, mid, tin, tout, tier=None):
        content = [{"type": "text", "text": "."}]
        if tier:
            content.append({"type": "tool_use", "name": "Skill", "input": {"skill": f"jev:tier-{tier}"}})
        return {"type": "assistant", "timestamp": ts, "message": {
            "id": mid, "model": model, "content": content,
            "usage": {"input_tokens": tin, "cache_read_input_tokens": 100, "output_tokens": tout}}}

    entries = [{"type": "user", "message": {"content": "where is x"}},
               reply("claude-opus-5-5", "m1", 10, 5, tier="light"),
               reply("claude-opus-5-5", "m1", 10, 5, tier="light"),  # same message id twice: counted once
               {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
               reply("claude-haiku-5-5", "m2", 20, 7),
               {"type": "user", "message": {"content": "design the cache layer"}},
               reply("claude-opus-5-5", "m3", 30, 9)]
    (d / "s.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries))
    out = jev_ctl.cmd_status(a, now=NOW)
    assert "降档轮：claude-haiku-5-5 输入 120 / 输出 7" in out
    assert "其他轮：claude-opus-5-5 输入 240 / 输出 14" in out


def test_status_without_transcripts_says_none(tmp_path):
    out = jev_ctl.cmd_status(str(tmp_path / "a"), now=NOW)
    assert "降档轮：无" in out and "其他轮：无" in out


def test_main_rejects_unknown_action():
    assert jev_ctl.main(["bogus"]) == 2
```

- [ ] **Step 2: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_ctl.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'jev_ctl'`

- [ ] **Step 3: 实现**

`claude/jev/scripts/jev_ctl.py`：

```python
"""/jev on | off | status — the per-project model-routing switch and its evidence:
how often routing was suggested vs followed, and the tokens each model actually used."""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
import route  # noqa: E402

WINDOW_DAYS = 7
INPUT_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def cmd_on(root):
    C.set_route(root, True)
    lines = [f"已在本项目打开 Jev 选模型：{root}",
             "从现在起，在这个项目里你每句手打的话，原文会经 OpenRouter 发给 Jev 判断难度（日志不记原文）。",
             "新会话的第一句不会降档（还读不出会话模型）。关闭：/jev off"]
    if not os.environ.get("OPENROUTER_API_KEY"):
        lines.append("注意：当前没有 OPENROUTER_API_KEY，设置之前不会有任何判断。")
    return "\n".join(lines)


def cmd_off(root):
    C.set_route(root, False)
    return f"已在本项目关闭 Jev 选模型：{root}"


def _parse_ts(value):
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _log_entries(root, since):
    path = C.log_path()
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        ts = _parse_ts(e.get("ts")) if isinstance(e, dict) else None
        if ts and e.get("project") == root and ts >= since:
            out.append(e)
    return out


def transcript_usage(root, since):
    usage, seen = {}, set()
    folder = C.transcript_dir(root)
    if not folder.is_dir():
        return usage
    for path in folder.glob("*.jsonl"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for entry, routed in route.walk_assistant(lines):
            msg = entry.get("message") or {}
            model, u, ts = route.real_model(entry), msg.get("usage"), _parse_ts(entry.get("timestamp"))
            if not model or not isinstance(u, dict) or not ts or ts < since:
                continue
            key = msg.get("id") or f"{path.name}:{id(entry)}"
            if key in seen:
                continue
            seen.add(key)
            slot = usage.setdefault((routed, model), [0, 0])
            slot[0] += sum(u.get(k) or 0 for k in INPUT_KEYS)
            slot[1] += u.get("output_tokens") or 0
    return usage


def _fmt_usage(usage, routed):
    items = [f"{model} 输入 {v[0]} / 输出 {v[1]}" for (r, model), v in sorted(usage.items()) if r == routed]
    return "；".join(items) or "无"


def cmd_status(root, now=None):
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=WINDOW_DAYS)
    entries = _log_entries(root, since)
    decisions = [e for e in entries if e.get("event", "route") == "route"]
    sent = [e for e in decisions if e.get("sent")]
    tiers = Counter(e.get("tier") for e in sent if e.get("tier"))
    suggested = sum(1 for e in sent if e.get("reason") == "routed")
    followed = sum(1 for e in entries if e.get("event") == "tier_invoked")
    errors = [e for e in sent if e.get("reason") == "error"]
    timeouts = sum(1 for e in errors if "Timeout" in (e.get("error") or ""))
    latencies = [e["latency_ms"] for e in sent if isinstance(e.get("latency_ms"), (int, float))]
    cost = sum(e.get("cost") or 0 for e in sent)
    usage = transcript_usage(root, since)
    enabled = C.route_projects()
    fmt = lambda c: "、".join(f"{k} {v}" for k, v in sorted(c.items())) or "无"
    return "\n".join([
        f"本项目：{'开' if root in enabled else '关'}（{root}）",
        f"已打开的项目：{', '.join(enabled) or '无'}",
        f"最近 {WINDOW_DAYS} 天：判断 {len(sent)} 句，未发送 {len(decisions) - len(sent)} 句",
        f"Jev 判档：{fmt(tiers)}",
        f"建议降档 {suggested} 次，照做 {followed} 次",
        f"失败 {len(errors) - timeouts}，超时 {timeouts}",
        f"平均延迟：{round(sum(latencies) / len(latencies)) if latencies else '-'} ms",
        f"Jev 花费：${cost:.4f}",
        "实际 token（来自本项目 transcript，输入含缓存）：",
        f"  降档轮：{_fmt_usage(usage, True)}",
        f"  其他轮：{_fmt_usage(usage, False)}",
    ])


def main(argv):
    parser = argparse.ArgumentParser(prog="/jev")
    parser.add_argument("action", choices=["on", "off", "status"])
    parser.add_argument("--cwd", default=os.getcwd())
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    root = C.project_root(args.cwd)
    try:
        print({"on": cmd_on, "off": cmd_off, "status": cmd_status}[args.action](root))
    except C.ConfigError as e:
        print(f"配置文件有问题：{e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_ctl.py`
Expected: 5 passed

- [ ] **Step 5: 写命令文件**

`claude/jev/commands/jev.md`：

````markdown
---
description: 在当前项目打开、关闭或查看 Jev 选模型（on | off | status）
argument-hint: on | off | status
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

参数是 `$ARGUMENTS`。它必须是 `on`、`off`、`status` 之一；不是的话，不运行任何命令，告诉用户用法：`/jev on | off | status`。

是的话运行：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jev_ctl.py" $ARGUMENTS --cwd "$PWD"
```

把输出原样告诉用户，不加解释。
````

- [ ] **Step 6: 提交**

```bash
git add claude/jev/scripts/jev_ctl.py claude/jev/commands claude/jev/tests/test_ctl.py
git commit -m "feat(jev): /jev on|off|status，含照做率与按轮 token 统计

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev
```

---

### Task 6: `jev_batch.py`（批量判断引擎）

外发放行检查对象是 `--source`（数据的原始来源，缺省为输入文件本身）：代码扫描时输入文件是临时切块文件，真正要放行的是代码目录。本任务同时把这一句补进 spec 的 R-16。

**Files:**
- Create: `claude/jev/scripts/jev_batch.py`
- Test: `claude/jev/tests/test_batch.py`
- Modify: `docs/superpowers/specs/2026-10-16-jev-plugin-design.md`（R-16 加一句）

**Interfaces:**
- Consumes: `jev_config.load_config/is_allowed/config_dir/calibrations_path/question_sets_dir/read_json/write_json/ConfigError`；`jev_client.make_caller/JevError`。
- Produces: `class Refused(Exception)`（属性 `code`）；`EXIT_REFUSED = 2`、`EXIT_NOT_ALLOWED = 3`；`load_rows(path) -> list[dict]`；`load_questions(path) -> tuple[dict, dict]`；`question_hash(questions, model) -> str`；`bucket_for(answers, questions, thresholds, bc) -> tuple[str, list[str]]`；`read_results(out) -> dict[str, dict]`；`read_resolutions(out) -> dict[str, dict]`（每项 `{"answers": dict, "by": str | None, "verdicts": {rule: verdict}}`）；
  `run(input_path, questions_path, out_path, *, cfg, source=None, sample=None, skip_calibration=None, confirm_cost=False, concurrency=None, ask_factory=make_caller) -> dict`；
  `approve(out_path, questions_path, cfg, *, disagree: int, notes: str, accept_reason: str | None = None) -> dict`；
  `rebucket(out_path, questions_path, cfg) -> dict`；
  `resolve(out_path, decisions_path, questions_path, cfg) -> int`；
  `save_set(questions_path, name, out_path, cfg) -> Path`；
  `export_csv(out_path, csv_path) -> int`；`hits(out_path, questions_path, cfg) -> list[dict]`；`main(argv) -> int`。
  结果行键：`id`、`qhash`、`bucket`、`reasons`、`answers`、`usage`、`model`，可选 `long_context`。
  summary（`<out>.summary.json`）键：`rows_total`、`sample`、`skip_calibration`、`rows_done`、`buckets`、`qhash`、`thresholds`、`models`、`input_tokens`、`cost_usd`、`calibrated`、`calibration`、`resolved`、`unresolved_review`、`long_context`、`rules`（每条 noul 规则 `{"hits", "confirmed", "false_positive"}`）。
  裁决文件每行：`{"id", "by": "claude"|"user", "answers": {qid: value}}` 或 `{"id", "by", "rule": qid, "verdict": "confirmed"|"false_positive"}`，可带 `note`。

- [ ] **Step 1: 写失败的测试**

`claude/jev/tests/test_batch.py`：

```python
import csv
import json

import pytest

import jev_batch as B
import jev_config as C
from conftest import default_answers

NOUL_Q = {"questions": {"spam": {"type": "noul", "instructions": "Is this spam?"},
                        "kind": {"type": "choice", "instructions": "What kind?",
                                 "criteria": {"praise": "positive", "complaint": "negative"}}},
          "thresholds": {"kind": 0.8}}


@pytest.fixture
def data(tmp_path, cfg_dir):
    d = tmp_path / "data"
    d.mkdir()
    C.write_json(cfg_dir / "allow.json", {"paths": [str(d)]})
    return d


def write_rows(path, n):
    path.write_text("".join(json.dumps({"id": f"r{i}", "state": f"row {i}"}) + "\n" for i in range(n)))
    return path


def write_q(path, spec=NOUL_Q):
    path.write_text(json.dumps(spec))
    return path


def go(data, n=10, spec=NOUL_Q, **kw):
    rows = write_rows(data / "rows.jsonl", n)
    q = write_q(data / "q.json", spec)
    return B.run(str(rows), str(q), str(data / "out.jsonl"), cfg=C.load_config(), **kw)


def paths(data):
    return str(data / "out.jsonl"), str(data / "q.json")


def summary_of(data):
    return json.loads((data / "out.jsonl.summary.json").read_text())


def kind_conf(conf):
    def responder(body):
        out = default_answers(body)
        out["answers"]["kind"]["confidence"] = conf
        return 200, out
    return responder


def spam_hits(states):
    def responder(body):
        out = default_answers(body)
        if body["state"] in states:
            out["answers"]["spam"]["noul"] = 0.97
        return 200, out
    return responder


def decisions(data, items):
    path = data / "dec.jsonl"
    path.write_text("".join(json.dumps(d) + "\n" for d in items))
    return str(path)


# ---- refusals before any request ----

def test_not_allowed_sends_nothing(fake_jev, tmp_path):
    rows = write_rows(tmp_path / "rows.jsonl", 3)
    with pytest.raises(B.Refused) as err:
        B.run(str(rows), str(write_q(tmp_path / "q.json")), str(tmp_path / "o.jsonl"), cfg=C.load_config())
    assert err.value.code == B.EXIT_NOT_ALLOWED and fake_jev.requests == []


def test_source_is_what_gets_checked(fake_jev, data, tmp_path):
    rows = write_rows(tmp_path / "chunks.jsonl", 3)  # outside the allowlist
    q = write_q(tmp_path / "q.json")
    summary = B.run(str(rows), str(q), str(tmp_path / "o.jsonl"), cfg=C.load_config(), source=str(data))
    assert summary["rows_done"] == 3
    with pytest.raises(B.Refused):
        B.run(str(rows), str(q), str(tmp_path / "o2.jsonl"), cfg=C.load_config(), source=str(tmp_path / "secret"))


@pytest.mark.parametrize("text,needle", [
    ('{"id": 1, "state": "a"}\n{bad\n', ":2:"),
    ('{"id": 1, "state": "a"}\n{"id": 1, "state": "b"}\n', "重复"),
    ('{"id": 1}\n', "state"),
    ("\n\n", "没有数据"),
])
def test_bad_rows_refused_with_line(fake_jev, data, text, needle):
    (data / "rows.jsonl").write_text(text)
    with pytest.raises(B.Refused, match=needle):
        B.run(str(data / "rows.jsonl"), str(write_q(data / "q.json")), str(data / "o.jsonl"), cfg=C.load_config())
    assert fake_jev.requests == []


def test_bad_question_type_refused(fake_jev, data):
    write_rows(data / "rows.jsonl", 2)
    q = write_q(data / "q.json", {"questions": {"x": {"type": "essay"}}})
    with pytest.raises(B.Refused, match="type"):
        B.run(str(data / "rows.jsonl"), str(q), str(data / "o.jsonl"), cfg=C.load_config())


def test_no_key_refused(data):
    with pytest.raises(B.Refused, match="OPENROUTER_API_KEY"):
        go(data)


def test_malformed_config_refused_by_main(fake_jev, data, cfg_dir, capsys):
    (cfg_dir / "config.json").write_text("{broken")
    write_rows(data / "rows.jsonl", 2)
    code = B.main(["run", "--input", str(data / "rows.jsonl"), "--questions", str(write_q(data / "q.json")),
                   "--out", str(data / "o.jsonl")])
    assert code == B.EXIT_REFUSED and "config.json" in capsys.readouterr().err
    assert fake_jev.requests == []


# ---- bucketing ----

BC = C.DEFAULTS["batch"]
QS = NOUL_Q["questions"]


@pytest.mark.parametrize("noul,expected", [(0.95, "auto"), (0.05, "auto"), (0.5, "review"), (0.9, "auto")])
def test_noul_band(noul, expected):
    answers = {"spam": {"noul": noul}, "kind": {"confidence": 0.99}}
    assert B.bucket_for(answers, QS, {}, BC)[0] == expected


def test_choice_below_threshold_is_review():
    bucket, reasons = B.bucket_for({"spam": {"noul": 0.0}, "kind": {"confidence": 0.7}}, QS, {"kind": 0.8}, BC)
    assert bucket == "review" and "kind" in reasons[0]


def test_numeric_threshold_for_noul_is_symmetric():
    assert B.bucket_for({"spam": {"noul": 0.75}, "kind": {"confidence": 1}}, QS, {"spam": 0.7}, BC)[0] == "auto"
    assert B.bucket_for({"spam": {"noul": 0.28}, "kind": {"confidence": 1}}, QS, {"spam": 0.7}, BC)[0] == "auto"
    assert B.bucket_for({"spam": {"noul": 0.5}, "kind": {"confidence": 1}}, QS, {"spam": 0.7}, BC)[0] == "review"


def test_missing_answer_is_review():
    assert B.bucket_for({"kind": {"confidence": 1}}, QS, {}, BC)[0] == "review"


# ---- calibration must leave a review record ----

def test_large_run_requires_a_sample(fake_jev, data):
    with pytest.raises(B.Refused, match="--sample"):
        go(data, n=100)
    assert fake_jev.requests == []


def test_sample_alone_is_not_enough_then_approve_unlocks(fake_jev, data):
    s = go(data, n=100, sample=20)
    assert len(fake_jev.requests) == 20 and s["sample"] is True and s["calibrated"] is False
    with pytest.raises(B.Refused, match="approve"):
        go(data, n=100)
    out, q = paths(data)
    B.approve(out, q, C.load_config(), disagree=0, notes="无")
    full = go(data, n=100)
    assert len(fake_jev.requests) == 100
    assert full["rows_done"] == 100 and full["calibrated"] is True and full["calibration"]["disagree"] == 0


def test_approve_needs_a_sample(fake_jev, data):
    go(data, n=3)
    out, q = paths(data)
    with pytest.raises(B.Refused, match="--sample"):
        B.approve(out, q, C.load_config(), disagree=0, notes="无")


def test_approve_with_disagreement_needs_reason(fake_jev, data):
    go(data, n=60, sample=20)
    out, q = paths(data)
    with pytest.raises(B.Refused, match="--accept-reason"):
        B.approve(out, q, C.load_config(), disagree=2, notes="两条把建议判成了抱怨")
    B.approve(out, q, C.load_config(), disagree=2, notes="两条把建议判成了抱怨", accept_reason="用户说可以接受")
    assert summary_of(data)["calibration"]["disagree"] == 2


def test_approve_needs_notes(fake_jev, data):
    go(data, n=60, sample=20)
    out, q = paths(data)
    with pytest.raises(B.Refused, match="--notes"):
        B.approve(out, q, C.load_config(), disagree=0, notes="  ")


def test_skip_calibration_reason_recorded(fake_jev, data):
    s = go(data, n=60, skip_calibration="用户说：直接跑")
    assert s["skip_calibration"] == "用户说：直接跑" and s["calibrated"] is False


# ---- cost, resume, question-set identity ----

def test_cost_cap(fake_jev, data, cfg_dir):
    C.write_json(cfg_dir / "config.json", {"batch": {"input_usd_per_mtok": 1_000_000}})
    with pytest.raises(B.Refused, match="--confirm-cost"):
        go(data, n=5)
    assert fake_jev.requests == []
    assert go(data, n=5, confirm_cost=True)["rows_done"] == 5


def test_resume_skips_done_and_retries_failed(fake_jev, data):
    fake_jev.responder = lambda body: (400, {}) if body["state"] == "row 3" else (200, default_answers(body))
    s = go(data, n=5)
    assert s["buckets"]["failed"] == 1
    fake_jev.responder = lambda body: (200, default_answers(body))
    s = go(data, n=5)
    assert len(fake_jev.requests) == 6 and s["buckets"].get("failed", 0) == 0


def test_changed_questions_are_a_foreign_set(fake_jev, data):
    go(data, n=3)
    other = json.loads(json.dumps(NOUL_Q))
    other["questions"]["spam"]["instructions"] = "Is this an advertisement?"
    write_q(data / "q.json", other)
    with pytest.raises(B.Refused, match="另一套题目"):
        B.run(str(data / "rows.jsonl"), str(data / "q.json"), str(data / "out.jsonl"), cfg=C.load_config())


def test_rebucket_changes_threshold_without_requests(fake_jev, data):
    fake_jev.responder = kind_conf(0.7)
    assert go(data, n=4)["buckets"] == {"review": 4}
    before = len(fake_jev.requests)
    write_q(data / "q.json", dict(NOUL_Q, thresholds={"kind": 0.6}))
    out, q = paths(data)
    assert B.rebucket(out, q, C.load_config())["buckets"] == {"auto": 4}
    B.run(str(data / "rows.jsonl"), q, out, cfg=C.load_config())  # thresholds alone: same set, nothing to redo
    assert len(fake_jev.requests) == before


def test_long_context_flagged(fake_jev, data):
    (data / "rows.jsonl").write_text(json.dumps({"id": "big", "state": "x" * 33000}) + "\n")
    s = B.run(str(data / "rows.jsonl"), str(write_q(data / "q.json")), str(data / "out.jsonl"), cfg=C.load_config())
    assert s["long_context"] == 1
    assert B.read_results(data / "out.jsonl")["big"]["long_context"] is True


def test_summary_file_written(fake_jev, data):
    go(data, n=4)
    summary = summary_of(data)
    assert summary["buckets"] == {"auto": 4} and summary["cost_usd"] == pytest.approx(0.0004)


# ---- review verdicts land in the deliverable ----

def test_resolve_review_rows_into_final_columns(fake_jev, data):
    fake_jev.responder = kind_conf(0.5)
    go(data, n=2)
    out, q = paths(data)
    dec = decisions(data, [{"id": "r0", "by": "claude", "answers": {"kind": "complaint"}}])
    assert B.resolve(out, dec, q, C.load_config()) == 1
    assert B.export_csv(out, str(data / "out.csv")) == 2
    rows = {r["id"]: r for r in csv.DictReader(open(data / "out.csv", encoding="utf-8"))}  # concurrent writes: any order
    assert rows["r0"]["final_kind"] == "complaint" and rows["r0"]["decided_by"] == "claude"
    assert rows["r1"]["final_kind"] == "" and rows["r1"]["decided_by"] == ""
    assert rows["r0"]["kind"] == "praise" and "kind_confidence" in rows["r0"]
    summary = summary_of(data)
    assert summary["resolved"] == 1 and summary["unresolved_review"] == 1


def test_auto_rows_are_decided_by_jev(fake_jev, data):
    go(data, n=2)
    out, _ = paths(data)
    B.export_csv(out, str(data / "out.csv"))
    rows = {r["id"]: r for r in csv.DictReader(open(data / "out.csv", encoding="utf-8"))}
    assert rows["r0"]["final_kind"] == "praise" and rows["r0"]["decided_by"] == "jev" and rows["r0"]["spam"] == "0.0"


def test_resolve_rejects_bad_lines_and_writes_nothing(fake_jev, data):
    go(data, n=2)
    out, q = paths(data)
    dec = decisions(data, [{"id": "r0", "by": "claude", "answers": {"kind": "praise"}},
                           {"id": "zzz", "by": "user", "answers": {"kind": "praise"}}])
    with pytest.raises(B.Refused, match=":2:"):
        B.resolve(out, dec, q, C.load_config())
    dec = decisions(data, [{"id": "r0", "by": "robot", "answers": {"kind": "praise"}}])
    with pytest.raises(B.Refused, match="by"):
        B.resolve(out, dec, q, C.load_config())
    assert not (data / "out.jsonl.resolutions.jsonl").exists()


# ---- hits, false positives, saving a question set ----

def test_hits_lists_noul_above_hi(fake_jev, data):
    fake_jev.responder = spam_hits({"row 1"})
    go(data, n=3)
    out, q = paths(data)
    assert B.hits(out, q, C.load_config()) == [{"id": "r1", "rules": ["spam"]}]


def test_false_positive_heavy_rule_blocks_save_set(fake_jev, data):
    fake_jev.responder = spam_hits({f"row {i}" for i in range(5)})
    go(data, n=10, sample=10)
    out, q = paths(data)
    cfg = C.load_config()
    B.approve(out, q, cfg, disagree=0, notes="无")
    B.resolve(out, decisions(data, [{"id": f"r{i}", "by": "claude", "rule": "spam", "verdict": "false_positive"} for i in range(4)]
                             + [{"id": "r4", "by": "claude", "rule": "spam", "verdict": "confirmed"}]), q, cfg)
    assert summary_of(data)["rules"]["spam"] == {"hits": 5, "confirmed": 1, "false_positive": 4}
    with pytest.raises(B.Refused, match="spam"):
        B.save_set(q, "spam-check", out, cfg)


def test_save_set_requires_approve_then_writes(fake_jev, data):
    go(data, n=5, sample=5)
    out, q = paths(data)
    cfg = C.load_config()
    with pytest.raises(B.Refused, match="approve"):
        B.save_set(q, "comments", out, cfg)
    B.approve(out, q, cfg, disagree=0, notes="无")
    dest = B.save_set(q, "comments", out, cfg)
    saved = json.loads(dest.read_text())
    assert dest == C.question_sets_dir() / "comments.json"
    assert saved["questions"] == NOUL_Q["questions"] and saved["calibration"]["disagree"] == 0
```

- [ ] **Step 2: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_batch.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'jev_batch'`

- [ ] **Step 3: 实现**

`claude/jev/scripts/jev_batch.py`：

```python
"""Batch judgments with Jev: the same questions for every row, bucketed by confidence.

  run       --sample N first, then the full run (above batch.calibrate_over rows the full run needs an
            approved sample). Resumable: rows already answered under the same question set are skipped,
            failed rows retried.
  approve   record that the sample was reviewed: how many judgments you disagree with, and what.
  rebucket  re-bucket stored answers under the current thresholds — no requests.
  resolve   record final verdicts (review rows, code-scan hits) next to the results.
  save-set  keep an approved question set for reuse; refused while a rule is mostly false positives.
  export    results -> CSV with final answers and who decided them.
  hits      rows where a noul answer is at or above its upper threshold.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402
from jev_client import JevError, make_caller  # noqa: E402

EXIT_REFUSED = 2
EXIT_NOT_ALLOWED = 3
TYPES = ("choice", "score", "noul")
VALUE_KEYS = ("choice", "score", "noul")
FP_MIN_VERIFIED = 4


class Refused(Exception):
    def __init__(self, message, code=EXIT_REFUSED):
        super().__init__(message)
        self.code = code


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _summary_path(out_path):
    return Path(str(out_path) + ".summary.json")


def _resolutions_path(out_path):
    return Path(str(out_path) + ".resolutions.jsonl")


def load_rows(path):
    rows, seen = [], set()
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            raise Refused(f"{path}:{n}: 不是合法 JSON") from None
        if not isinstance(row, dict) or "id" not in row or "state" not in row:
            raise Refused(f"{path}:{n}: 每行需要 id 和 state")
        rid = str(row["id"])
        if rid in seen:
            raise Refused(f"{path}:{n}: id 重复：{rid}")
        seen.add(rid)
        rows.append({"id": rid, "state": row["state"]})
    if not rows:
        raise Refused(f"{path}: 没有数据")
    return rows


def load_questions(path):
    try:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refused(f"{path}: {e}") from None
    questions = spec.get("questions") if isinstance(spec, dict) else None
    if not isinstance(questions, dict) or not questions:
        raise Refused(f"{path}: 需要非空的 questions 对象")
    for qid, q in questions.items():
        if not isinstance(q, dict) or q.get("type") not in TYPES:
            raise Refused(f"{path}: 题目 {qid} 的 type 必须是 {'/'.join(TYPES)}")
    return questions, spec.get("thresholds") or {}


def question_hash(questions, model):
    """Identity of a question set. Thresholds are deliberately excluded: retuning them re-buckets
    stored answers and never needs new requests."""
    blob = json.dumps({"q": questions, "m": model}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def _noul_band(threshold, bc):
    if isinstance(threshold, (int, float)):
        return threshold, 1 - threshold
    threshold = threshold or {}
    return threshold.get("hi", bc["noul_hi"]), threshold.get("lo", bc["noul_lo"])


def _noul_of(row, qid):
    v = ((row.get("answers") or {}).get(qid) or {}).get("noul")
    return v if isinstance(v, (int, float)) else None


def bucket_for(answers, questions, thresholds, bc):
    reasons = []
    for qid, q in questions.items():
        a = answers.get(qid)
        if not isinstance(a, dict):
            reasons.append(f"{qid}: 没有答案")
        elif q["type"] == "noul":
            hi, lo = _noul_band(thresholds.get(qid), bc)
            v = a.get("noul")
            if not isinstance(v, (int, float)) or lo < v < hi:
                reasons.append(f"{qid}: noul={v} 落在 {lo}–{hi} 之间")
        else:
            t = thresholds.get(qid, bc["default_threshold"])
            c = a.get("confidence")
            if not isinstance(c, (int, float)) or c < t:
                reasons.append(f"{qid}: confidence={c} < {t}")
    return ("review" if reasons else "auto"), reasons


def read_results(out):
    path = Path(out)
    results = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                results[rec["id"]] = rec  # last line per id wins
    return results


def read_resolutions(out):
    merged = {}
    path = _resolutions_path(out)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            m = merged.setdefault(d["id"], {"answers": {}, "by": None, "verdicts": {}})
            if d.get("answers"):
                m["answers"].update(d["answers"])
                m["by"] = d["by"]
            if d.get("verdict"):
                m["verdicts"][d["rule"]] = d["verdict"]
    return merged


def _state_bytes(state):
    return len((state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)).encode("utf-8"))


def _estimate_usd(rows, questions, bc):
    q_bytes = len(json.dumps(questions, ensure_ascii=False).encode("utf-8"))
    tokens = sum(_state_bytes(r["state"]) + q_bytes for r in rows) / 3  # ~3 UTF-8 bytes per token
    return tokens / 1_000_000 * bc["input_usd_per_mtok"]


def _pick_sample(rows, n):
    n = min(n, len(rows))
    return [rows[i * len(rows) // n] for i in range(n)]


def _calibration(qhash):
    return C.read_json(C.calibrations_path(), {}).get(qhash) or {}


def _refresh_summary(out_path, questions, thresholds, cfg, **fixed):
    path = _summary_path(out_path)
    prev = C.read_json(path, {})
    qhash = question_hash(questions, cfg["model"])
    calib = _calibration(qhash)
    results = [r for r in read_results(out_path).values() if r.get("qhash") == qhash]
    res = read_resolutions(out_path)
    buckets = {}
    for r in results:
        buckets[r["bucket"]] = buckets.get(r["bucket"], 0) + 1
    rules = {}
    for qid, q in questions.items():
        if q["type"] != "noul":
            continue
        hi = _noul_band(thresholds.get(qid), cfg["batch"])[0]
        verdicts = [m["verdicts"].get(qid) for m in res.values()]
        rules[qid] = {"hits": sum(1 for r in results if (_noul_of(r, qid) is not None and _noul_of(r, qid) >= hi)),
                      "confirmed": verdicts.count("confirmed"),
                      "false_positive": verdicts.count("false_positive")}
    summary = {**prev, **fixed,
               "rows_done": len(results),
               "buckets": buckets,
               "qhash": qhash,
               "thresholds": thresholds,
               "models": sorted({r["model"] for r in results if r.get("model")}),
               "input_tokens": sum((r.get("usage") or {}).get("input_tokens") or 0 for r in results),
               "cost_usd": round(sum((r.get("usage") or {}).get("cost") or 0 for r in results), 6),
               "calibrated": bool(calib.get("approved")),
               "calibration": calib or None,
               "resolved": len(res),
               "unresolved_review": sum(1 for r in results if r["bucket"] == "review" and r["id"] not in res),
               "long_context": sum(1 for r in results if r.get("long_context")),
               "rules": rules}
    C.write_json(path, summary)
    return summary


def run(input_path, questions_path, out_path, *, cfg, source=None, sample=None, skip_calibration=None,
        confirm_cost=False, concurrency=None, ask_factory=make_caller):
    bc = cfg["batch"]
    source = source or input_path
    if not C.is_allowed(source):
        raise Refused(f"{source} 不在外发放行清单 {C.config_dir() / 'allow.json'} 里，没有发送任何数据。",
                      EXIT_NOT_ALLOWED)
    rows = load_rows(input_path)
    questions, thresholds = load_questions(questions_path)
    qhash = question_hash(questions, cfg["model"])
    done = read_results(out_path)
    foreign = sorted({str(r.get("qhash")) for r in done.values()} - {qhash})
    if foreign:
        raise Refused(f"{out_path} 里已有另一套题目（{', '.join(foreign)}）的结果；换一个输出路径。")

    if sample:
        targets = _pick_sample(rows, sample)
    else:
        calib = _calibration(qhash)
        if len(rows) > bc["calibrate_over"] and not calib.get("approved") and not skip_calibration:
            if calib.get("sampled"):
                raise Refused("这套题目已试跑但还没 approve：逐条看样本结果，再运行 approve 记录不同意的条数与要点。")
            raise Refused(f"{len(rows)} 行超过 {bc['calibrate_over']} 行，这套题目还没试跑过。"
                          f"先用 --sample {bc['sample']} 试跑并逐条检查结果，再 approve；"
                          "用户明确同意不校准时才用 --skip-calibration \"理由\"。")
        targets = rows
    todo = [r for r in targets if r["id"] not in done or done[r["id"]]["bucket"] == "failed"]

    estimate = _estimate_usd(todo, questions, bc)
    if estimate > bc["cost_cap_usd"] and not confirm_cost:
        raise Refused(f"本次 {len(todo)} 行预计花费约 ${estimate:.2f}，超过上限 ${bc['cost_cap_usd']:.2f}；"
                      "用户确认后加 --confirm-cost 重跑。")

    if todo:
        try:
            ask = ask_factory(cfg, timeout=bc["request_timeout_s"])
        except JevError as e:
            raise Refused(str(e)) from None
        lock = Lock()
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as f:
            def work(row):
                try:
                    res = ask(row["state"], questions)
                    bucket, reasons = bucket_for(res["answers"], questions, thresholds, bc)
                    rec = {"id": row["id"], "qhash": qhash, "bucket": bucket, "reasons": reasons,
                           "answers": res["answers"], "usage": res["usage"], "model": res["model"]}
                except JevError as e:
                    rec = {"id": row["id"], "qhash": qhash, "bucket": "failed", "reasons": [str(e)],
                           "answers": {}, "usage": {}, "model": None}
                if _state_bytes(row["state"]) > bc["long_context_bytes"]:
                    rec["long_context"] = True
                with lock:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
            with ThreadPoolExecutor(max_workers=concurrency or bc["concurrency"]) as pool:
                list(pool.map(work, todo))

    if sample:
        calibrations = C.read_json(C.calibrations_path(), {})
        calibrations[qhash] = {"sampled": len(targets), "sampled_at": _now()}  # a new sample voids an old approval
        C.write_json(C.calibrations_path(), calibrations)
    return _refresh_summary(out_path, questions, thresholds, cfg, rows_total=len(rows), sample=bool(sample),
                            skip_calibration=skip_calibration)


def approve(out_path, questions_path, cfg, *, disagree, notes, accept_reason=None):
    questions, thresholds = load_questions(questions_path)
    qhash = question_hash(questions, cfg["model"])
    calibrations = C.read_json(C.calibrations_path(), {})
    entry = calibrations.get(qhash)
    if not entry or not entry.get("sampled"):
        raise Refused("这套题目还没有 --sample 试跑记录，没有可审查的样本。")
    if disagree < 0:
        raise Refused("--disagree 不能是负数")
    if not (notes or "").strip():
        raise Refused("--notes 必填：写下样本里看到的问题；没有就写“无”。")
    if disagree > 0 and not accept_reason:
        raise Refused(f"样本里有 {disagree} 条你不同意：改题目或阈值后重新试跑（改阈值可先 rebucket）；"
                      "确要接受，加 --accept-reason \"理由\"。")
    entry.update(approved=True, approved_at=_now(), disagree=disagree, notes=notes.strip(),
                 accept_reason=accept_reason)
    C.write_json(C.calibrations_path(), calibrations)
    _refresh_summary(out_path, questions, thresholds, cfg)
    return entry


def rebucket(out_path, questions_path, cfg):
    questions, thresholds = load_questions(questions_path)
    qhash = question_hash(questions, cfg["model"])
    results = read_results(out_path)
    if not results:
        raise Refused(f"{out_path}: 没有结果")
    if any(r.get("qhash") != qhash for r in results.values()):
        raise Refused(f"{out_path} 的结果来自另一套题目；rebucket 只能改阈值，不能改题目。")
    tmp = Path(str(out_path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in results.values():
            if r["bucket"] != "failed":
                r["bucket"], r["reasons"] = bucket_for(r["answers"], questions, thresholds, cfg["batch"])
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out_path)
    return _refresh_summary(out_path, questions, thresholds, cfg)


def resolve(out_path, decisions_path, questions_path, cfg):
    questions, thresholds = load_questions(questions_path)
    results = read_results(out_path)
    if not results:
        raise Refused(f"{out_path}: 没有结果")
    accepted = []
    for n, line in enumerate(Path(decisions_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        where = f"{decisions_path}:{n}:"
        try:
            d = json.loads(line)
        except ValueError:
            raise Refused(f"{where} 不是合法 JSON") from None
        if not isinstance(d, dict) or str(d.get("id")) not in results:
            raise Refused(f"{where} 结果里没有这个 id")
        if d.get("by") not in ("claude", "user"):
            raise Refused(f"{where} by 必须是 claude 或 user")
        has_answers = isinstance(d.get("answers"), dict) and bool(d["answers"])
        has_verdict = d.get("verdict") in ("confirmed", "false_positive") and d.get("rule") in questions
        if not (has_answers or has_verdict):
            raise Refused(f"{where} 需要 answers，或 rule（题目 id）+ verdict（confirmed / false_positive）")
        accepted.append({**d, "id": str(d["id"]), "at": _now()})
    with open(_resolutions_path(out_path), "a", encoding="utf-8") as f:
        for d in accepted:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    _refresh_summary(out_path, questions, thresholds, cfg)
    return len(accepted)


def save_set(questions_path, name, out_path, cfg):
    questions, thresholds = load_questions(questions_path)
    calib = _calibration(question_hash(questions, cfg["model"]))
    if not calib.get("approved"):
        raise Refused("这套题目还没 approve，不能存为题目集。")
    if not re.fullmatch(r"[\w.-]+", name):
        raise Refused("名字只能用字母、数字、下划线、点和连字符")
    summary = _refresh_summary(out_path, questions, thresholds, cfg)
    noisy = [qid for qid, s in summary["rules"].items()
             if s["confirmed"] + s["false_positive"] >= FP_MIN_VERIFIED
             and s["false_positive"] * 2 > s["confirmed"] + s["false_positive"]]
    if noisy:
        raise Refused(f"这些规则已核实的命中里误报过半，先改规则再存：{', '.join(noisy)}")
    dest = C.question_sets_dir() / f"{name}.json"
    C.write_json(dest, {"questions": questions, "thresholds": thresholds, "calibration": calib})
    return dest


def export_csv(out_path, csv_path):
    results = list(read_results(out_path).values())
    res = read_resolutions(out_path)
    qids = []
    for r in results:
        for qid in r.get("answers") or {}:
            if qid not in qids:
                qids.append(qid)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["id", "bucket"]
        for qid in qids:
            header += [qid, f"{qid}_confidence", f"final_{qid}"]
        writer.writerow(header + ["decided_by", "verdicts", "reasons"])
        for r in results:
            m = res.get(r["id"]) or {"answers": {}, "by": None, "verdicts": {}}
            line = [r["id"], r["bucket"]]
            for qid in qids:
                a = (r.get("answers") or {}).get(qid) or {}
                value = next((a[k] for k in VALUE_KEYS if k in a), "")
                final = m["answers"].get(qid, value if r["bucket"] == "auto" else "")
                line += [value, a.get("confidence", ""), final]
            decided_by = m["by"] or ("jev" if r["bucket"] == "auto" else "")
            verdicts = "; ".join(f"{k}:{v}" for k, v in sorted(m["verdicts"].items()))
            writer.writerow(line + [decided_by, verdicts, "; ".join(r.get("reasons") or [])])
    return len(results)


def hits(out_path, questions_path, cfg):
    questions, thresholds = load_questions(questions_path)
    found = []
    for r in read_results(out_path).values():
        rules = []
        for qid, q in questions.items():
            v = _noul_of(r, qid)
            if q["type"] == "noul" and v is not None and v >= _noul_band(thresholds.get(qid), cfg["batch"])[0]:
                rules.append(qid)
        if rules:
            found.append({"id": r["id"], "rules": rules})
    return found


def main(argv):
    parser = argparse.ArgumentParser(prog="jev_batch.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--input", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--source", help="数据的原始来源（放行清单检查它）；缺省为 --input")
    p.add_argument("--sample", type=int)
    p.add_argument("--skip-calibration")
    p.add_argument("--confirm-cost", action="store_true")
    p.add_argument("--concurrency", type=int)
    p = sub.add_parser("approve")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--disagree", type=int, required=True)
    p.add_argument("--notes", required=True)
    p.add_argument("--accept-reason")
    for name in ("rebucket", "hits"):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--questions", required=True)
    p = sub.add_parser("resolve")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--decisions", required=True)
    p = sub.add_parser("save-set")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("export")
    p.add_argument("--out", required=True)
    p.add_argument("--csv", required=True)
    args = parser.parse_args(argv)
    show = lambda obj: print(json.dumps(obj, ensure_ascii=False, indent=2))
    try:
        cfg = C.load_config()
        if args.cmd == "run":
            show(run(args.input, args.questions, args.out, cfg=cfg, source=args.source, sample=args.sample,
                     skip_calibration=args.skip_calibration, confirm_cost=args.confirm_cost,
                     concurrency=args.concurrency))
        elif args.cmd == "approve":
            show(approve(args.out, args.questions, cfg, disagree=args.disagree, notes=args.notes,
                         accept_reason=args.accept_reason))
        elif args.cmd == "rebucket":
            show(rebucket(args.out, args.questions, cfg))
        elif args.cmd == "resolve":
            print(f"记录了 {resolve(args.out, args.decisions, args.questions, cfg)} 条裁决")
        elif args.cmd == "save-set":
            print(f"已存：{save_set(args.questions, args.name, args.out, cfg)}")
        elif args.cmd == "export":
            print(f"{export_csv(args.out, args.csv)} 行 → {args.csv}")
        else:
            for h in hits(args.out, args.questions, cfg):
                print(json.dumps(h, ensure_ascii=False))
    except Refused as e:
        print(str(e), file=sys.stderr)
        return e.code
    except C.ConfigError as e:
        print(f"配置文件有问题：{e}", file=sys.stderr)
        return EXIT_REFUSED
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_batch.py`
Expected: 全部 passed（约 40 个）

- [ ] **Step 5: spec R-16 补一句**

在 spec 的 R-16 末尾（"……不得绕过脚本直接用 curl 等方式把数据发给 Jev。"之后）加：

```text
  放行检查的对象是 `--source`（数据的原始来源，缺省为输入文件本身）：输入文件是由别的数据转换出来的
  （如 Claude 把 CSV 转成 JSONL、代码扫描的切块文件），`--source` 必须写原始数据或代码目录的路径。
```

- [ ] **Step 6: 提交**

```bash
git add claude/jev/scripts/jev_batch.py claude/jev/tests/test_batch.py docs/superpowers/specs/2026-10-16-jev-plugin-design.md
git commit -m "feat(jev): 批量判断引擎（校准审查、调阈值、裁决落地、误报回流）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev docs/superpowers/specs/2026-10-16-jev-plugin-design.md
```

---

### Task 7: `classify` skill + 插件布局测试

**Files:**
- Create: `claude/jev/skills/classify/SKILL.md`
- Create: `claude/jev/tests/test_plugin_layout.py`

**Interfaces:**
- Consumes: `jev_batch.py` 的 CLI（`run` / `approve` / `rebucket` / `resolve` / `save-set` / `export`），退出码 2 / 3。
- Produces: `test_plugin_layout.py` 的 `frontmatter(path) -> dict`，Task 8 往里加断言。

- [ ] **Step 1: 写失败的布局测试**

`claude/jev/tests/test_plugin_layout.py`：

```python
import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def test_manifests_agree():
    plugin = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    market = json.loads((PLUGIN / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] == market["name"] == market["plugins"][0]["name"] == "jev"
    assert plugin["version"] == market["plugins"][0]["version"] == "0.1.0"


def test_hooks_point_at_existing_scripts_with_timeouts():
    hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text())["hooks"]
    prompt = hooks["UserPromptSubmit"][0]["hooks"][0]
    assert "scripts/route.py" in prompt["command"] and prompt["timeout"] == 5
    post = hooks["PostToolUse"][0]
    assert post["matcher"] == "Skill" and "scripts/tier_seen.py" in post["hooks"][0]["command"]
    assert (PLUGIN / "scripts/route.py").exists() and (PLUGIN / "scripts/tier_seen.py").exists()


def test_every_skill_has_matching_name_and_description():
    for skill in (PLUGIN / "skills").iterdir():
        fm = frontmatter(skill / "SKILL.md")
        assert fm["name"] == skill.name and fm["description"]


def test_tier_skills_set_a_model_and_an_escape_hatch():
    for name, model in (("tier-light", "haiku"), ("tier-standard", "sonnet")):
        path = PLUGIN / "skills" / name / "SKILL.md"
        assert frontmatter(path)["model"] == model
        assert "重发" in path.read_text(encoding="utf-8")


def test_jev_command_is_user_only():
    assert frontmatter(PLUGIN / "commands/jev.md")["disable-model-invocation"] == "true"


def test_route_question_has_three_tiers():
    q = json.loads((PLUGIN / "scripts/route_question.json").read_text())["tier"]
    assert q["type"] == "choice" and list(q["criteria"]) == ["light", "standard", "heavy"]


def test_classify_skill_states_its_contract():
    text = (PLUGIN / "skills/classify/SKILL.md").read_text(encoding="utf-8")
    for needle in ["--sample", "approve", "rebucket", "resolve", "save-set", "--source", "review",
                   "allow.json", "jev_batch.py", "curl"]:
        assert needle in text, needle
```

（P2 走降级方案时：删掉 `test_tier_skills_set_a_model_and_an_escape_hatch`，并从 `test_hooks_point_at_existing_scripts_with_timeouts` 删掉 PostToolUse 两行。）

- [ ] **Step 2: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_plugin_layout.py`
Expected: 只有 `test_classify_skill_states_its_contract` FAIL（`FileNotFoundError`），其余 6 个 passed

- [ ] **Step 3: 写 SKILL.md**

`claude/jev/skills/classify/SKILL.md`：

````markdown
---
name: classify
description: Batch-classify or score many records (dozens or more) that all answer the same fixed questions — pick one of N options, place on a defined scale, or yes/no probability — by sending them to Jev (TypeSafe's typed decision model, via OpenRouter). For comment/ticket/email/lead/transcript triage and similar bulk judgments. Not for a handful of items, per-item different questions, or anything that needs generated text.
---

# classify — 用 Jev 做批量判断

Jev 只做一件事：对一段数据回答事先定好选项的题，并给出概率。它便宜、快，每条独立作答，不占你的上下文。
分工是：**你出题、校准、处理拿不准的；Jev 把同一组题对每一条答一遍。** 它答得快不等于答得对——
它的价值在于把"确定的大多数"和"需要细看的少数"分开，让你的注意力只花在后者上。
整个流程是一个闭环：样本暴露题目的毛病 → 你改题目或阈值 → 再看样本 → 认可后全量 → 拿不准的由你或用户裁决、
裁决写回结果 → 调好的题目存下来给下一次用。哪一环断了，结果就只是"Jev 说的"，不是"核实过的"。

## 什么时候用，什么时候不用

用：数据有几十条以上，每条问的是同一组问题，答案能事先枚举成选项 / 分档 / 是否。
不用：只有几条（你自己判更好）；每条要问的不一样；需要写出解释、摘要或改写；需要多步推理才能下结论
（拆成几道原子题后能用就拆，拆不开就不用）。

## 前提

- `OPENROUTER_API_KEY` 已设置。没有就停下告诉用户。可以提议改由你自己判，但要明说那不是 Jev 的结果。
- 数据来源在外发放行清单 `${XDG_CONFIG_HOME:-~/.config}/jev/allow.json`（`{"paths": [...]}`）里。
  脚本退出码 3 = 不在清单里、没有发出任何数据：把路径告诉用户、说明会发给 OpenRouter 上的 Jev，
  用户同意后再把路径加进清单。**不得绕过脚本、用 curl 或别的方式把数据发给 Jev。**

## 交付验收

每一条都要满足，做不到的在交付时明说。

1. **题目**（题目文件 `{"questions": {...}, "thresholds": {...}}`，`questions` 是 Jev 原生格式）：
   每题只问一件事；`choice` 的每个选项、`score` 的每一档、`noul` 的是与否都写判定标准（`criteria`），
   不能只有标签；阈值写进 `thresholds`（choice / score 填一个数，noul 填 `{"hi", "lo"}` 或一个数）。
   开始前先看 `${XDG_CONFIG_HOME:-~/.config}/jev/question-sets/` 里有没有同类数据用过的题目。
2. **数据**：JSONL，每行 `{"id", "state"}`；`state` 只放判断需要的字段，不带无关的个人信息。
   输入是你从别的文件转换出来的，`--source` 写原始文件的路径。
3. **校准并留下记录**：超过 50 行时，先 `--sample 20` 试跑（单独的输出文件），逐条看样本结果，数出你不同意几条。
   只是阈值不合适 → 改 `thresholds` 后 `rebucket`（不花钱）；题目本身有问题 → 改题目，用新输出文件重新试跑。
   认可后运行 `approve`，如实填 `--disagree` 与 `--notes`；仍有不同意却要继续，只能在用户同意时加 `--accept-reason`（写用户原话）。
   脚本没有 approve 记录时会拒绝全量运行。`--skip-calibration "理由"` 只在用户明确同意不校准时用，理由写用户的原话。
4. **全量跑**：花费超过上限（默认 1 美元）时脚本会先拒绝并给出估算；把估算告诉用户，同意后加 `--confirm-cost`。
5. **review 桶**：每一条要么由你判、要么交给用户，**不得当作 auto 用**。裁决写成 JSONL（`{"id", "by": "claude"|"user", "answers": {题目id: 结论}}`）
   用 `resolve` 记下；summary 的 `unresolved_review` 要么是 0，要么在交付说明里列出剩下的是哪些、为什么没裁决。
6. **failed 桶**：同一命令重跑一次（脚本只重试失败的）；仍失败的列出来。
7. **交付说明**必须包含：哪些结论来自 Jev、各桶条数、阈值、校准记录（样本数、不同意数、要点）、
   review 桶怎么处理的（你判了几条、交给用户几条、还剩几条）、有没有 `long_context` 行（这些行 Jev 更慢、更不准）、
   花费（summary 的 `cost_usd`）。结果表用 `export` 出 CSV：`final_*` 是最终结论，`decided_by` 是谁定的（`jev` / `claude` / `user`）。
8. **存题目**：校准通过的题目用 `save-set` 存下来，下次同类数据直接用。

## 命令

```bash
B="${CLAUDE_PLUGIN_ROOT}/scripts/jev_batch.py"
python3 "$B" run --input rows.jsonl --questions q.json --out sample.jsonl --source <原始数据> --sample 20
python3 "$B" rebucket --out sample.jsonl --questions q.json            # 只改了阈值时
python3 "$B" approve --out sample.jsonl --questions q.json --disagree 0 --notes "无"
python3 "$B" run --input rows.jsonl --questions q.json --out out.jsonl --source <原始数据>
python3 "$B" resolve --out out.jsonl --questions q.json --decisions decisions.jsonl
python3 "$B" export --out out.jsonl --csv out.csv
python3 "$B" save-set --out out.jsonl --questions q.json --name <简短名字>
```

`run`、`approve`、`rebucket` 打印 summary（同时写到 `<out>.summary.json`）。同一输出文件可以重复 `run`：已完成的行跳过，
失败的行重试；改了题目就要换输出文件，只改阈值不用。退出码：0 成功，2 拒绝（看 stderr 的原因），3 不在放行清单。

示例题目文件：

```json
{
  "questions": {
    "kind": {"type": "choice", "instructions": "这条留言属于哪一类？",
             "criteria": {"praise": "表达满意或感谢", "complaint": "表达不满或报告问题", "suggestion": "提出改进或新功能建议", "question": "在提问，等待回答"}},
    "needs_reply": {"type": "noul", "instructions": "这条留言是否需要我们回复？",
                    "criteria": {"true": "提了问题或投诉，且没有看到我们的回复", "false": "纯表态，或已经被回复过"}}
  },
  "thresholds": {"kind": 0.8, "needs_reply": {"hi": 0.9, "lo": 0.1}}
}
```
````

- [ ] **Step 4: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_plugin_layout.py`
Expected: 7 passed

- [ ] **Step 5: 提交**

```bash
git add claude/jev/skills/classify claude/jev/tests/test_plugin_layout.py
git commit -m "feat(jev): classify skill 与插件布局测试

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev
```

---

### Task 8: `code_chunks.py` + `code-scan` skill

**Files:**
- Create: `claude/jev/scripts/code_chunks.py`
- Create: `claude/jev/skills/code-scan/SKILL.md`
- Test: `claude/jev/tests/test_chunks.py`
- Modify: `claude/jev/tests/test_plugin_layout.py`（加 code-scan 断言）

**Interfaces:**
- Consumes: `jev_config.is_allowed/config_dir`；`jev_batch.py` CLI 的 `hits` / `resolve`（裁决行带 `rule` + `verdict`）/ `save-set`。
- Produces: `tracked_files(root, pathspecs) -> list[str]`；`read_text(path, max_bytes) -> str | None`；`by_file(text) -> list[tuple[int, int]]`；`by_window(text, lines, overlap) -> list[tuple[int, int]]`；`by_grep(text, pattern, context) -> list[tuple[int, int]]`；`parse_diff(diff_text) -> list[tuple[str, int, int, str]]`；`make_row(rel, start, end, body) -> dict`；`main(argv) -> int`（输出 JSONL 到 `--out`；根目录不在放行清单时退出 3）。行号从 1 开始，区间闭合。

- [ ] **Step 1: 写失败的测试**

`claude/jev/tests/test_chunks.py`：

```python
import json
import subprocess

import pytest

import code_chunks as K
import jev_config as C

TEN = "".join(f"line {i}\n" for i in range(1, 11))


def test_by_file():
    assert K.by_file(TEN) == [(1, 10)]
    assert K.by_file("") == []


def test_by_window_overlaps_and_covers_end():
    assert K.by_window(TEN, lines=4, overlap=1) == [(1, 4), (4, 7), (7, 10)]
    assert K.by_window("a\nb\n", lines=4, overlap=1) == [(1, 2)]


def test_by_grep_merges_overlapping_context():
    text = "".join(("SECRET\n" if i in (3, 5, 10) else "x\n") for i in range(1, 13))
    assert K.by_grep(text, "SECRET", context=1) == [(2, 6), (9, 11)]
    assert K.by_grep(text, "nothing", context=1) == []


DIFF = """diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,3 +1,4 @@
 one
+two
 three
@@ -10 +11,0 @@
-gone
diff --git a/old.py b/old.py
--- a/old.py
+++ /dev/null
@@ -1 +0,0 @@
-x
"""


def test_parse_diff_new_side_ranges():
    hunks = K.parse_diff(DIFF)
    assert [(p, s, e) for p, s, e, _ in hunks] == [("src/a.py", 1, 4), ("src/a.py", 11, 11)]
    assert "+two" in hunks[0][3]


def test_make_row_id_and_header():
    row = K.make_row("src/a.py", 3, 7, "body")
    assert row["id"] == "src/a.py:3-7" and row["state"].startswith("# src/a.py (lines 3-7)\n")


@pytest.fixture
def repo(git_repo, cfg_dir):
    (git_repo / "a.py").write_text(TEN)
    (git_repo / "bin.dat").write_bytes(b"\x00\x01\x02")
    (git_repo / "big.txt").write_text("x" * 5000)
    subprocess.run(["git", "-C", str(git_repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(git_repo), "commit", "-qm", "init"], check=True)
    (git_repo / "untracked.py").write_text("SECRET\n")
    C.write_json(cfg_dir / "allow.json", {"paths": [str(git_repo)]})
    return git_repo


def rows_of(out):
    return [json.loads(l) for l in out.read_text().splitlines()]


def test_main_by_file_skips_binary_big_and_untracked(repo, tmp_path):
    out = tmp_path / "chunks.jsonl"
    assert K.main(["--root", str(repo), "--by", "file", "--max-bytes", "1000", "--out", str(out)]) == 0
    assert [r["id"] for r in rows_of(out)] == ["a.py:1-10"]


def test_main_by_hunk(repo, tmp_path):
    (repo / "a.py").write_text(TEN.replace("line 5\n", "line 5 changed\n"))
    out = tmp_path / "chunks.jsonl"
    assert K.main(["--root", str(repo), "--by", "hunk", "--base", "HEAD", "--context", "1", "--out", str(out)]) == 0
    assert [r["id"] for r in rows_of(out)] == ["a.py:4-6"]


def test_main_refuses_root_outside_allowlist(git_repo, tmp_path):
    assert K.main(["--root", str(git_repo), "--by", "file", "--out", str(tmp_path / "o.jsonl")]) == 3
    assert not (tmp_path / "o.jsonl").exists()
```

- [ ] **Step 2: 运行，确认失败**

Run: `python3 -m pytest -q claude/jev/tests/test_chunks.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'code_chunks'`

- [ ] **Step 3: 实现**

`claude/jev/scripts/code_chunks.py`：

```python
"""Cut tracked code into jev_batch.py input rows: by file, diff hunk, grep match, or fixed window.

Only files listed by `git ls-files`; binaries and files over --max-bytes are skipped.
Refuses (exit 3) when --root is not in the outbound allowlist.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_config as C  # noqa: E402

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def tracked_files(root, pathspecs):
    out = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", *pathspecs],
                         capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def read_text(path, max_bytes):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return None
    if len(raw) > max_bytes or b"\0" in raw[:8000]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def by_file(text):
    n = len(text.splitlines())
    return [(1, n)] if n else []


def by_window(text, lines, overlap):
    n = len(text.splitlines())
    ranges, start = [], 1
    while start <= n:
        end = min(start + lines - 1, n)
        ranges.append((start, end))
        if end == n:
            break
        start = end - overlap + 1
    return ranges


def by_grep(text, pattern, context):
    rx = re.compile(pattern)
    lines = text.splitlines()
    ranges = []
    for i, line in enumerate(lines, 1):
        if rx.search(line):
            s, e = max(1, i - context), min(len(lines), i + context)
            if ranges and s <= ranges[-1][1] + 1:
                ranges[-1] = (ranges[-1][0], max(ranges[-1][1], e))
            else:
                ranges.append((s, e))
    return ranges


def parse_diff(diff_text):
    hunks, path, current = [], None, None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            path = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            continue
        m = HUNK.match(line)
        if m:
            current = None
            if path is not None:
                start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
                current = [path, start, start + max(count, 1) - 1, [line]]
                hunks.append(current)
            continue
        if line.startswith("diff --git"):
            current = None
        elif current is not None:
            current[3].append(line)
    return [(p, s, e, "\n".join(body)) for p, s, e, body in hunks]


def make_row(rel, start, end, body):
    return {"id": f"{rel}:{start}-{end}", "state": f"# {rel} (lines {start}-{end})\n{body}"}


def main(argv):
    parser = argparse.ArgumentParser(prog="code_chunks.py")
    parser.add_argument("--root", required=True)
    parser.add_argument("--by", required=True, choices=["file", "window", "grep", "hunk"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--lines", type=int, default=80)
    parser.add_argument("--overlap", type=int, default=10)
    parser.add_argument("--pattern")
    parser.add_argument("--context", type=int, default=5)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--max-bytes", type=int, default=200_000)
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    if args.by == "grep" and not args.pattern:
        parser.error("--by grep needs --pattern")
    if not C.is_allowed(args.root):
        print(f"{args.root} 不在外发放行清单 {C.config_dir() / 'allow.json'} 里；没有生成切块。", file=sys.stderr)
        return 3
    rows = []
    if args.by == "hunk":
        diff = subprocess.run(["git", "-C", args.root, "diff", f"-U{args.context}", args.base, "--", *args.paths],
                              capture_output=True, text=True, check=True).stdout
        rows = [make_row(p, s, e, body) for p, s, e, body in parse_diff(diff)]
    else:
        for rel in tracked_files(args.root, args.paths):
            text = read_text(Path(args.root) / rel, args.max_bytes)
            if text is None:
                continue
            lines = text.splitlines()
            if args.by == "file":
                ranges = by_file(text)
            elif args.by == "window":
                ranges = by_window(text, args.lines, args.overlap)
            else:
                ranges = by_grep(text, args.pattern, args.context)
            rows += [make_row(rel, s, e, "\n".join(lines[s - 1:e])) for s, e in ranges]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} 块 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: 运行，确认通过**

Run: `python3 -m pytest -q claude/jev/tests/test_chunks.py`
Expected: 8 passed

- [ ] **Step 5: 写 code-scan SKILL.md**

`claude/jev/skills/code-scan/SKILL.md`：

````markdown
---
name: code-scan
description: Scan many code chunks (a whole repo, a diff, or every match of a pattern) against the same plain-language yes/no rules with Jev — semantic lint like "does this log line print a secret", "does this comment contradict the code", "does this change weaken a test" — then verify every hit yourself. Not for reviewing one file or for bug hunting that needs reasoning across files.
---

# code-scan — 用 Jev 按大白话规则扫代码

把代码切成小块，每块对同一组"是否"规则各答一次。Jev 负责在大量代码里快速圈出可疑的块；
**结论由你下**：Jev 圈出的每一块你都要打开源码确认，没确认过的不算问题。
你的确认与否定要写回结果——它们决定这条规则下次还能不能用：误报过半的规则不改就存不下来。

## 什么时候用，什么时候不用

用：规则能写成对单个代码片段的是 / 否问题，且要过的片段很多（整个仓库、一个大 diff、某个模式的全部出现处）。
不用：只看一两个文件（你直接读）；结论依赖跨文件追踪或运行时行为；规则本身需要推理才能判断。

## 前提

与 classify 相同：`OPENROUTER_API_KEY` 已设置；**代码仓库根目录**在 `${XDG_CONFIG_HOME:-~/.config}/jev/allow.json` 里
（切块脚本与批量脚本都会检查，退出码 3 = 不在清单、没有发出任何东西：告诉用户会把代码片段发给 OpenRouter 上的 Jev，
用户同意后再加）。不得绕过脚本、用 curl 或别的方式发送代码。

## 交付验收

1. **规则文件**：每条规则是一道 `noul` 题，只问一件事，写 `criteria` 说明"是"和"否"各指什么；阈值写进 `thresholds`。
   先看 `question-sets/` 里有没有现成的规则集。
2. **切块**：按规则挑切法——日志、密钥一类用 `grep`（先用模式缩小范围），注释与命名用 `window`，
   审一次改动用 `hunk`，小文件多的仓库用 `file`。切块文件放在临时目录，不要写进用户仓库。
3. **校准**：块数超过 50 时先 `--sample 20` 试跑，检查样本里的命中与漏判，调规则或阈值，`approve` 留记录。规则同 classify。
4. **全量跑**：`--source` 写仓库根目录；花费超上限时把估算告诉用户再 `--confirm-cost`。
5. **逐条确认并写回**：`hits` 列出的每一块，你都打开源码对应行确认，每条命中写一行裁决
   `{"id", "by": "claude", "rule": "<规则id>", "verdict": "confirmed"|"false_positive", "note": "一句理由"}`，用 `resolve` 记下。
   报告里只把 confirmed 的列为问题（文件、行号、规则、理由）；false_positive 单独列为"Jev 误报"并计数。
6. **review 桶**（落在上下阈值之间的块）：说明条数；数量少就逐条看并同样写裁决，多就按规则抽查，写明抽查了多少。
7. **交付说明**：规则清单、切法、块数、各桶条数、每条规则的命中 / 确认 / 误报（summary 的 `rules`）、review 怎么处理的、花费。
   本 skill 只报告，不改代码；修不修由用户决定。
8. **存规则**：值得复用的规则集用 `save-set` 存；脚本拒存时（某条规则已核实 ≥ 4 次且误报过半），先改那条规则。

## 命令

```bash
K="${CLAUDE_PLUGIN_ROOT}/scripts/code_chunks.py"
B="${CLAUDE_PLUGIN_ROOT}/scripts/jev_batch.py"
python3 "$K" --root <repo> --by grep --pattern 'log|print' --context 3 --out <tmp>/chunks.jsonl
python3 "$B" run --input <tmp>/chunks.jsonl --questions rules.json --out <tmp>/sample.jsonl --source <repo> --sample 20
python3 "$B" approve --out <tmp>/sample.jsonl --questions rules.json --disagree 0 --notes "无"
python3 "$B" run --input <tmp>/chunks.jsonl --questions rules.json --out <tmp>/scan.jsonl --source <repo>
python3 "$B" hits --out <tmp>/scan.jsonl --questions rules.json
python3 "$B" resolve --out <tmp>/scan.jsonl --questions rules.json --decisions <tmp>/verdicts.jsonl
python3 "$B" save-set --out <tmp>/scan.jsonl --questions rules.json --name <简短名字>
```

切法参数：`--by file|window|grep|hunk`；`window` 用 `--lines 80 --overlap 10`；`grep` 用 `--pattern <正则> --context N`；
`hunk` 用 `--base <git 引用> --context N`；可在末尾加路径限定范围。块的 id 是 `路径:起始行-结束行`。

示例规则文件：

```json
{
  "questions": {
    "logs_secret": {"type": "noul", "instructions": "这段代码是否把密钥、token、密码或完整卡号写进了日志或打印输出？",
                    "criteria": {"true": "日志 / print 的参数里直接或间接包含凭据或卡号", "false": "没有日志，或日志内容不含凭据"}},
    "stale_comment": {"type": "noul", "instructions": "这段代码里是否有注释描述的行为与代码实际行为不符？",
                      "criteria": {"true": "注释说的和代码做的对不上", "false": "注释与代码一致，或没有注释"}}
  },
  "thresholds": {"logs_secret": {"hi": 0.8, "lo": 0.1}, "stale_comment": {"hi": 0.9, "lo": 0.1}}
}
```
````

- [ ] **Step 6: 布局测试加 code-scan 断言**

在 `claude/jev/tests/test_plugin_layout.py` 末尾追加：

```python
def test_code_scan_skill_states_its_contract():
    text = (PLUGIN / "skills/code-scan/SKILL.md").read_text(encoding="utf-8")
    for needle in ["code_chunks.py", "hits", "resolve", "false_positive", "save-set", "--source", "误报",
                   "allow.json", "curl"]:
        assert needle in text, needle
```

Run: `python3 -m pytest -q claude/jev/tests`
Expected: 全部 passed

- [ ] **Step 7: 提交**

```bash
git add claude/jev/scripts/code_chunks.py claude/jev/skills/code-scan claude/jev/tests/test_chunks.py claude/jev/tests/test_plugin_layout.py
git commit -m "feat(jev): 代码切块与 code-scan skill

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- claude/jev
```

---

### Task 9: 文档、真实环境验收、本机安装

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/superpowers/specs/2026-10-16-jev-plugin-design.md`（"探针结论"一节追加验收结果）

- [ ] **Step 1: 改根 CLAUDE.md**

Directory Structure 代码块里 `│   └── grillstorm/` 一行改为：

```text
│   ├── grillstorm/
│   └── jev/                  # Jev (TypeSafe decision model via OpenRouter): model routing, batch classify, code scan
```

"Installing Plugins" 的 Claude Code 段里，`Optional: claude/grillstorm → grillstorm@grillstorm.` 那一段之后加：

```text
Optional: `claude/jev` → `jev@jev` (needs `OPENROUTER_API_KEY`). `/jev on|off|status` toggles per-project model routing (off by default; status shows suggested vs followed routes and tokens per model); `classify` and `code-scan` are model-invoked skills. Config and state live in `${XDG_CONFIG_HOME:-~/.config}/jev/`; outbound data must be listed in `allow.json` there.
```

"External Service Keys" 表的 OpenRouter 一行，`Used By` 列改为 `meta-skill capabilities, jev`，`Purpose` 列改为 `Cross-model XV + image generation (GPT-5 Image); Jev decisions`。

- [ ] **Step 2: 全量测试与套件覆盖**

Run: `python3 -m pytest -q claude/jev/tests shared/suites/test_suite_coverage.py`
Expected: 全部 passed

- [ ] **Step 3: 以 --plugin-dir 装上真插件验收选模型（两轮）**

```bash
claude plugin list 2>/dev/null | grep -i 'jev@' && echo "已装同名插件会遮住 --plugin-dir：先停下问用户" || true
cd "$SCRATCH" && mkdir -p routecheck && cd routecheck && git init -q
JEV=/Users/aa/workspace/myskills/claude/jev
python3 "$JEV/scripts/jev_ctl.py" on --cwd "$PWD"
claude -p --plugin-dir "$JEV" --model opus --output-format json "Say hello in one word." > turn1.json
SID=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['session_id'])" turn1.json)
claude -p --plugin-dir "$JEV" --model opus --resume "$SID" --output-format json \
  "In this directory, list the files (there may be none) and reply with the count." > turn2.json
claude -p --plugin-dir "$JEV" --model opus --resume "$SID" --output-format json \
  "What is today's date? Reply in one line." > turn3.json
python3 "$JEV/scripts/jev_ctl.py" status --cwd "$PWD"
python3 "$JEV/scripts/jev_ctl.py" off --cwd "$PWD"
```

Expected：
- 第 1 轮：日志 `reason` 为 `unknown_model`（新会话第一句不降）。
- 第 2、3 轮：日志里有判档；判为 light 时 `status` 的"建议降档"与"照做"都加 1，"降档轮"出现 haiku 系的 token。
- **第 3 轮仍能被判档和降档**——这验证会话模型没有被第 2 轮的降档污染。
记录实际判档、是否降档、照做次数、延迟、花费与 token 分布。没有降档时照实记录原因（日志 `reason`），不改代码去凑结果。

- [ ] **Step 4: 真实批量样例（30 条，走完整闭环）**

用本仓库最近 30 条提交信息做样例（是用户自己的仓库；临时目录加进放行清单，跑完再移除）：

```bash
W="$SCRATCH/batchcheck"; mkdir -p "$W"; B=/Users/aa/workspace/myskills/claude/jev/scripts/jev_batch.py
git -C /Users/aa/workspace/myskills log -30 --format='%h%x09%s' | python3 -c "
import json,sys
for line in sys.stdin:
    h, s = line.rstrip('\n').split('\t', 1)
    print(json.dumps({'id': h, 'state': s}, ensure_ascii=False))" > "$W/rows.jsonl"
cat > "$W/q.json" <<'EOF'
{"questions": {"kind": {"type": "choice", "instructions": "What kind of change does this commit message describe?",
  "criteria": {"feature": "adds new capability", "fix": "fixes a defect", "docs": "documentation or spec only", "chore": "version bump, tooling, refactor without behavior change"}}},
 "thresholds": {"kind": 0.8}}
EOF
python3 - "$W" <<'EOF'
import json, os, sys
p = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "jev", "allow.json")
data = json.load(open(p)) if os.path.exists(p) else {"paths": []}
data["paths"].append(sys.argv[1]); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(data, open(p, "w"), indent=2)
EOF
python3 "$B" run --input "$W/rows.jsonl" --questions "$W/q.json" --out "$W/sample.jsonl" --sample 10
python3 "$B" run --input "$W/rows.jsonl" --questions "$W/q.json" --out "$W/out.jsonl"
```

然后：
- 逐条看 `sample.jsonl`，数出不同意的条数，运行 `approve`（如实填 `--disagree` / `--notes`）。
- 若 `out.jsonl` 有 review 行，逐条判，写 `decisions.jsonl`，运行 `resolve`；`export` 出 CSV，确认 `final_kind` 与 `decided_by` 齐全、summary 的 `unresolved_review` 为 0。
- 跑完从 `allow.json` 里删掉 `$W` 这一项。

Expected：summary 里 `rows_done` 30，`cost_usd` 与 Task 1 的单价量级一致。记下不同意条数与 review 条数。

- [ ] **Step 5: 记录验收结果并提交**

在 spec 的"探针结论"一节末尾加"验收"小节：选模型三轮实测（每轮的 `reason`、判档、是否降档、照做、token 分布、花费）、批量样例（样本不同意数、各桶条数、review 裁决数、总花费）。

```bash
git commit -m "docs(jev): CLAUDE.md 安装说明与真实环境验收结果

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- CLAUDE.md docs/superpowers/specs/2026-10-16-jev-plugin-design.md
```

- [ ] **Step 6: 本机安装与更新命令（问过用户再执行）**

先运行 `claude plugin --help` 与 `claude plugin marketplace --help`，按当时列出的子命令确认下面的写法。把这几条命令给用户，**用户同意后**再执行安装：

```bash
claude plugin marketplace add /Users/aa/workspace/myskills/claude/jev
claude plugin install jev@jev
# 改版后：先改 plugin.json 与 marketplace.json 的 version，再
claude plugin marketplace update jev
claude plugin update jev@jev
```

装好后提醒用户：重启 `claude`；在想用的项目里 `/jev on`；`/jev status` 看效果。
