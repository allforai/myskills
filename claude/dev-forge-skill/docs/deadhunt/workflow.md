## 整体工作流

```
首次使用:                           后续使用:

  Phase 0: 项目分析 ──→ 保存          检测 .allforai/deadhunt/output/
  (Claude 自动初始化)                  (直接跑)
       ↓                  ↓                ↓
  Phase 1: 静态分析      ↓          有 validation-profile.json?
       ↓                  ↓            ├── 有 → 跳过 Phase 0，直接用
  Phase 2: 制定测试计划   ↓            └── 没有 → 走首次流程
       ↓                  ↓
  Phase 3: 深度测试      ↓          有 .auth/*.json?
       ↓                  ↓            ├── 有 → 跳过登录，直接用
  Phase 4: 报告          ↓            └── 没有 → 重新登录
                         ↓
              .allforai/deadhunt/output/    有 上次报告?
              (所有状态都保存在这里)    ├── 有 → 增量对比，只报告变化
                                     └── 没有 → 全量报告
```

### 核心原则：初始化一次，后续复用

```
.allforai/deadhunt/output/
├── validation-profile.json    ← Phase 0 的产出，持久保存
├── static-analysis/           ← Phase 1 的产出，每次更新
│   ├── routes.json
│   ├── crud-coverage.json
│   ├── api-reverse-coverage.json
│   └── bidirectional-matrix.json
├── test-plan.json             ← Phase 2 的产出，profile 不变就不变
├── tests/                     ← 生成的测试脚本，profile 不变就不变
├── reports/                   ← Phase 4 的产出，每次更新
│   ├── dead-links-report.json
│   ├── validation-report-admin.md
│   └── baseline.json          ← 上次的结果快照，用于增量对比
└── fix-tasks.json

.allforai/deadhunt/.auth/
├── admin.json                 ← 登录状态，长期有效（直到 token 过期）
├── merchant.json
└── customer.json
```

### 状态检测与流程决策

Claude 在开始验证时，**第一步**是检查 `.allforai/deadhunt/output/` 下已有的状态：

```typescript
// 概念逻辑 — Claude 应通过 Read/Glob/Grep 工具实现以下检测，而非直接执行此代码

interface ValidationState {
  profile: 'missing' | 'exists' | 'outdated';
  auth: Record<string, 'missing' | 'valid' | 'expired'>;
  static_analysis: 'missing' | 'exists' | 'outdated';
  test_plan: 'missing' | 'exists';
  last_report: 'missing' | 'exists';
}

/**
 * 检测已有状态，决定跳过哪些步骤
 */
async function detectState(validationDir: string): Promise<ValidationState> {
  const fs = require('fs');
  const path = require('path');
  const outputDir = path.join(validationDir, 'output');

  const state: ValidationState = {
    profile: 'missing',
    auth: {},
    static_analysis: 'missing',
    test_plan: 'missing',
    last_report: 'missing',
  };

  // 1. 检查 validation-profile.json
  const profilePath = path.join(outputDir, 'validation-profile.json');
  if (fs.existsSync(profilePath)) {
    const profile = JSON.parse(fs.readFileSync(profilePath, 'utf-8'));
    const profileAge = Date.now() - new Date(profile._meta?.updated_at || 0).getTime();
    const projectMtime = getProjectLastModified(profile.project?.path);

    if (profileAge > 7 * 24 * 3600 * 1000) {
      // 超过 7 天，建议更新（但不强制）
      state.profile = 'outdated';
    } else {
      state.profile = 'exists';
    }
  }

  // 2. 检查 auth state
  const authDir = path.join(validationDir, '.auth');
  if (fs.existsSync(authDir)) {
    const authFiles = fs.readdirSync(authDir).filter((f: string) => f.endsWith('.json'));
    for (const f of authFiles) {
      const clientId = f.replace('.json', '');
      const authData = JSON.parse(fs.readFileSync(path.join(authDir, f), 'utf-8'));

      // 检查 cookie/token 是否过期
      const isExpired = checkAuthExpired(authData);
      state.auth[clientId] = isExpired ? 'expired' : 'valid';
    }
  }

  // 3. 检查静态分析结果
  const staticDir = path.join(outputDir, 'static-analysis');
  if (fs.existsSync(path.join(staticDir, 'routes.json'))) {
    state.static_analysis = 'exists';
  }

  // 4. 检查测试计划
  if (fs.existsSync(path.join(outputDir, 'test-plan.json'))) {
    state.test_plan = 'exists';
  }

  // 5. 检查上次报告
  if (fs.existsSync(path.join(outputDir, 'reports', 'baseline.json'))) {
    state.last_report = 'exists';
  }

  return state;
}

/** 检查 auth state 中的 cookie/token 是否过期 */
function checkAuthExpired(authData: any): boolean {
  if (authData.cookies) {
    const now = Date.now() / 1000;
    return authData.cookies.some((c: any) => c.expires && c.expires > 0 && c.expires < now);
  }
  // localStorage 中的 token 无法从 state 文件判断过期
  // 保守处理：state 文件超过 24 小时视为可能过期
  const stat = require('fs').statSync(authData._path || '');
  return Date.now() - stat.mtimeMs > 24 * 3600 * 1000;
}
```

### 流程决策逻辑

```typescript
// 概念逻辑 — Claude 根据此决策树决定执行哪些 Phase

async function decideWorkflow(state: ValidationState): Promise<Phase[]> {
  const phases: Phase[] = [];

  // ── Profile ──
  if (state.profile === 'missing') {
    console.log('📋 未发现项目配置 — 需要初始化 (Phase 0)');
    phases.push('phase0_analyze');
  } else if (state.profile === 'outdated') {
    console.log('📋 项目配置超过 7 天 — 建议更新，但可以先用旧的');
    // 不强制重新分析，用户可以选择
  } else {
    console.log('✅ 项目配置已存在 — 跳过 Phase 0');
  }

  // ── Auth ──
  // 对每个需要验证的 client 检查 auth
  // 有效的直接用，过期的重新登录，没有的需要初始化
  for (const [clientId, authState] of Object.entries(state.auth)) {
    if (authState === 'valid') {
      console.log(`✅ ${clientId} 登录状态有效 — 直接复用`);
    } else if (authState === 'expired') {
      console.log(`⚠️ ${clientId} 登录状态已过期 — 需要重新登录`);
      phases.push(`auth_${clientId}`);
    }
  }

  // ── 静态分析 ──
  // 静态分析每次都跑（快，且代码可能变了）
  phases.push('phase1_static');

  // ── 测试计划 ──
  if (state.test_plan === 'exists' && state.profile !== 'missing') {
    console.log('✅ 测试计划已存在 — 检查是否需要更新');
    // 如果静态分析发现新的路由/模块，测试计划需要更新
  } else {
    phases.push('phase2_plan');
  }

  // ── 深度测试 ──
  phases.push('phase3_test');

  // ── 报告 ──
  if (state.last_report === 'exists') {
    console.log('📊 发现上次报告 — 将生成增量对比');
  }
  phases.push('phase4_report');

  return phases;
}
```

### profile 中的元信息

`validation-profile.json` 需要记录创建和更新时间：

```json
{
  "_meta": {
    "version": "1.0",
    "created_at": "2026-02-16T10:00:00Z",
    "updated_at": "2026-02-16T14:30:00Z",
    "created_by": "deadhunt skill",
    "project_hash": "abc123",
    "notes": "用户确认过模块分类"
  },
  "project": { ... },
  "clients": [ ... ],
  "modules": [ ... ]
}
```

`project_hash` 是项目关键文件（路由配置、菜单配置、package.json）的哈希值。如果哈希变了，说明项目结构可能变了，建议重新分析。

### 用户交互：初始化 vs 直接跑

Claude 在收到验证请求时的决策流程：

```
用户说: "请验证我的项目"
          │
          ▼
  检查 .allforai/deadhunt/output/validation-profile.json
          │
    ┌─────┴──────┐
    │            │
  不存在        存在
    │            │
    ▼            ▼
  "我来分析      "上次配置还在，
   你的项目..."     直接开跑？"
    │            │
    ▼        ┌───┴───┐
  Phase 0     │       │
  (首次初始化)  用户: 对  用户: 重新分析
    │         │       │
    ▼         ▼       ▼
  请用户确认   跳过 Phase 0  重跑 Phase 0
  模块分类     直接 Phase 1→
```

**关键对话模式：**

```
# 首次使用
用户: 请验证我的项目，路径 /home/david/my-shop。
Claude: 这是第一次验证这个项目，让我先分析结构...
        [执行 Phase 0]
        请确认模块分类...

# 后续使用（有配置）
用户: 请验证我的项目。
Claude: 检测到上次的验证配置（2天前创建，15 个模块）。
        登录状态: admin ✅有效  merchant ✅有效
        直接开始验证？还是需要更新配置？
用户: 直接跑。
Claude: [跳过 Phase 0，直接 Phase 1 → Phase 4]

# 后续使用（配置过期）
用户: 请验证我的项目。
Claude: 检测到上次的验证配置（10天前）。
        但项目路由文件有变更，建议更新配置。
        要更新还是先用旧的？
用户: 更新吧。
Claude: [重跑 Phase 0，但保留之前的模块分类作为参考]

# 后续使用（auth 过期）
用户: 请验证我的项目。
Claude: 项目配置 ✅ 有效。
        但 admin 的登录状态已过期（超过 24 小时）。
        需要重新登录。账号密码还是 admin/123456 吗？
用户: 对。
Claude: [只重新登录，不重跑 Phase 0]
```
