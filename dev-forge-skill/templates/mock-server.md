# Mock Server 模板

> 基于 Express 的轻量 mock 后端，前端开发阶段连此服务。数据来自 seed-forge plan 产物。

---

## 目录结构

```
apps/mock-server/
├── package.json
├── server.js                       # 入口，一行启动
├── routes.json                     # 端点 → 响应映射（自动生成）
├── middleware/
│   ├── auth.js                     # 简化版 JWT 验证（始终放行或按 role 过滤）
│   ├── delay.js                    # 模拟网络延迟（可配置）
│   ├── cors.js                     # CORS 放行
│   └── image-proxy.js              # 图片代理中间件
├── fixtures/                       # Mock 数据（来自 seed-forge plan）
│   ├── users.json
│   ├── {entity-a}.json
│   ├── {entity-b}.json
│   └── ...
└── uploads/                        # 模拟文件上传目录
```

---

## package.json

```json
{
  "name": "mock-server",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "morgan": "^1.10.0",
    "jsonwebtoken": "^9.0.0"
  }
}
```

---

## server.js 模板

```javascript
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.MOCK_PORT || 4000;

// --- Middleware ---
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// 模拟延迟（可选）
const DELAY_MS = parseInt(process.env.MOCK_DELAY || '0', 10);
if (DELAY_MS > 0) {
  app.use((req, res, next) => setTimeout(next, DELAY_MS));
}

// --- 图片代理 ---
// /api/images/{id} → 从 image-map.json 查找真实 URL 并代理
const imageProxy = require('./middleware/image-proxy');
app.use('/api/images', imageProxy);

// --- 静态文件 ---
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// --- 路由加载 ---
const routes = require('./routes.json');

// 为每个端点注册路由
for (const route of routes) {
  const { method, path: routePath, fixture, response } = route;
  const handler = createHandler(route);
  app[method.toLowerCase()](routePath, handler);
}

function createHandler(route) {
  return (req, res) => {
    // 加载 fixture 数据
    if (route.fixture) {
      const data = loadFixture(route.fixture);
      if (!data) return res.status(500).json({ error: 'Fixture not found' });

      // 支持分页
      if (route.paginated && req.query.page) {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const start = (page - 1) * limit;
        const items = Array.isArray(data) ? data : data.items || [];
        return res.json({
          items: items.slice(start, start + limit),
          total: items.length,
          page,
          limit,
          totalPages: Math.ceil(items.length / limit)
        });
      }

      // 支持按 ID 查询
      if (req.params.id && Array.isArray(data)) {
        const item = data.find(d => String(d.id) === String(req.params.id));
        if (!item) return res.status(404).json({ error: 'Not found' });
        return res.json(item);
      }

      return res.json(data);
    }

    // 静态响应
    if (route.response) {
      return res.status(route.status || 200).json(route.response);
    }

    // 写操作：回显请求体
    if (['POST', 'PUT', 'PATCH'].includes(route.method)) {
      return res.status(route.status || 201).json({
        ...req.body,
        id: req.params.id || generateId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }

    // DELETE
    if (route.method === 'DELETE') {
      return res.status(204).send();
    }

    res.status(200).json({ message: 'OK' });
  };
}

function loadFixture(name) {
  const filePath = path.join(__dirname, 'fixtures', `${name}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function generateId() {
  return `mock-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// --- 认证端点（简化版）---
app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;
  const users = loadFixture('users') || [];
  const user = users.find(u => u.email === email);
  if (!user) return res.status(401).json({ error: 'Invalid credentials' });
  const jwt = require('jsonwebtoken');
  const token = jwt.sign(
    { id: user.id, role: user.role, email: user.email },
    process.env.JWT_SECRET || 'mock-secret',
    { expiresIn: '24h' }
  );
  res.json({ token, user: { id: user.id, name: user.name, role: user.role, email: user.email } });
});

app.get('/api/auth/me', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'No token' });
  try {
    const jwt = require('jsonwebtoken');
    const decoded = jwt.verify(authHeader.replace('Bearer ', ''), process.env.JWT_SECRET || 'mock-secret');
    const users = loadFixture('users') || [];
    const user = users.find(u => u.id === decoded.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
});

// --- 健康检查 ---
app.get('/health', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));

// --- 启动 ---
app.listen(PORT, () => {
  console.log(`Mock server running at http://localhost:${PORT}`);
  console.log(`Routes loaded: ${routes.length}`);
  console.log(`Fixtures dir: ${path.join(__dirname, 'fixtures')}`);
});
```

---

## routes.json 生成规则

从后端子项目的 `design.md` 提取 API 端点列表，生成路由映射：

```json
[
  {
    "method": "GET",
    "path": "/api/{resource}",
    "fixture": "{resource}",
    "paginated": true,
    "description": "列表查询"
  },
  {
    "method": "GET",
    "path": "/api/{resource}/:id",
    "fixture": "{resource}",
    "description": "详情查询"
  },
  {
    "method": "POST",
    "path": "/api/{resource}",
    "status": 201,
    "description": "创建"
  },
  {
    "method": "PUT",
    "path": "/api/{resource}/:id",
    "status": 200,
    "description": "更新"
  },
  {
    "method": "DELETE",
    "path": "/api/{resource}/:id",
    "status": 204,
    "description": "删除"
  }
]
```

**映射规则**:
- `design.md` 中每个 API 端点 → 1 条路由
- CRUD 端点自动展开为 GET(list) + GET(:id) + POST + PUT + DELETE
- 非 CRUD 端点（如 `/api/orders/:id/approve`）→ 自定义 handler，返回状态变更后的对象

---

## fixtures 数据生成规则

### 有 seed-forge plan 时

读取 `.allforai/seed-forge/seed-plan.json`（或旧版 `forge-plan.json`），为每个实体生成 fixture：

1. 每个实体 → 1 个 `{entity}.json` 文件
2. 数据量按 seed-plan 中的数量设计（高频多、低频少）
3. 关联关系正确（外键引用已有记录 ID）
4. 状态枚举全覆盖
5. 时间戳合理（created_at < updated_at，近密远疏）

### 无 seed-forge plan 时

为每个实体生成最小 fixture：
- 每实体 3-5 条记录
- 覆盖所有状态枚举
- 使用合理的占位数据

---

## 图片代理中间件

**middleware/image-proxy.js**:

```javascript
const https = require('https');
const http = require('http');
const path = require('path');
const fs = require('fs');

// image-map.json: { "img-001": "https://images.unsplash.com/..." }
const IMAGE_MAP_PATH = path.join(__dirname, '..', 'fixtures', 'image-map.json');

module.exports = (req, res) => {
  const imageId = req.params[0] || req.path.replace('/', '');

  // 加载映射
  if (!fs.existsSync(IMAGE_MAP_PATH)) {
    return res.status(404).json({ error: 'image-map.json not found' });
  }

  const imageMap = JSON.parse(fs.readFileSync(IMAGE_MAP_PATH, 'utf-8'));
  const url = imageMap[imageId];
  if (!url) return res.status(404).json({ error: `Image ${imageId} not found` });

  // 代理请求
  const client = url.startsWith('https') ? https : http;
  client.get(url, (proxyRes) => {
    res.set('Content-Type', proxyRes.headers['content-type'] || 'image/jpeg');
    res.set('Cache-Control', 'public, max-age=86400');
    proxyRes.pipe(res);
  }).on('error', () => {
    res.status(502).json({ error: 'Failed to proxy image' });
  });
};
```

**前端代码中的图片路径**: `/api/images/{id}` — 与真实后端一致，切换时只改 base URL。

---

## Auth 中间件

**middleware/auth.js**:

```javascript
const jwt = require('jsonwebtoken');
const SECRET = process.env.JWT_SECRET || 'mock-secret';

module.exports = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'No token provided' });

  try {
    const token = authHeader.replace('Bearer ', '');
    req.user = jwt.verify(token, SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
};
```

---

## 前端连接配置

前端子项目的 `.env.development`:
```bash
# 开发阶段连 mock-server
NEXT_PUBLIC_API_URL=http://localhost:4000
# 集成阶段切换到真实后端
# NEXT_PUBLIC_API_URL=http://localhost:3001
```

**切换时机**: Phase 4 Round 3（B4 Integration），修改环境变量即可。

---

## 启动验证

```bash
cd apps/mock-server
pnpm install
pnpm start
# → Mock server running at http://localhost:4000
# → Routes loaded: 25

# 验证
curl http://localhost:4000/health
curl http://localhost:4000/api/users
curl -X POST http://localhost:4000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@test.com","password":"SeedForge2024!"}'
```
