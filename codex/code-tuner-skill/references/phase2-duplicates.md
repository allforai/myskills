# Phase 2: 重复代码检测 (Duplication Detection)

对服务端代码进行结构化重复检测，覆盖 Entry（API/入口）、Business（业务）、Data（数据）、Utility（工具）四层。核心思路：不做逐行 diff，而是提取方法的**结构签名**进行相似度比对，阈值 70%。

---

## 2-1. API/入口层重复

### 检测模式

#### 模式 A：相似的导出逻辑

多个 Controller 各自实现 export 方法，内部逻辑均为 query → transform → write Excel → return stream。仅 entity 名称和查询条件不同。

**Java (Spring Boot) 示例：**

```java
// UserController.java
@GetMapping("/users/export")
public void exportUsers(HttpServletResponse response, UserQuery query) {
    List<User> list = userService.list(query);
    List<UserExcelVO> voList = list.stream().map(UserExcelVO::from).collect(toList());
    ExcelUtil.write(response, "users.xlsx", UserExcelVO.class, voList);
}

// OrderController.java
@GetMapping("/orders/export")
public void exportOrders(HttpServletResponse response, OrderQuery query) {
    List<Order> list = orderService.list(query);
    List<OrderExcelVO> voList = list.stream().map(OrderExcelVO::from).collect(toList());
    ExcelUtil.write(response, "orders.xlsx", OrderExcelVO.class, voList);
}
```

结构签名完全一致：`(Query, Response) → [service.list, stream.map, ExcelUtil.write] → (void)`。

**Node.js (NestJS) 示例：**

```typescript
// user.controller.ts
@Get('users/export')
async exportUsers(@Query() query: UserQueryDto, @Res() res: Response) {
  const list = await this.userService.findAll(query);
  const rows = list.map(toUserExcelRow);
  const buffer = await generateExcel(rows, UserColumns);
  res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  res.send(buffer);
}

// order.controller.ts
@Get('orders/export')
async exportOrders(@Query() query: OrderQueryDto, @Res() res: Response) {
  const list = await this.orderService.findAll(query);
  const rows = list.map(toOrderExcelRow);
  const buffer = await generateExcel(rows, OrderColumns);
  res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  res.send(buffer);
}
```

#### 模式 B：相似的分页/排序/过滤实现

每个 Controller 各自解析 `page`、`size`、`sort`、`filter` 参数，手动构造分页对象。

```java
// 在多个 Controller 中重复出现
int page = query.getPage() != null ? query.getPage() : 1;
int size = query.getSize() != null ? query.getSize() : 20;
String sort = query.getSort() != null ? query.getSort() : "id";
String direction = query.getDirection() != null ? query.getDirection() : "DESC";
PageRequest pageRequest = PageRequest.of(page - 1, size, Sort.by(Sort.Direction.fromString(direction), sort));
```

#### 模式 C：相似的 CRUD endpoint handler

每个 Controller 的 create / update / delete 方法遵循相同流程：validate input → call service → wrap response。

```java
// 几乎每个 Controller 都有这种结构
@PostMapping
public Result<UserVO> create(@Valid @RequestBody UserCreateDTO dto) {
    return Result.ok(userService.create(dto));
}

@PutMapping("/{id}")
public Result<UserVO> update(@PathVariable Long id, @Valid @RequestBody UserUpdateDTO dto) {
    return Result.ok(userService.update(id, dto));
}

@DeleteMapping("/{id}")
public Result<Void> delete(@PathVariable Long id) {
    userService.delete(id);
    return Result.ok();
}
```

### 合并策略

| 模式 | 合并方式 | 说明 |
|------|---------|------|
| 相似导出 | 创建通用 `ExportController`，接收 module 参数 | `GET /export?module=user&query=...`，内部通过策略模式路由到对应 Service |
| 相似分页 | 提取 `PageableResolver` 工具类或自定义 `@PageableDefault` 注解 | 统一解析逻辑，Controller 直接接收 `Pageable` 对象 |
| 相似 CRUD | 创建 `BaseCrudController<E, CreateDTO, UpdateDTO, VO>`，子类仅声明泛型 | NestJS 中可用 mixin 模式实现 |

---

## 2-2. 业务层重复

### 检测模式

#### 模式 A：相似的 CRUD 流程

多个 Service 的 create/update/getById 方法内部步骤完全一致，仅 entity 类型不同。

```java
// UserService.java
public UserVO create(UserCreateDTO dto) {
    validateCreate(dto);           // 1. validate
    User entity = toEntity(dto);   // 2. transform
    setDefaults(entity);           // 3. set defaults
    userRepo.save(entity);         // 4. save
    return toVO(entity);           // 5. transform to VO
}

// OrderService.java
public OrderVO create(OrderCreateDTO dto) {
    validateCreate(dto);           // 1. validate
    Order entity = toEntity(dto);  // 2. transform
    setDefaults(entity);           // 3. set defaults
    orderRepo.save(entity);        // 4. save
    return toVO(entity);           // 5. transform to VO
}
```

结构签名：`(CreateDTO) → [validate, toEntity, setDefaults, repo.save, toVO] → (VO)`，相似度 100%。

#### 模式 B：复制粘贴仅改 entity 名称

典型表现为方法体结构完全相同，仅将 `User` 替换为 `Order`、`userRepo` 替换为 `orderRepo`。扫描时提取操作序列（去除具体类型名称）即可发现。

#### 模式 C：相似的业务规则

状态机、审批流等结构性相似的业务逻辑。例如订单审批和退款审批都实现了 `submit → review → approve/reject → complete` 的状态流转，内部校验与通知逻辑结构一致。

#### 模式 D：Passthrough Service 检测（T-03 规则）

识别仅做透传的 Service 方法——方法体只调用一个 Repository/DAO 方法并直接返回结果，无任何业务逻辑。

**Passthrough 示例（应标记）：**

```java
// UserService.java — passthrough，无业务逻辑
public User getById(Long id) {
    return userRepository.findById(id).orElseThrow(() -> new NotFoundException("User not found"));
}
```

```typescript
// user.service.ts — passthrough
async findById(id: string): Promise<User> {
  return this.userRepository.findOneOrFail({ where: { id } });
}
```

上述方法仅做 Repository 调用 + 异常包装，无校验、无转换、无副作用。建议移除该 Service 方法，让 Entry 层直接调用 Data 层。

**合法 Service 逻辑示例（不应标记）：**

```java
// UserService.java — 有真实业务逻辑
public UserVO getById(Long id) {
    User user = userRepository.findById(id)
        .orElseThrow(() -> new NotFoundException("User not found"));
    enrichWithDepartment(user);       // 关联查询
    auditService.logAccess(id);       // 副作用：审计日志
    return UserVO.from(user);         // 数据转换
}
```

判定标准：方法内除 repository 调用外，存在**额外操作**（关联查询、副作用、数据转换、权限校验等）则为合法 Service 逻辑。

---

## 2-3. 数据层重复

### 检测模式

#### 模式 A：相似的查询逻辑

多个 Repository/DAO 的查询方法仅在表名和条件字段上不同，查询结构（JOIN、WHERE 组合方式、分页排序）完全一致。

```java
// UserRepository
@Query("SELECT u FROM User u WHERE u.status = :status AND u.name LIKE :keyword ORDER BY u.createdAt DESC")
Page<User> search(@Param("status") Integer status, @Param("keyword") String keyword, Pageable pageable);

// OrderRepository
@Query("SELECT o FROM Order o WHERE o.status = :status AND o.title LIKE :keyword ORDER BY o.createdAt DESC")
Page<Order> search(@Param("status") Integer status, @Param("keyword") String keyword, Pageable pageable);
```

#### 模式 B：重复的分页/排序/过滤逻辑

Data 层各自实现分页参数处理，而非统一委托给框架或共享工具。

#### 模式 C：DTO/VO 字段高度重叠

多个 DTO 或 VO 之间字段重合度超过 70%。

**检测方法（Jaccard 相似度）：**

1. 提取每个 DTO/VO 的所有字段名集合，例如：
   - `UserDTO = {id, name, email, phone, status, createdAt, updatedAt, avatar, role, department}`
   - `UserVO = {id, name, email, phone, status, createdAt, updatedAt, avatar}`
2. 计算 Jaccard 系数：`J = |A ∩ B| / |A ∪ B|`
   - 交集：`{id, name, email, phone, status, createdAt, updatedAt, avatar}` = 8 个
   - 并集：`{id, name, email, phone, status, createdAt, updatedAt, avatar, role, department}` = 10 个
   - `J = 8 / 10 = 0.80` → 超过 70% 阈值 → 标记

> 注意：跨层的 Entity ↔ DTO 重叠属于架构设计意图，见「误判排除」一节。仅对**同层或相邻层的非 Entity 类型**计算。

#### 模式 D：相似的 mapper/converter 方法

多个 converter 类中存在结构一致的字段映射方法，逐字段 set/get 且映射方式无差异。

---

## 2-4. 工具类重复

### 检测模式

#### 模式 A：不同包中的同名工具类

多个模块各自包含功能相同的工具类，例如 `com.app.user.util.DateUtils` 和 `com.app.order.util.DateUtils` 内部方法签名和实现一致。

**检测方法：**
1. 扫描所有以 `Utils`、`Helper`、`Tool`、`Common` 结尾（或在 `util`/`utils`/`common`/`shared`/`helper` 目录下）的类/文件。
2. 提取方法签名列表。
3. 对不同文件中的同名方法做签名比对（参数类型 + 返回类型 + 操作序列）。
4. 签名匹配度 > 70% 即标记。

#### 模式 B：重新实现已有依赖的能力

项目依赖中已包含 Apache Commons Lang、Guava、Lodash 等工具库，但代码中自行实现了相同功能。

检测方式：维护常见工具库的 API 清单，扫描自定义工具方法的签名和功能描述，匹配已有库中的等价方法。

常见案例：
- 自定义 `StringUtils.isEmpty()` vs `org.apache.commons.lang3.StringUtils.isEmpty()`
- 自定义 `CollectionUtils.partition()` vs `com.google.common.collect.Lists.partition()`
- 自定义 `deepClone()` vs `lodash.cloneDeep()`

#### 模式 C：跨模块复制工具类

同一个工具类文件被复制到多个模块，而非抽取为 shared module 引用。通过文件内容 hash 或方法签名集合相似度检测。

---

## 结构签名方法

### 核心算法

结构签名（Structural Signature）是 Phase 2 的核心检测手段，用于避免逐行 diff 带来的噪音（变量命名、空格、注释差异等），聚焦于方法的**行为结构**。

**提取步骤：**

1. **解析入参类型**：提取方法参数的抽象类型（DTO、ID、Query 等），忽略具体类名。
2. **识别操作序列**：按执行顺序提取方法体内的操作类型：
   - `validate` — 参数校验、断言
   - `query` / `db-read` — 数据库读取
   - `db-write` / `save` — 数据库写入
   - `api-call` — 外部 API 调用
   - `transform` / `map` — 数据转换
   - `setDefaults` — 默认值设置
   - `notify` — 消息/事件发送
   - `log` — 日志记录
   - `cache-read` / `cache-write` — 缓存操作
3. **提取返回类型**：抽象为 VO、Entity、void、List、Page 等。
4. **生成签名字符串**：`(抽象入参) → [操作序列] → (抽象返回)`。

**比对方式：**

对两个签名中的操作序列计算编辑距离（Levenshtein distance），归一化后得到相似度。阈值设定为 **70%**——高于 70% 即判定为候选重复对。

### 示例

```
UserService.create:    (CreateDTO) → [validate, transform, setDefaults, db-write, transform] → (VO)
OrderService.create:   (CreateDTO) → [validate, transform, setDefaults, db-write, transform] → (VO)
Similarity: 100% → 候选重复

UserService.update:    (ID, UpdateDTO) → [db-read, validate, merge, db-write, transform] → (VO)
ProductService.update: (ID, UpdateDTO) → [db-read, validate, merge, db-write, transform, notify] → (VO)
Similarity: 5/6 operations match = 83% → 候选重复

UserService.register:  (RegisterDTO) → [validate, transform, db-write, api-call, notify] → (VO)
OrderService.create:   (CreateDTO) → [validate, transform, setDefaults, db-write, transform] → (VO)
Similarity: 2/5 exact position match = 40% → 不标记
```

---

## 误判排除

以下场景**不应**标记为重复：

### 1. 跨层的有意隔离

Entity（Data 层）与 DTO（Entry 层）字段高度重叠属于分层架构的设计意图，不是重复。保持各层独立的数据模型是为了解耦——Data 层 schema 变更不应直接暴露给 API 消费者。

**判定规则：** Entity 与 DTO/VO 之间的字段重叠不计入 DTO overlap 检测。仅对**同层**的多个 DTO 之间或同层多个 VO 之间进行比对。

### 2. 框架强制的样板代码

以下属于框架要求，不构成可消除的重复：
- Spring Boot：`@RestController`、`@Service`、`@Repository` 注解声明
- NestJS：`@Controller()`、`@Injectable()`、`@Module()` 装饰器
- JPA Entity：`@Entity`、`@Table`、`@Column` 注解
- Lombok：`@Data`、`@Builder` 等注解

**判定规则：** 在提取结构签名时，忽略框架注解/装饰器。仅分析方法体内的操作序列。

### 3. 测试代码

测试文件中可能存在大量重复的 setup 逻辑（mock 初始化、测试数据构造），这些重复往往是有意为之，目的是保持测试用例独立可读。

**判定规则：** 对 `*Test.java`、`*Spec.ts`、`*.test.ts`、`*.spec.ts`、`*_test.go` 等测试文件，默认跳过或降低告警级别（severity: `info` 而非 `warning`）。

### 4. 极小方法

单行或两行的简单委托方法（如 getter/setter wrapper）不标记，避免产生过量低价值告警。

**判定规则：** 方法体操作序列长度 < 2 时跳过。

---

## 输出格式

Phase 2 的检测结果输出为 `phase2-duplicates.json`，schema 如下：

```json
{
  "duplicate_pairs": [
    {
      "id": "DUP-001",
      "type": "entry-layer",
      "similarity": 85,
      "file_a": {
        "path": "src/controller/UserController.java",
        "method": "exportUsers",
        "line_start": 45,
        "line_end": 52
      },
      "file_b": {
        "path": "src/controller/OrderController.java",
        "method": "exportOrders",
        "line_start": 38,
        "line_end": 45
      },
      "structural_signature": "(Query, Response) → [service.list, stream.map, ExcelUtil.write] → (void)",
      "suggestion": {
        "pre-launch": "合并为通用 ExportController，接收 module 参数路由到对应 Service",
        "maintenance": "提取 exportTemplate() 方法至 BaseController，原方法标注 @Deprecated 后逐步替换"
      }
    }
  ],
  "passthrough_services": [
    {
      "service_file": "src/service/UserService.java",
      "method": "getById",
      "delegates_to": "userRepository.findById",
      "suggestion": "Remove passthrough, let Entry call Data directly"
    }
  ],
  "dto_overlaps": [
    {
      "dto_a": "src/dto/UserDTO.java",
      "dto_b": "src/dto/UserVO.java",
      "overlap_percentage": 80,
      "shared_fields": ["id", "name", "email", "phone", "status", "createdAt", "updatedAt", "avatar"],
      "suggestion": "提取共享字段为 UserBase，UserDTO extends UserBase 增加 role/department，UserVO extends UserBase"
    }
  ],
  "summary": {
    "total_pairs": 12,
    "by_layer": {
      "entry": 3,
      "business": 5,
      "data": 2,
      "utility": 2
    }
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识，格式 `DUP-NNN` |
| `type` | enum | `entry-layer` / `business-layer` / `data-layer` / `utility` |
| `similarity` | number | 结构相似度百分比（70-100） |
| `file_a` / `file_b` | object | 重复对的两个方法的位置信息 |
| `structural_signature` | string | 匹配的结构签名描述 |
| `suggestion.pre-launch` | string | 上线前模式下的合并建议 |
| `suggestion.maintenance` | string | 维护模式下的渐进式重构建议 |
| `passthrough_services[].delegates_to` | string | 被透传调用的 Repository 方法 |
| `dto_overlaps[].overlap_percentage` | number | Jaccard 相似度百分比 |
| `dto_overlaps[].shared_fields` | array | 重叠的具体字段名列表 |

---

## 模式区分

### Pre-launch 模式（上线前）

项目尚未上线或处于大版本重构期，可承受较大改动范围。

**策略：直接合并/重写。**

- 给出**目标结构**而非增量修改步骤。
- 示例建议：「合并 UserController.export 和 OrderController.export 为 GenericExportController.export(String module, Query query)，通过 Map<String, ExportStrategy> 路由到具体实现。」
- 对 passthrough service 直接建议删除，调用方改为直接引用 Repository。
- 对 DTO overlap 建议提取 base class 或使用组合模式（composition）。

**Pre-launch 输出重点：**
1. 合并后的目标类/方法结构描述。
2. 需要删除的文件或方法列表。
3. 需要修改的调用方列表。

### Maintenance 模式（维护期）

项目已上线运行，需要渐进式重构以控制风险。

**策略：提取共享 → 保留原接口 → 标记废弃 → 逐步替换。**

- 第一步：提取公共逻辑为新方法/类（如 `AbstractCrudService<E, D, V>`）。
- 第二步：原方法内部改为委托调用新方法，保持外部接口不变。
- 第三步：原方法标注 `@Deprecated`（Java）或 `/** @deprecated */`（TypeScript）。
- 第四步：在后续迭代中逐步将调用方切换到新接口，最终删除旧方法。

**Maintenance 输出重点：**
1. 提取出的共享方法/类的建议实现。
2. 原方法的委托改造示例。
3. 废弃标记和替换时间线建议。

---

## 检测优先级

按影响面和修复收益排序检测优先级：

| 优先级 | 类型 | 原因 |
|--------|------|------|
| P0 | Passthrough Service | 违反分层原则（T-03），修复成本最低，收益明确 |
| P1 | 业务层 CRUD 重复 | 影响面最广，通常涉及多个 Service |
| P2 | 入口层重复 | 影响 API 一致性，合并后可减少大量模板代码 |
| P3 | 工具类重复 | 维护风险（修一处漏一处），但影响面相对局部 |
| P4 | DTO/VO 重叠 | 需要权衡改动范围，跨层影响需谨慎 |
| P5 | 数据层查询重复 | 多数可通过泛型 Repository 解决，但需评估 ORM 框架支持度 |
