---
name: journal-merge
description: >
  Merge decision-journal entries into product-concept.json and emit
  concept-drift.json. User-invoked only via /skill:journal-merge or
  /skill:meta-skill journal-merge; never invoke it yourself.
---

# Journal Merge — Decision Reconciliation

用户显式调用 `/skill:journal-merge` 才运行。把 journal 合并进产品概念，并写出 drift。

## Inputs

读取：

- `.allforai/product-concept/decision-journal.json`
- `.allforai/product-concept/product-concept.json`
- 已有的 `.allforai/product-concept/concept-drift.json`

缺 journal 则停止，请用户先 `/skill:journal`。缺概念文件则停止，请用户先完成概念阶段。

## Step 1: Identify Unmerged Decisions

用 `concept-drift.json.last_merged_batch`（若有）判断未合并批次。每条分为 conflict / addition / no-op。

## Step 2: Resolve Conflicts

冲突用纯文本出示 journal 值与当前概念值，请用户三选一：接受 journal、保留概念、给出合并值。不要擅自决定。
addition 在没有新矛盾时自动接受。no-op 跳过。

## Step 3: Update the Concept

把接受的变更写入 `.allforai/product-concept/product-concept.json`。

## Step 4: Write Audit Trail

追加 `.allforai/product-concept/merge-audit.json`：merged batches、resolution mode、before/after。

## Step 5: Emit Drift Manifest

写或更新 `.allforai/product-concept/concept-drift.json`：时间、来源批次、变更列表、受影响下游（`product-map`、`experience-map`、`workflow`、`code`）、`resolved: false`。

## Step 6: Report Impact

报告变更摘要、受影响产物、输出文件，然后请用户重跑 `/skill:bootstrap` 以重规划工作流。不要在 merge 里直接改 `workflow.json`。
