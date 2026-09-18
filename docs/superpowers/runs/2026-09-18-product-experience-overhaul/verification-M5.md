# M5 全量验证与基线对比

status: pass

run: `2026-09-18-product-experience-overhaul` · 分支 `product-experience-overhaul` · 被测 HEAD `08c31984`
基线: `6a59fe44`（`test(pi): 补宿主侧核查——模型解析链与外部 CLI 的实际模型归属`）——1198 passed / 4 failed（meta-skill 全量），superstorm 255 passed
执行: 2026-09-18，逐条串行，一次只跑一个。解释器 `python3` = CPython 3.14.7（`/opt/homebrew/opt/python@3.14`），pytest 9.0.3。
下表为在 `08c31984` 上的运行结果（订正后的十五段，全段 rc=0，`OVERALL_RC=0`）；同一 HEAD 上把验收命令原串
（十五段用 `&&` 串起来的那一条）又整串跑了一遍，`ACCEPTANCE_RC=0`，meta-skill 全量同样是 4 failed / 1297 passed、`unexpected: []`，
其余各套件通过数与下表逐一相同。
先前两轮（`4d9e666f`、`d2e94dbf`）结论相同，数字与本轮逐一一致。`4d9e666f → 08c31984` 之间落地的三个提交里，
只有 `08c31984` 碰到被测文件（`claude/meta-skill/tests/prompts/domain-codex.md` 一行夹具文本），其余两个只动本文件与 run 台账；
该夹具本轮已随 meta-skill 全量一并跑过。
本文件自身的留档提交只动本文件，不动被测源码，故"被测 HEAD"始终记运行时的那个 commit。
原始输出: `docs/superpowers/runs/2026-09-18-product-experience-overhaul/logs/T-M5-14.log`（`08c31984` 本轮输出，
每段末尾带 `RESULT <label> rc=0 dur=…`，结尾 `OVERALL_RC=0`）

## 逐条结果

R-M5-05 的九条（C1–C9，其中第六条按仓库惯例拆为 C6a/C6b/C6c 三次调用，见下节）
+ 规格"验收"两条（A1–A2）+ 两条跨模块不变量（I1–I2）。

| # | 命令 | 退出码 | passed / failed | 耗时 |
|---|---|---|---|---|
| C1 | `python3 -m pytest -q -rfE claude/meta-skill/tests/unit` | 1（基线四个；验收包装器 exit 0） | 1297 passed / 4 failed | 359.9s |
| C2 | `python3 -m pytest -q claude/superstorm/scripts` | 0 | 255 passed / 0 failed | 6.7s |
| C3 | `python3 -m pytest -q codex/cross-exam-skill/scripts` | 0 | 172 passed / 0 failed | 6.8s |
| C4 | `python3 -m pytest -q shared/evidence-engine` | 0 | 46 passed / 0 failed | 3.8s |
| C5 | `python3 -m pytest -q shared/visual-acceptance` | 0 | 211 passed / 0 failed | 3.4s |
| C6a | `python3 -m pytest -q shared/scripts/orchestrator` | 0 | 144 passed / 0 failed | 10.9s |
| C6b | `python3 -m pytest -q shared/keep-code-simple` | 0 | 14 passed（+40 subtests）/ 0 failed | 0.4s |
| C6c | `python3 -m pytest -q pi/cross-exam` | 0 | 7 passed / 0 failed | 0.2s |
| C7 | `python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py codex/meta-skill/test_install.py` | 0 | 202 passed（+21 subtests）/ 0 failed | 44.9s |
| C8 | `python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py` | 0 | `{"passed": true, "errors": [], "warnings": []}` | <0.1s |
| C9 | `python3 claude/superstorm/scripts/check_skill_refs.py` | 0 | `OK: all 33 referenced files present` | <0.1s |
| A1 | `python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py` | 0 | 6 passed / 0 failed | 2.6s |
| A2 | `python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py` | 0 | 11 passed / 0 failed | 0.2s |
| I1 | `grep -rn "experience_priority" claude/meta-skill/knowledge \| grep -v "experience_priority.mode" \| grep -v bootstrap` | 1（无输出，期望为空） | — | <0.1s |
| I2 | `python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py` | 0 | 无输出 | 0.1s |

十三条命令全部符合预期，无一条非预期退出码，无收集错误。

## meta-skill 全量：失败用例 id 与基线逐一比对

C1 用 `-rfE` 取到的失败/错误 node id 集合，共 4 个，无 `ERROR` 行（即无收集错误）：

| # | 失败用例 id | 在基线四个之内 |
|---|---|---|
| 1 | `claude/meta-skill/tests/unit/test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude]` | 是 |
| 2 | `claude/meta-skill/tests/unit/test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[codex]` | 是 |
| 3 | `claude/meta-skill/tests/unit/test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude]` | 是 |
| 4 | `claude/meta-skill/tests/unit/test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[codex]` | 是 |

差集 `失败集合 - 基线四个` 为空（C1 包装器打印 `unexpected: []`）：`失败集合 ⊆ 基线四个` 成立，
且两侧元素个数相同，即失败集合 == 基线四个；第五个失败不存在。四个用例本轮未被触碰。

**基线变化。** 无。四个既有失败在本轮仍全部失败（`test_evidence_freshness` 两例的首段仍是
`assert ready.returncode == 1 and 'stale_evidence' in ready.stdout` → `assert (0 == 1)`），没有一个转为通过。

**通过数增量（相对基线 `6a59fe44`）。**

| 套件 | 基线 | 本轮 | 增量 |
|---|---|---|---|
| `claude/meta-skill/tests/unit` | 1198 passed / 4 failed | 1297 passed / 4 failed | +99 passed，失败数不变 |
| `claude/superstorm/scripts` | 255 passed | 255 passed | ±0 |

## 跨模块不变量

- **I1（M1 的不变量在最终文本上复核）。** M2、M3、M4 都往 `claude/meta-skill/knowledge/` 写过字，
  改完之后重新 grep：除 `experience_priority.mode` 与 bootstrap 侧的出现之外，`knowledge/` 里没有
  任何 `experience_priority` 的裸引用。grep 无输出（退出码 1 即"期望为空"成立）。
- **I2。** `validate_meta_contracts.py` exit 0：M1/M3/M4 三个新钉住的契约函数同时成立。

## R-M5-05 第六条的命令形状订正（不是本轮回归）

规格与计划里第六条原写作一次调用三个目录：

```bash
python3 -m pytest -q shared/scripts/orchestrator shared/keep-code-simple pi/cross-exam
```

这条在收集阶段就中断（退出码 2，0 collected）：

```
ERROR collecting pi/cross-exam/test_contract.py
import file mismatch:
imported module 'test_contract' has this __file__ attribute:
  /Users/aa/workspace/myskills/shared/keep-code-simple/test_contract.py
which is not the same as the test file we want to collect:
  /Users/aa/workspace/myskills/pi/cross-exam/test_contract.py
```

`shared/keep-code-simple/test_contract.py` 与 `pi/cross-exam/test_contract.py` 同名且两个目录都没有
`__init__.py`，pytest 默认的 `prepend` 导入模式下同一次调用里只能导入其中一个。判定为命令形状缺陷而非回归，依据：

- 两个文件在基线 `6a59fe44` 就都已存在（`git ls-tree 6a59fe44` 各有 blob），本轮未改动任何一个，
  交换两个目录的顺序报错也对称出现（先收集到哪个，另一个就报 mismatch）；清掉 `__pycache__` 后复现依旧，是确定性冲突。
- 仓库对同名测试文件的既有惯例就是**一次一个目录**：`.githooks/pre-commit:25` 写着
  `# the two test_render_report.py collide: one dir per run`，
  `docs/superpowers/plans/2026-09-18-review-alignment-plan.md:25` 也写着"always as separate pytest invocations"，
  并且把 `pi/cross-exam/test_contract.py` 单独成条调用。
- 按该惯例分三次调用，三个目录全部 exit 0（C6a/C6b/C6c，合计 165 passed + 40 subtests），无失败、无收集错误。

**已应用的订正。** 本轮把 R-M5-05 第六条与 T-M5-14 验收串中的对应一段改为三次调用：

```bash
python3 -m pytest -q shared/scripts/orchestrator && python3 -m pytest -q shared/keep-code-simple && python3 -m pytest -q pi/cross-exam
```

落在 `docs/superpowers/specs/2026-09-18-regression-parity-design.md`（R-M5-05 命令组）与
`docs/superpowers/plans/2026-09-18-regression-parity-plan.md`（T-M5-14 Acceptance）两处。
订正只改调用形状，不改任何被测文件，覆盖的目录与断言强度不变；不订正则该条恒为退出码 2，与被测代码无关。
编排侧已按决定 D-0003 采纳同一形状（见 `decision-ledger.json` 与提交 `8ba4eb00`），本轮跑的就是订正后的十五段。

## 结论

- meta-skill 全量失败集合 == 基线四个，通过数 1297 ≥ 1198，无收集错误。
- 其余套件与两条不变量全部符合预期，十三条命令逐条 exit 码均为预期值。
- 未出现第五个失败，未出现基线变化，四个既有失败未被触碰。
- 订正后的验收命令原串在 `08c31984` 上整串跑通（`ACCEPTANCE_RC=0`），与逐段结果一致。

status: pass
