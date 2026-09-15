---
name: journal
description: >
  Record product-level decisions from the current conversation into
  decision-journal.json. User-invoked only via /skill:journal or
  /skill:meta-skill journal; never invoke it yourself.
---

# Journal — Product Decision Journal

用户显式调用 `/skill:journal [topic]` 才运行。把本轮对话里的产品级决策记入 journal。

## Step 1: Scan Conversation Context

记录：

- 用户在选项中的选择
- 设计改向或纠正
- 功能增加、删除或推迟
- 架构或技术栈变化
- 产品行为澄清

不要记录：实现细节、临时调试、已经完整写在稳定产品产物里且用户未改的事实。

## Step 2: Summarize Decisions

每条记录 `question`、`chosen`、`rationale`，覆盖旧决定时加 `supersedes`。

## Step 3: Write Journal File

目标：`.allforai/product-concept/decision-journal.json`
已有则追加新批次；没有则按 canonical schema 新建。

## Step 4: Confirm Summary

用纯文本报告：条数、批次主题、每条一行、文件路径。

## Step 5: Detect Concept Conflicts

若存在 `.allforai/product-concept/product-concept.json`，找出与新 journal 的矛盾（仍保留的已删功能、概念明确排除的新功能），报告冲突，不要在 journal 步骤里合并。告诉用户下一步是 `/skill:journal-merge`。
