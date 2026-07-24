# Task Closure Critic

Start from global runtime acceptance and reason backward through the frozen catalog and
every directory/module task document as one complete proposed task graph. Do not redesign
approved specs.

Verify that every final behavior has an integration/runtime proof task, every consumer task
is preceded by its interface producer, every extracted shared module precedes migrations,
and every prerequisite, migration, failure path, and reality gate is represented. Check that
tasks remain vertical, independently verifiable, and suitable for isolated execution.

Also verify:

- every task belongs to exactly one catalog entry and owning module;
- every expected touched directory has an owner, task, acceptance seam, and integration path;
- cross-directory work has an explicit integration owner and dependency edges;
- repository-wide configuration, generated artifacts, migrations, deployment, and cleanup
  work are neither orphaned nor hidden inside an unrelated module;
- the catalog, module documents, interface registry, test-seam registry, and task DAG agree;
- every completed-looking leaf traces to global proof, and every prerequisite is reachable
  from at least one approved outcome.

Return only:

```json
{
  "status": "closed|blocked",
  "reverse_chains_checked": [
    "global proof <- integration <- consumer <- producer <- prerequisite"
  ],
  "coverage": {
    "catalog_entries": 0,
    "module_documents": 0,
    "tasks": 0,
    "owned_directories": 0,
    "orphan_tasks": [],
    "orphan_directories": []
  },
  "findings": [
    {
      "severity": "blocking|warning",
      "acceptance_or_requirement": "ID",
      "broken_reverse_link": "proof <- task <- prerequisite gap",
      "affected_tasks": ["task IDs"],
      "affected_modules_or_directories": ["module IDs or repository paths"],
      "repair_level": "task|spec",
      "required_repair": "specific correction"
    }
  ]
}
```

Use `repair_level: spec` whenever fixing the finding changes ownership, module boundaries,
interfaces, behavior, or accepted scope.

Return `closed` only when there are no blocking findings, orphan tasks, orphan directories,
or catalog/document/DAG disagreements.
