# Spec Execute Command

Execute tasks from the approved task list, automatically continuing until all tasks are done.

## Usage
```
/spec-execute [task-id] [feature-name]
```

- 指定 task-id：只执行该任务，完成后继续执行下一个
- 不指定 task-id：从第一个未完成任务开始，**一直执行到全部完成**

## CRITICAL: 不要停下来

完成每个任务后，**立即开始下一个**，不要停下来等用户说"继续"。

唯一停止条件：
- 所有任务已完成 → 打印"✅ 全部任务完成"并退出
- 某任务失败且无法自动修复 → 报告具体错误并停止
- 用户在对话中明确说"停下" / "stop" / "暂停"

## 执行循环

```
LOOP:
  1. 读取 tasks.md，找到第一个未完成 ([ ]) 的任务
  2. 如果没有未完成任务 → 打印"✅ {feature-name} 全部任务完成" → EXIT
  3. 加载该任务的上下文（steering + spec + task details）
  4. 用 spec-task-executor agent 执行任务
  5. 执行成功：
       - 标记完成：claude-code-spec-workflow get-tasks {feature-name} {task-id} --mode complete
       - 打印一行："✅ Task {task-id} 完成 — {一句话说明}"
       - GOTO LOOP（立即开始下一个）
  6. 执行失败：
       - 尝试修复，最多重试 2 次
       - 仍失败 → 报告"❌ Task {task-id} 失败：{原因}" → EXIT
```

## Step 1: Load Context（每个任务执行前）

```bash
# 加载 steering 文档（如果存在）
claude-code-spec-workflow get-steering-context

# 加载 spec 上下文
claude-code-spec-workflow get-spec-context {feature-name}

# 加载当前任务详情
claude-code-spec-workflow get-tasks {feature-name} {task-id} --mode single
```

## Step 2: 用 Agent 执行

```
Use the spec-task-executor agent to implement task {task-id} for the {feature-name} specification.

## Steering Context
[完整的 get-steering-context 输出]

## Specification Context
[get-spec-context 的 requirements + design 部分]

## Task Details
[get-tasks single 输出]

## Instructions
- 只实现指定的任务：{task-id}
- 遵循项目规范，复用现有代码
- 完成后标记：claude-code-spec-workflow get-tasks {feature-name} {task-id} --mode complete
```

## 实现规范

- 每次专注一个任务，不跨任务修改
- 遵循 steering 文档（tech.md / structure.md）
- 复用现有 utilities 和 patterns
- 如有子任务先完成子任务
- 有测试要求的必须写测试

## 任务选择逻辑

未指定 task-id 时：
- 扫描 tasks.md，找所有未完成任务
- 按编号顺序依次执行，不跳过，不询问

未指定 feature-name 时：
- 检查 `.claude/specs/` 目录
- 只有一个 spec → 直接使用
- 多个 spec → 询问用户选哪个

## 示例

```
/spec-execute user-authentication          # 从头执行所有任务
/spec-execute 2.1 user-authentication      # 从 2.1 开始，继续到结束
```
