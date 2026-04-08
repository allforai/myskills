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
