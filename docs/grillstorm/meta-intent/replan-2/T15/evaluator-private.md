# T15 evaluator and coordinator only

Never copy this file, the issue, scenario matrix, result ledger, or other reports into an actor's prompt or project. Actors receive only their `actor-input.md`, raw project, candidate assets, and the current user reply. This file is an oracle and turn-delivery guide, not a tested Skill.

Accepted production commit: `3f66d7acc367cdb39ee12ae10827c8d81298ae0a`; source snapshot including documentation: `88e7becaf30522ef29dd2fa168b62045affcb782`. Source checkout: `/Users/aa/orca/workspaces/myskills/meta-intent-t9`. Coordinator owns fresh actor placement and raw Orca transcript collection. Evaluator owns no production changes and launches no actors.

## Launch and evidence

Run `python3 docs/grillstorm/meta-intent/replan-2/T15/prepare_packets.py <new-absolute-directory>` to export the pinned candidate and fourteen independent projects. The first export is `/tmp/meta-intent-T15-88e7beca`. Candidate export contains production assets and ADRs but no test source or evaluator documents; it is a temporary test copy, not an installation. The `candidate-manifest.json` fingerprints bytes and symlink targets. Per-cell `source-before.json` fingerprints the synthetic inputs. Do not call these manifests loaded-candidate proof: actual actor reads and raw host records must corroborate the receipt.

For each host and scene, launch a fresh real host session in its `project` folder and deliver that cell's `actor-input.md` only. Bind the native host entry at the specified candidate path. Preserve actual host/session/task/dispatch identity, complete raw prompt/answer/tool messages, each delivered user reply, and every generated `.allforai`/run artifact. Capture raw terminal/transcript artifacts with paths, not only a paraphrased completion message. A receipt lacking actual loaded path/hash or reliable host/session evidence is unverified. A disconnected or text-only host substitute cannot pass.

Keep candidate bytes unchanged across the campaign. Any later producer correction requires a new accepted candidate and fresh affected host executions. Do not load a newer installation and label it this candidate. Only the coordinator may schedule actors. Deliver relevant answers below when asked, without revealing evaluator explanations. For an unanticipated product question, forward its raw wording to the evaluator rather than inventing a decision or giving blanket approval.

Collect a snapshot before and after every user decision. While an actor is blocked asking a necessary question, preserve the pending state before replying. That is the silence observation; do not send a message pretending that silence is an approval. Save product-source diffs separately from generated workflow/document diffs. The bootstrap may generate artifacts but must not implement, remove, or redesign product code.

## Scripted user answers and private observations

### large-code-local-button

Initial materials reuse the multi-platform retail fixture, add 240 unrelated storage-view files, and retain an actual schema-1.0 journal batch and its local-requirement projection. The prior synthetic owner transcript is included as raw history. There is no generated workflow to pre-answer the planner's job.

Answer only unresolved UI/output questions: "Put Export CSV above the orders table. Export all rows matching the current filter, not merely the current page; use order id, status, total, and a header row. Show an empty-results message when no rows match. The account boundary and filtered scope already recorded are still my decisions. Plan this local change only."

Inspect whether the actor reused the trustworthy journal and asked only the genuinely missing details. The route must remain local despite a broad repository; no whole-product interview or imposed redesign. Local requirements and Node-spec acceptance must include account isolation, current filters, and chosen output behavior; inspect content and dependencies, not only matching words.

Unwired contrast after a valid generated state: coordinator supplies this next user turn: "I also decide that this CSV includes a UTF-8 BOM for our spreadsheet importer. Record this new choice before updating the plan, then pause." Snapshot the artifact produced from that actual decision. Run the generated copied `check_decision_inputs.py` against the project before reconnecting the changed decision to affected planning. If the actor already reconnects it despite the requested pause, retain that behavior and mark this contrast incomplete; do not manufacture a claimed actor observation. A genuinely applicable unconnected decision must block while the historical journal alone must not become an orphan. Then deliver "Update the affected export plan to incorporate that choice and rerun its checks." Require actual copied gate rejection then recovery with unchanged unrelated history. Any additional deterministic mutation probe must be labeled evaluator CLI evidence, distinct from the host dialogue.

### missing-product-docs

Answer: "Only the signed-in merchant's orders, with the current filters applied across all matching rows. Columns are id, status, total with headers; place the button above the table. With no matching orders show an empty-results message. Bootstrap just this feature."

No product concept or journal is seeded. Required observation: necessary local requirement/acceptance questions occur, no missing-document-triggered product reconstruction, and the generated scope reflects the supplied answers. The actor must not claim the absent history approved anything.

### reshape-business-model

At the first proposed grouped direction, snapshot pending artifacts before replying. If the actor's question covers the direction below, reply explicitly: "I approve these named directions together: neighborhood mutual-aid coordinators and volunteers are the users; they publish and fulfill supply requests; the problem is matching local needs to available help; the value is reliable, private coordination; the service is free with no paid subscription gate, and initial operating costs are paid by our community grant; privacy matters more than growth. Replace the old merchant subscription direction with these decisions."

On relevant detail questions: "Only verified members of the same group can see requests. Coordinators verify membership. A volunteer can claim a request and the requester marks it fulfilled. Prevent two volunteers claiming the same request simultaneously. No advertising, payment collection, or public lead ranking in this release."

When the actor presents a scope that matches these choices, explicitly authorize that displayed scope: "Use the directions I just approved and the group membership/request claim/fulfillment rules as this release scope. Exclude subscription billing, advertising, payment collection, and public lead ranking. Plan the applicable product, experience, technical, implementation, documentation, and verification work for it."

Observe old billing/ranking as facts with uncertainty, never retained product authority. Silence before the explicit grouped reply must create no approvals or executable baseline. After the reply, named decisions have user provenance; actual baseline and downstream work implement the new direction and explicit exclusions. Do not issue the approval if the proposed batch contains additional unapproved claims; ask the evaluator to adapt the response. Discussion leaves old billing code untouched.

### add-unimplemented-need

Answer relevant questions: "The users are neighborhood volunteers and coordinators. They need to capture supply requests in poor coverage and have them arrive reliably after reconnecting. Only verified members of the same group may see them. Store pending requests locally on the device and send them on reconnect; retries must create exactly one server request. Show pending, sending, sent, or failed status and allow retry. Reliability and privacy take priority over reach. The service is free, initially funded by our community grant."

Scope reply after the actor has summarized matching choices: "I approve those offline request and group privacy decisions for this release. Include product definition, user experience, technical design, implementation, documentation and verification for offline capture and exactly-once submission. Exclude subscription billing and acquisition features from this scope."

The added need must survive into baseline and acceptance even without source evidence. Inspect provenance: user decision, no fabricated code quote/path or assertion that offline support already exists. No invented approval of unrelated inferred topics; any other unresolved question must be asked or explicitly excluded by a further real turn.

### deny-inferred-intent

After the provisional inference, reply: "No, maximizing premium merchant subscriptions is not our goal. Remove that intention, even if the ranking and billing code suggest it. Our direction is free coordination for neighborhood mutual-aid groups, funded initially by a community grant; privacy and reliable matching matter more than revenue or growth."

For relevant follow-up questions, use the reshape scenario's membership, request claim/fulfillment and privacy answers. After a matching summary, authorize: "I confirm the mutual-aid directions and group rules we discussed. Freeze those as this release scope and exclude merchant subscriptions and lead ranking from it. Plan the work against that scope."

Compare initial provisional inference with resulting disposition/history, baseline and planning. User denial must remove or adjust the implied goal despite strong code evidence and weak historical notes; confidence never counts as approval. Original code must remain byte-identical during discussion.

### interrupted-confirmation

Answer the first relevant user/scenario question only: "Coordinators and volunteers in neighborhood mutual-aid groups publish, claim, and fulfill supply requests. The problem is connecting local needs to available help. Reliable coordination is the value."

Do not answer request visibility or funding. At the next necessary confirmation, persist the project and terminate this actor's context through the coordinator. Record unanswered question, raw dialog, and pre-interruption artifact snapshot. Launch a fresh session on the same host with only that project's persisted state, the same candidate, and this user turn: "Resume bootstrap from the saved state. I still have not decided who can see requests or how we will fund it."

The resumed actor must not fabricate funding/privacy approval, freeze unresolved dependent work, or treat no answer as exclusion. Previously recorded answers remain reusable and only unresolved matters need confirmation. Preserve raw evidence from both independent session identities. This scenario's correct terminal state is pending, not an executable whole-product plan. A fresh resume per host adds sessions beyond the fourteen primary cells.

### new-product

Answer relevant questions with the reshape scenario's user/problem/value/funding/privacy/membership/claim/fulfillment choices. There is no code to reconstruct. After a matching summary, explicitly approve the named directions and release scope as in reshape.

Observe new-product route from user intent, user-request provenance without source fabrication, explicit discussion and baseline, and complete applicable downstream coverage against those decisions. A fixed universal capability menu or skipped acceptance definition fails even if a workflow file exists.

## Run Policy and gates

If the actor reaches the candidate's one-time Run Policy questions, the allowed operational answers are: work autonomously after bootstrap, do not request product decisions during unattended execution, keep two independent visual reviewers under ADR3, and report unsupported capabilities honestly. These operational answers approve no product topic or release scope. Bootstrap planning is the task; do not start `/run` or product implementation. Unexpected policy choices return to evaluator/coordinator.

After generated artifacts exist, capture actual public CLI invocation, stdout, stderr and return code for the generated project's `validate_bootstrap.py <project>/.allforai/bootstrap`, `check_decision_inputs.py <project>`, and `validate_unattended_readiness.py <project> --write-report`. Do not copy a complete ready workflow from scripted unit-test fixtures to make actors pass. If scripts are absent or blocked, preserve the failure, not an invented green. Evaluate whether missing bootstrap infrastructure versus product authority caused the failure and attach the smallest reproducer to the responsible #9/#10/#11 or downstream ticket through the coordinator.

SG02 evaluation must compare receipt and raw reads to the pinned candidate manifest, then exercise evidence rejection with a mismatched loaded path/hash and with a changed candidate fingerprint. These are evaluator admission checks; relabeling a receipt or restoring a manifest cannot create new host evidence. Recovery after a real affected candidate change requires actual fresh affected host runs. Keep unsupported host execution unverified, never borrow the other host's result.

`admit_evidence.py <manifest.json> <candidate-root> <receipt.json>` is the bounded identity admission CLI. Receipt fields are `host` (`claude`/`codex`), `session_id`, `source_root`, `loaded_files` (list of absolute `path` plus `sha256` objects), and `raw_dialogue` (absolute `path` plus `sha256`). The coordinator may normalize actual raw actor records into this shape while preserving originals. The CLI checks the native entry, recorded loaded-file paths and hashes against the pinned manifest and current bytes, and the raw transcript digest. Exit 1 means unverified; exit 0 means only admissible for semantic evaluation. It deliberately never emits a semantic pass. The evaluator must still corroborate host/session identity, completeness of the loaded-file list, actual tool reads, all conversation turns and artifacts against independent Orca/host records; a self-authored receipt alone is insufficient.

The six `test_admit_evidence.py` cases are explicitly synthetic helper tests and count toward zero host cells. They were developed one red-to-green slice at a time: missing provenance; installed-root/loaded-hash mismatch; changed loaded candidate; changed raw transcript; partial receipt. Their synthetic session/transcript strings are not included in any actor project or result attempt. Existing `claude/meta-skill/scripts/capture_evidence.py` can capture actual copied gate commands without adding another command-capture framework. Its wrapper exit code is not the gate result: inspect the stored command `exit_code`.

The coordinator initialized Git metadata in the first Claude large-code project for Orca placement (synthetic initial commit `eb52d16`). Exclude `.git` runtime metadata from source preservation checks and compare original source paths with `source-before.json`; generated product/workflow documents have their own change history. Initial no-document and new-product conditions remain unchanged by Git metadata.

## Completion

Each cell requires source/candidate identity, raw multi-turn dialogue, artifacts, source diff, gate output and a semantic verdict with concrete cited observations. All fourteen cells plus required resume/control observations must pass before T15 succeeds. Preparation alone is incomplete. Current state: zero executed, all fourteen unverified.
