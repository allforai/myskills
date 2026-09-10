# Keep code simple — src

## 范围与证据限制

- Repo/cwd：`/private/var/folders/yk/1lzd8nn12m50n2l4gd8r28340000gp/T/keep-code-simple-native-2v5evcm7/codex`；分支 `main`；提交 `1d238237ed144ea9c8f091c50470556681f3e507`；调查时间 2026-09-10（Asia/Singapore）。工作区摸底与复核均只显示未跟踪的 `.agents/`，`src` 未显示改动，没有版本漂移证据。
- 加载的入口：`.agents/skills/cross-exam/keep-code-simple/SKILL.md`；执行协议：`.agents/skills/cross-exam/keep-code-simple/protocol.md`。未加载或调用 cross-exam、product-review、meta-skill。
- 明确需求来源：`README.md:5-9`。契约证据：`src/tests/test_contracts.py:13-19`（仅阅读）。README 明确这是合成 fixture、没有真实客户/凭证/网关、没有用量指标、只依赖 Python 标准库。
- 已深入三个独立业务分区：Catalog（`src/catalog/export.py`、`src/catalog/history.py`、`src/shared/tabular.py` 及 CSV 契约）、Search（`src/search/query.py` 及查询契约）、Billing（`src/billing/collect.py` 的入口→外部扣款→账本写入→失败/重试链路）。全库其余源文件均作为跨区复用/冲突背景读取。
- 仅枚举：项目文件地图、依赖/指导文件名、调用方与同类符号分布。未查：外部调用方、真实网关/存储、部署与并发模型、生产用量、失败率、金额、运营恢复流程；项目没有提供这些材料。
- 排除：`.git/` 内部内容、生成物、vendor、缓存、二进制与秘密文件；未发现依赖清单或锁文件。没有访问外部资料。
- 静态审查；未执行项目、测试、构建、安装、脚本、迁移、业务请求或实验，未修改源码/配置。测试文件导入即写 `REVIEW_EXECUTED_TESTS`，本次没有执行它。
- 派发能力预检确认宿主提供 `spawn_agent`、等待/结果回收及逐任务 `model` 参数。摸底后实际并发启动并收齐 3 个 fresh-context、只读任务（主会话之外）：Catalog，requested `gpt-5.6-luna`/medium；Search，requested `gpt-5.6-luna`/medium；Billing 高影响复核，requested `gpt-6-astra`/high。三项状态均完成；宿主未向任务或主会话返回可观察的 resolved 精确型号，故 resolved 均记未知。任务未继承作者对话、未递归派发；共享并发上限 4（3 个调查任务 + 主会话）。

## 建议

### S1 — Catalog 统一复用共享 `write_csv`

- 类型：实现等价；依据：已查证。
- 现状与证据：`src/catalog/export.py:1-11` 手写 CSV 转义；`src/catalog/history.py:1-5` 已使用 `src/shared/tabular.py:5-8` 的 `write_csv`。`README.md:5` 明确要求保留字段内逗号、引号和换行，并称现有导出使用共享接口；`src/tests/test_contracts.py:14-16` 要求两个导出结果相等。全 `src` 搜索 `write_csv|export_catalog|export_history|csv.writer|StringIO`，未发现第三套实现或更多调用方。
- 推荐方案：让 `export_catalog(rows)` 直接返回共享 `write_csv(rows)`，删除本地序列化循环。标准库 `csv.writer` 已是项目现成实现，不新增依赖；相较保留现状，可消除两套 CSV 规则的维护分叉。
- 商业功能：保留 CSV 对逗号、引号、CR/LF 的编码、CRLF 行终止、`None` 空字段及普通值字符串化。没有证据表明 Catalog 需要独立格式策略；极端自定义对象、异常类型与迭代器边界行为未运行验证。用户量与频率未知。
- 净收益与代价：预计删除 `export.py` 的局部转义与组装实现，减少认知和测试维护；迁移只涉及现有共享接口。净减行数未实测。
- 数据/资金/安全：不涉及外部写入、资金、权限或账号隔离；输出数据完整性是明确需求，不能删除 CSV 防护。公式注入等下游策略不在现有证据范围，本建议不改变它。
- 验证方法：未来验证逗号、引号、`\r`、`\n`、`None`、数字、多行及异常边界，并运行现有契约；本次未执行。
- 关联：无。
- 选择：A 复用共享 `write_csv`（推荐） / B 保留现状 / C 暂缓并先验证边界行为。

### S2 — Search 用 `strip().lower()` 表达既有规则

- 类型：实现等价；依据：已查证（异常/自定义字符串边界为条件性限制）。
- 现状与证据：`src/search/query.py:1-6` 用两个逐字符循环删除两端 `str.isspace()` 字符，再转小写；`README.md:6` 明确要求仅删除外部空白并保留内部空白；`src/tests/test_contracts.py:18-19` 覆盖内部双空格。全 `src` 搜索 `normalize_query|strip|lower|isspace`，没有其他规范化实现或调用方。
- 推荐方案：替换为 `return query.strip().lower()`。这是 Python 标准字符串的熟悉写法，不新增抽象或依赖；与保留两个切片循环相比，意图更直接。
- 商业功能：保留两端 Unicode 空白删除、内部空白与顺序、转小写。可能减少的仅是自定义 `str` 子类逐项访问/异常等未承诺行为；若业务依赖此类行为，应保留或先验证。用户量与频率未知。
- 净收益与代价：预计删除两个循环及重复边界判断，调用方和配置无迁移；净减行数未实测。
- 数据/资金/安全：没有写入、外部副作用或资金链路。主要风险是搜索匹配语义；内部空白契约必须保留。
- 验证方法：未来验证空串、全空白、Unicode 两端空白、内部连续空白、大小写与非字符串/自定义字符串边界；本次未执行。
- 关联：无。
- 选择：A 改为 `strip().lower()`（推荐） / B 保留现状 / C 暂缓并先验证边界行为。

## 安全发现与未决限制

- **同一发票更换请求键可能重复扣款。** `src/billing/collect.py:3-5` 只按 `request_key` 查账本，随后直接扣款；而 `README.md:7` 明确承诺一张发票最多收款一次。项目没有证据表明网关会按发票去重。未来需验证同发票不同请求键、并发请求及金额变化，并明确发票唯一性在哪层强制。不能提供“接受重复扣款风险”的简化选项。
- **扣款成功与记账成功之间存在未恢复窗口。** `src/billing/collect.py:5-10` 先调用外部扣款再写账本；账本写失败或扣款响应丢失时，异常并不撤销已发生的副作用。项目没有恢复、结果查询、补录或“结果未知”终态证据；同键重试是否安全依赖未知的网关幂等期限、键作用域和返回行为。未来需验证扣款后记账失败、响应丢失、同键/并发重试和幂等过期。在证明底线前应保留现有账本短路、`idempotency_key` 与记录写入，不把它们列为简化候选。
- 同一 `request_key` 搭配不同发票/金额会直接返回旧记录；键的唯一性与参数绑定责任没有文档。README 的“prior receipt”和函数返回整个记录之间也缺少调用方/测试以判定契约。Billing 在已枚举测试中没有覆盖。
- Billing 没有值得正式推荐的简单化项：删除防重、外部幂等参数或对账记录均违反明确需求或削弱尚未证明安全的失败链路；引入通用重试器/事务包装也没有复用收益，且不能回滚外部扣款。
- 以上资金与记录风险不因 fixture 无真实资金或没有用量数据而被豁免。它们是静态发现，不代表已在运行中复现。

## 用户选择

待用户选择；接受建议不代表授权实施。
