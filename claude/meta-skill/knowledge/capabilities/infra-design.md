# Infrastructure Design Capability

> Design infrastructure architecture: realtime communication, message queues,
> object storage, CDN, push notifications, caching, load balancing.
> Internal execution is LLM-driven — infra choices adapt to project scale and requirements.

## Goal

Design the infrastructure layer that supports the application. Select appropriate
technologies for each concern, define integration patterns, and produce an
infrastructure architecture document that implementation nodes consume.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `infra-design.json` | Infrastructure decisions: technology choices, configuration requirements, integration patterns |
| `infra-design.md` | Human-readable infrastructure architecture document |

### Design Dimensions (LLM selects which apply)

| Dimension | Options to evaluate | Applies when |
|-----------|-------------------|-------------|
| Realtime communication | WebSocket / gRPC streaming / SSE / MQTT / Long polling | Product has live updates, chat, collaboration |
| Message queue | NATS / Kafka / RabbitMQ / Redis Pub-Sub / SQS | Product has async workflows, event-driven processing |
| Object storage | S3 / MinIO / GCS / Azure Blob | Product handles file uploads, media, documents |
| CDN & static assets | CloudFront / Cloudflare / Fastly / self-hosted | Product serves static content or media at scale |
| Push notifications | APNs / FCM / Web Push / OneSignal | Product has mobile apps or browser notifications |
| Caching | Redis / Memcached / application-level cache | Product has hot data or expensive queries |
| Load balancing | Nginx / HAProxy / cloud LB / service mesh | Product expects concurrent users |
| Service discovery | DNS / Consul / Kubernetes / etcd | Product has multiple services |

### Required Quality

- Every dimension relevant to the project has an explicit technology choice with rationale
- Choices are justified by project scale, team expertise, and operational complexity
- Integration patterns between components are defined (how does the API talk to the queue? how does the queue trigger the worker?)
- Development vs production configuration differences are noted

## Interaction Mode

**Search-driven selection questions (mandatory for each relevant dimension):**

For each design dimension that applies to this project, LLM MUST:

1. **WebSearch** 1-2 rounds: benchmarks, case studies, production war stories for the candidate technologies at the project's expected scale
2. **Present 2-4 options** as a selection question, each with:
   - Technology name + one-line positioning (e.g., "NATS — lightweight, no persistence, <1ms latency")
   - Evidence from search ("Used by Cloudflare for 10M+ msg/s", "Benchmark shows X vs Y at N scale")
   - Fit assessment for THIS project ("your scale is ~1K msg/s, so Kafka's overhead is unnecessary")
3. **User selects** — LLM does NOT decide for the user
4. **"Other" response** → WebSearch with user's input → new selection question with refined options

**When to skip interaction:**
- Dimension has only one viable option at the project's scale (e.g., APNs for iOS push — no real alternative)
- User already specified the technology in bootstrap Step 1.5 (e.g., "Redis" in infrastructure needs)
- **Decision already made in product-concept tech-architecture sub-phase** — load `tech-architecture.json` and inherit those choices. Only ask about integration/configuration details, not the technology selection itself.
- In these cases, state the decision with rationale and move on (user can override)

## Methodology Guidance (not steps)

- **Start from product requirements**: Read product-concept features that imply infra needs (realtime, notifications, file handling, search)
- **Right-size**: Don't recommend Kafka for a project that sends 10 messages/day. Match infra to expected scale.
- **12-Factor App principles**: Config in environment, stateless processes, disposable instances
- **CAP theorem awareness**: For distributed components, make explicit tradeoff (consistency vs availability)
- **Dev parity**: Infrastructure should be reproducible locally (Docker Compose, local emulators)

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Maximum-Realism: use real services when credentials exist
- defensive-patterns.md: fallback strategies when infra components are unavailable

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `infra-design.json` | technology choices per dimension | translate (setup-env node) | required | setup-env 需要知道选了哪些基础设施来配置环境 |
| `infra-design.json` | integration patterns | translate (implement nodes) | optional | 实现时参考组件间集成模式，缺失时按通用模式继续 |
| `infra-design.json` | realtime technology choice | design-to-spec | optional | protocol-spec.md 需要知道用 WebSocket 还是 gRPC |

## Composition Hints

### Single Node (default)
One infra-design node covers all infrastructure decisions for the project.

### Split by Subsystem
For microservice architectures: infra-realtime, infra-storage, infra-messaging as separate nodes.

### Merge with Another Capability
For simple projects with one database and no realtime: merge infra decisions into the setup-env node.

### Skip Entirely
For static sites, CLI tools, pure frontend apps with no backend, or SDK/library projects.
