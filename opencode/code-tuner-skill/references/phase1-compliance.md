# Phase 1: Architecture Compliance Check

Phase 1 对服务端代码进行架构合规性检查，覆盖三层架构、两层架构、DDD 架构以及通用规则。所有规则按 ID 编号，检测结果输出为 `phase1-compliance.json`。

---

## 三层架构规则 (T-01 ~ T-06)

适用于 Entry(Controller/Handler) → Business(Service) → Data(Repository/DAO) 分层结构。

### T-01: 依赖方向单向

- **规则**: 强制依赖方向为 Entry → Business → Data，禁止反向依赖。Service 不能 import Controller，Repository 不能 import Service。
- **严重级别**: critical
- **检测方法**: 扫描 Business 层文件的 import/require 语句，匹配是否引用 Entry 层的包或模块；扫描 Data 层文件，匹配是否引用 Business 层的包或模块。
- **违规示例 (Java)**:
```java
// UserService.java — 违规：Service import 了 Controller
package com.example.service;
import com.example.controller.UserController; // T-01 violation

public class UserService {
    private UserController controller; // 反向依赖
}
```
- **违规示例 (Go)**:
```go
// service/user_service.go — 违规：service 包 import 了 handler 包
package service

import "myapp/handler" // T-01 violation

func ProcessUser() {
    handler.GetContext() // 反向依赖入口层
}
```
- **违规示例 (TypeScript)**:
```typescript
// services/user.service.ts — 违规：Service import Controller
import { UserController } from '../controllers/user.controller'; // T-01 violation
```

### T-02: 入口层不得包含业务逻辑

- **规则**: Controller/Handler 只负责参数接收、格式校验、调用 Service、组装响应。禁止在入口层编写业务判断（if/else 业务条件、状态机流转、金额计算等）。
- **严重级别**: warning
- **检测方法**: 在 Entry 层文件中检测业务性质的条件判断——排除格式校验类（null check、length check、type check）之后，剩余的 if/else/switch 中包含业务术语（balance、status、inventory、price、discount、expired 等）视为违规。
- **违规示例 (Java)**:
```java
// OrderController.java — 违规：Controller 中包含库存判断
@PostMapping("/orders")
public Response createOrder(@RequestBody OrderRequest req) {
    Product product = productService.getProduct(req.getProductId());
    if (product.getInventory() < req.getQuantity()) { // T-02 violation: 业务逻辑
        return Response.error("库存不足");
    }
    BigDecimal total = product.getPrice()
        .multiply(BigDecimal.valueOf(req.getQuantity())); // T-02 violation: 金额计算
    return orderService.create(req, total);
}
```
- **违规示例 (Python)**:
```python
# views/order_view.py — 违规：View 中包含折扣计算
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    product = product_service.get(data["product_id"])
    if product.status == "discontinued":  # T-02 violation: 业务状态判断
        return jsonify(error="商品已下架"), 400
    discount = 0.8 if data["is_vip"] else 1.0  # T-02 violation: 折扣逻辑
    total = product.price * data["quantity"] * discount
    return order_service.create(data, total)
```

### T-03: 入口层直接访问数据层

- **规则 (特殊)**: 入口层直接注入 Repository/DAO 时需判断是否合理。简单 CRUD（无业务判断、无组合调用、无事务要求）→ **OK (info)**；包含业务逻辑 → **违规 (warning)**。
- **严重级别**: 视情况 info 或 warning
- **检测方法**: 检测 Entry 层文件是否 import Data 层模块。若检测到，进一步分析该方法体：(1) 是否仅有单次 Repository 调用且无条件分支 → info (simple CRUD); (2) 是否存在多次 Repository 调用、if/else 判断、事务注解 → warning (含业务逻辑)。

**合格的 Simple CRUD 示例**:
```java
// UserController.java — OK：纯粹的单表查询，无业务判断
@GetMapping("/users/{id}")
public UserDTO getUser(@PathVariable Long id) {
    User user = userRepository.findById(id).orElseThrow();
    return UserDTO.from(user); // 单次查询 + 转换，无业务逻辑
}

@GetMapping("/users")
public List<UserDTO> listUsers(Pageable pageable) {
    return userRepository.findAll(pageable)
        .map(UserDTO::from).getContent(); // 单次分页查询
}
```

**违规示例——包含业务逻辑**:
```java
// OrderController.java — 违规：跳过 Service 但包含业务逻辑
@PostMapping("/orders")
public Response createOrder(@RequestBody OrderRequest req) {
    Product product = productRepository.findById(req.getProductId()).orElseThrow();
    if (product.getInventory() < req.getQuantity()) { // 业务判断 → 不是 simple CRUD
        return Response.error("库存不足");
    }
    product.setInventory(product.getInventory() - req.getQuantity()); // 库存扣减
    productRepository.save(product);
    Order order = new Order(req, product.getPrice());
    orderRepository.save(order); // 多表操作 + 事务需求 → 应在 Service 层
    return Response.ok(order);
}
```

**判定标准汇总**:

| 特征 | Simple CRUD (OK) | 含业务逻辑 (违规) |
|------|-------------------|-------------------|
| Repository 调用次数 | 1 次 | 多次 |
| 条件分支 | 无业务判断 | 有 if/else 业务条件 |
| 事务需求 | 无 | 有 @Transactional 或跨表操作 |
| 数据组合 | 无 | 多表数据拼装 |
| 写操作附带校验 | 无 | 有（库存、余额等） |

### T-04: 数据层不得反向依赖业务层

- **规则**: Repository/DAO 不能 import Service 层模块。数据层只与实体和数据库框架交互。
- **严重级别**: critical
- **检测方法**: 扫描 Data 层文件的 import 语句，匹配 Business 层的包名或模块路径。
- **违规示例 (Java)**:
```java
// UserRepository.java — 违规
package com.example.repository;
import com.example.service.NotificationService; // T-04 violation
```
- **违规示例 (Go)**:
```go
// repository/user_repo.go — 违规
package repository
import "myapp/service" // T-04 violation
```

### T-05: 实体类不得在入口层直接暴露

- **规则**: Controller/Handler 的返回值和请求参数不得直接使用 Entity 类，应使用 DTO/VO 进行隔离。防止数据库结构泄漏、序列化问题、过度暴露字段。
- **严重级别**: warning
- **检测方法**: 分析 Entry 层方法的返回类型和参数类型，若直接引用 entity/model/domain 包下的类则标记违规。检查 `@ResponseBody` 方法返回 Entity、`@RequestBody` 参数为 Entity。
- **违规示例 (Java)**:
```java
// UserController.java — 违规：直接返回 Entity
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) { // T-05 violation: 返回 User Entity
    return userService.findById(id);
}
```
- **违规示例 (TypeScript)**:
```typescript
// user.controller.ts — 违规：直接返回数据库 model
@Get(':id')
async getUser(@Param('id') id: string): Promise<UserEntity> { // T-05 violation
    return this.userService.findById(id);
}
```

### T-06: 工具类不得依赖任何业务层

- **规则**: util/helper/common 包中的类不得 import Service、Repository、Controller。工具类应保持通用性，无业务耦合。
- **严重级别**: warning
- **检测方法**: 扫描 util/helper/common 目录下文件的 import 语句，匹配 controller/service/repository/handler 等业务层包名。
- **违规示例 (Java)**:
```java
// DateUtils.java — 违规
package com.example.util;
import com.example.service.ConfigService; // T-06 violation: 工具类依赖 Service
```
- **违规示例 (Python)**:
```python
# utils/date_helper.py — 违规
from services.config_service import ConfigService  # T-06 violation
```

---

## 两层架构规则 (W-01 ~ W-03)

适用于只有 Entry(Controller/Handler) → Data(Repository/DAO) 两层的简单项目，无独立 Business 层。

### W-01: 依赖方向 Entry → Data

- **规则**: 强制依赖方向为 Entry → Data，Data 层不得反向引用 Entry 层。
- **严重级别**: critical
- **检测方法**: 与 T-01 相同，但只检测两层间的关系。扫描 Data 层 import 是否包含 Entry 层引用。

### W-02: 业务逻辑应集中在入口层

- **规则**: 两层架构中，业务逻辑应集中在 Entry 层而非散落在 Data 层。Repository/DAO 中不应出现业务条件判断。
- **严重级别**: warning
- **检测方法**: 扫描 Data 层文件，检测是否包含业务性质的 if/else 判断（排除 null check 和数据完整性校验）。

### W-03: 实体暴露控制

- **规则**: 与 T-05 相同。即使是两层架构，也应避免直接暴露 Entity。对于极简项目（< 5 个实体）可降级为 info。
- **严重级别**: info 或 warning（视项目规模）
- **检测方法**: 同 T-05。额外统计项目实体数量以判定严重级别。

---

## DDD 规则 (D-01 ~ D-04)

适用于 Domain-Driven Design 分层：Interfaces → Application → Domain → Infrastructure。

### D-01: Domain 层零外部依赖

- **规则**: Domain 层不得引入任何框架 import（Spring、Hibernate、Express、GORM 等）和基础设施 import（database driver、HTTP client、message queue client）。Domain 层只包含纯业务逻辑和领域模型。
- **严重级别**: critical
- **检测方法**: 扫描 domain 包/目录下所有文件的 import 语句，匹配框架包名清单（`org.springframework`、`javax.persistence`、`gorm.io`、`express`、`sqlalchemy` 等）。允许标准库和领域内部引用。
- **违规示例 (Java)**:
```java
// domain/model/Order.java — 违规
package com.example.domain.model;
import javax.persistence.Entity;    // D-01 violation: 框架依赖
import javax.persistence.Id;        // D-01 violation
import org.springframework.data.annotation.CreatedDate; // D-01 violation
```
- **违规示例 (Go)**:
```go
// domain/order.go — 违规
package domain
import "gorm.io/gorm" // D-01 violation: ORM 框架依赖
```

### D-02: Application 通过接口调用 Infrastructure

- **规则**: Application 层调用 Infrastructure 层时必须通过 Domain 层定义的接口（Repository Interface / Port），不得直接依赖 Infrastructure 实现类。
- **严重级别**: critical
- **检测方法**: 扫描 Application 层 import 语句，若直接引用 `infrastructure` 包下的具体实现类则标记违规。检查注入的依赖类型是否为接口。
- **违规示例 (Java)**:
```java
// application/OrderAppService.java — 违规
import com.example.infrastructure.persistence.OrderRepositoryImpl; // D-02 violation

public class OrderAppService {
    private final OrderRepositoryImpl repo; // 应依赖 OrderRepository 接口
}
```

### D-03: 领域逻辑在 Domain 内

- **规则**: 业务规则和领域逻辑应定义在 Domain 层的 Entity/Value Object/Domain Service 中，不应散落在 Application Service。Application Service 只做编排（调用 Domain 对象 + 基础设施）。
- **严重级别**: warning
- **检测方法**: 在 Application 层文件中检测业务条件判断。若 Application Service 方法中存在大量 if/else 业务逻辑（而非纯粹的流程编排），标记为违规。启发式规则：单个方法超过 3 个业务条件分支。

### D-04: 聚合边界清晰

- **规则**: 一个聚合不得直接访问另一个聚合的内部实体。跨聚合交互应通过 Repository 获取聚合根，或通过 Domain Event。
- **严重级别**: warning
- **检测方法**: 分析 Domain 层内 import 关系。若聚合 A 的代码直接引用聚合 B 的非根实体，标记违规。需先识别聚合根（通常是有 Repository 接口的实体）。

---

## 通用规则 (G-01 ~ G-06)

适用于所有架构模式。

### G-01: 循环依赖检测

- **规则**: 任何两个或多个模块之间不得形成循环依赖。
- **严重级别**: critical
- **检测算法**:
  1. 构建 import 有向图：每个文件/模块为节点，import 关系为有向边。
  2. 使用 DFS 遍历图，维护当前访问路径栈。
  3. 若遍历时遇到已在栈中的节点，则检测到环。
  4. 记录完整的环路径：A → B → C → A。
  5. 对同一个环只报告一次，取字典序最小的节点作为起点。

### G-02: 实体公共字段未抽取基类

- **规则**: 若多个 Entity 类都定义了 `id`、`createTime`/`createdAt`、`updateTime`/`updatedAt` 等公共字段，应抽取 BaseEntity 基类。
- **严重级别**: info
- **检测方法**: 统计 Entity 类中出现 `id`、`createTime`、`updateTime` 字段的频率。若 >= 3 个 Entity 都有相同的公共字段且未继承同一基类，标记建议。

### G-03: 配置硬编码

- **规则**: 业务代码中不得硬编码配置值。URL、IP 地址、密码、端口号、magic number 应通过配置文件或环境变量注入。
- **严重级别**: warning（密码类为 critical）
- **检测方法**: 使用正则匹配以下模式：
  - URL: `https?://[^\s"']+`（排除 test 文件和注释）
  - IP: `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
  - 密码相关: 变量名含 `password`/`secret`/`token` 且赋值为字符串字面量
  - Magic number: 业务代码中非 0/1/-1 的数字字面量（需启发式排除数组索引和常见常量）

### G-04: 格式校验应在入口层完成

- **规则**: 格式类校验（null check、长度校验、正则校验、类型校验）应在 Entry 层完成，不应出现在 Business 层。
- **严重级别**: info
- **检测方法**: 在 Service/Business 层文件中检测以下模式：
  - 正则校验: `Pattern.compile`、`matches()`、`re.match`、`RegExp`
  - Null check: 参数 null 判断后直接抛出 `IllegalArgumentException` 或返回错误
  - 长度校验: `.length() >` / `.length <` 结合参数校验类异常
  - 手动类型判断: `instanceof` 用于参数校验

### G-05: 业务规则验证应在业务层

- **规则**: 业务性质的条件判断（余额是否充足、库存是否足够、状态是否允许流转、权限是否满足）应在 Business 层，不应出现在 Controller。
- **严重级别**: warning
- **检测方法**: 在 Entry 层文件中检测含有以下业务术语的条件判断：`balance`、`inventory`/`stock`、`status`、`state`、`permission`、`role`、`expired`、`limit`、`quota`。排除格式类校验关键词。

### G-06: 数据层不做业务验证

- **规则**: Repository/DAO 中不得包含业务逻辑条件判断。数据层只负责 CRUD 操作，业务规则在 Business 层处理。
- **严重级别**: warning
- **检测方法**: 在 Data 层文件中检测 if/else 条件语句。排除以下合法情况：null/empty 防御性编程、数据库异常处理、分页参数处理。剩余的条件分支标记为疑似业务逻辑。

---

## 分层验证原则（宽进严出）

应用 Postel's Law（宽进严出）于服务端分层，确定每一层的校验职责边界。

### 入口层 (Entry Layer) — 格式校验

负责执行格式类校验，确保输入数据格式正确后传递给业务层：

- **Null check**: 必填字段是否为空
- **Length check**: 字符串长度、集合大小
- **Regex check**: 邮箱格式、手机号格式、身份证格式
- **Type check**: 数值范围、日期格式、枚举值

将格式校验放在入口层的原因：Business 层可能被多个入口复用（REST API、gRPC、MQ Consumer），每个入口的格式要求可能不同。在入口层完成格式校验，使 Business 层可专注于业务逻辑。

### 业务层 (Business Layer) — 业务规则校验

负责执行业务规则校验，保证业务操作的合法性：

- **余额校验**: 账户余额是否足以完成扣款
- **库存校验**: 商品库存是否足以完成下单
- **状态流转**: 订单状态 PENDING → PAID 是否合法（不能 CANCELLED → PAID）
- **权限校验**: 用户角色是否有权执行该操作
- **业务唯一性**: 业务层面的去重判断（如一个用户不能重复报名）

将业务规则放在业务层的原因：业务规则跟随业务逻辑，与入口形式无关。无论请求来自 HTTP、gRPC 还是消息队列，业务规则保持一致。

### 数据层 (Data Layer) — 数据完整性

只负责数据存储层面的约束：

- **Unique constraint**: 数据库唯一索引
- **Foreign key**: 外键约束
- **Type constraint**: 字段类型、长度限制
- **Not null constraint**: 数据库层面的非空约束

禁止在数据层执行业务验证。数据层的 Repository/DAO 只进行数据存取，不判断业务条件。

---

## 检测模式（按语言）

各语言的 import/依赖检测 grep 模式：

### Java
```
# import 语句
grep -rn "^import\s" --include="*.java"
# 匹配包名层级：controller/service/repository/domain
pattern: ^import\s+[\w.]+\.(controller|service|repository|dao|domain|infrastructure|application)\.
```

### Go
```
# import 语句
grep -rn "\"[\w/]+\"" --include="*.go"
# 匹配包路径中的层级目录
pattern: "[\w/]+/(handler|controller|service|repository|dao|domain|infrastructure)"
```

### Node.js / TypeScript
```
# import/require 语句
grep -rn "import\s.*from\|require(" --include="*.ts" --include="*.js"
# 匹配路径中的层级目录
pattern: (import|require).*['"]\.\./*(controllers?|services?|repositories?|models?|domain|infrastructure)
```

### Python
```
# import 语句
grep -rn "^from\s\|^import\s" --include="*.py"
# 匹配模块路径中的层级
pattern: ^(from|import)\s+[\w.]*\.(controllers?|services?|repositories?|models?|domain|infrastructure)
```

### .NET (C#)
```
# using 语句
grep -rn "^using\s" --include="*.cs"
# 匹配 namespace 层级
pattern: ^using\s+[\w.]+\.(Controllers?|Services?|Repositories?|Domain|Infrastructure)
```

### Rust
```
# use 语句
grep -rn "^use\s" --include="*.rs"
# 匹配 module 路径
pattern: ^use\s+(crate::)?(handlers?|services?|repositories?|domain|infrastructure)
```

---

## 输出格式

Phase 1 检测结果输出为 `phase1-compliance.json`，schema 定义如下：

```json
{
  "architecture": "three-tier | two-tier | ddd | unknown",
  "detectedLayers": ["entry", "business", "data"],
  "violations": [
    {
      "rule": "T-03",
      "severity": "warning",
      "file": "src/main/java/com/example/controller/UserController.java",
      "line": 45,
      "description": "入口层直接访问数据层且包含业务逻辑：Controller 中注入 Repository 并存在库存判断条件分支",
      "evidence": "import com.example.repository.UserRepository",
      "label": "MUST-FIX",
      "suggestion": {
        "pre-launch": "将业务逻辑提取到 UserService，Controller 仅调用 Service 方法",
        "maintenance": "记录为 TECH-DEBT，下次迭代重构时迁移到 Service 层"
      }
    },
    {
      "rule": "G-03",
      "severity": "critical",
      "file": "src/main/java/com/example/service/PaymentService.java",
      "line": 12,
      "description": "硬编码密码字符串",
      "evidence": "String apiKey = \"sk-live-abc123def456\";",
      "label": "MUST-FIX",
      "suggestion": {
        "pre-launch": "将 apiKey 迁移至环境变量或配置中心，代码中通过 @Value 或 os.environ 读取",
        "maintenance": "立即修复——安全风险，不论项目阶段"
      }
    }
  ],
  "summary": {
    "critical": 2,
    "warning": 5,
    "info": 3
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `architecture` | string | 检测到的架构模式 |
| `detectedLayers` | string[] | 识别到的分层 |
| `violations[].rule` | string | 规则 ID（T-01 ~ T-06, W-01 ~ W-03, D-01 ~ D-04, G-01 ~ G-06） |
| `violations[].severity` | string | `critical` / `warning` / `info` |
| `violations[].file` | string | 违规文件路径 |
| `violations[].line` | number | 违规行号 |
| `violations[].description` | string | 中文违规描述 |
| `violations[].evidence` | string | 触发违规的代码片段或 import 语句 |
| `violations[].label` | string | `MUST-FIX`（critical/warning） / `TECH-DEBT`（info 或维护阶段的 warning） |
| `violations[].suggestion` | object | 分阶段修复建议：`pre-launch`（上线前）和 `maintenance`（维护期） |
| `summary` | object | 各严重级别的违规计数 |

### Label 判定规则

- **MUST-FIX**: 所有 critical 违规；warning 违规在 pre-launch 阶段
- **TECH-DEBT**: info 违规；warning 违规在 maintenance 阶段（已上线项目酌情排期）

### Severity 汇总

- **critical**: 架构方向性错误，导致维护成本急剧上升（T-01, T-04, D-01, D-02, G-01, G-03 密码类）
- **warning**: 职责越界，当前可工作但长期劣化（T-02, T-03 含业务逻辑, T-05, T-06, G-03 非密码类, G-04, G-05, G-06）
- **info**: 改进建议，提升代码质量（T-03 simple CRUD, W-03 极简项目, G-02）
