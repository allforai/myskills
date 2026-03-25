# Phase 3: 抽象机会分析

> 本阶段在 Phase 2（重复检测）之后执行。依赖 `tuner-profile.json` 中的层级映射和模块列表，以及 `phase2-duplicates.json` 中已识别的重复项。

Phase 3 从五个维度分析抽象机会：垂直抽象（继承/基类）、横向抽象（组合/工具方法）、接口合并（API 参数化）、验证逻辑规范性、过度抽象检测。同时检测"该抽象没抽象"和"不该抽象却抽象了"两个方向。

---

## 3-1. 垂直抽象（继承/基类）

### 检测目标

找出多个类之间存在 >60% 结构重叠的情况，评估是否适合抽取公共基类。

### 检测方法

1. 从 Phase 2 的重复检测结果中提取已识别的相似类对
2. 对同一层级（通常是 Business 层或 Data 层）的类进行结构签名比对：提取每个类的方法列表，比较方法签名模式（参数类型序列 -> 操作序列 -> 返回类型）
3. 计算结构重叠率：`重叠方法数 / max(类A方法数, 类B方法数) * 100`
4. 重叠率 >60% 的类组标记为垂直抽象候选

### 常见模式

以下是服务端项目中最常见的垂直抽象机会：

**BaseService（CRUD 模板方法）**

最高频的模式。多个 Service 类包含结构相同的 `create`、`update`、`delete`、`getById`、`page` 方法，仅实体类型和少量验证逻辑不同。

**BaseController（通用端点模式）**

多个 Controller 包含相同的 CRUD 端点定义、相同的参数解析逻辑、相同的响应包装。

**BaseEntity（公共字段）**

多个实体类包含相同的基础字段：`id`、`createTime`、`updateTime`、`isDeleted`、`createdBy`、`updatedBy`。这通常是最容易也最安全的垂直抽象。

### 具体示例（Java）

```java
// Before: 3 个 Service 具有相同的 create 流程
// UserService.java
public UserVO create(UserDTO dto) {
    validateUser(dto);           // 验证
    User entity = toEntity(dto); // DTO -> Entity
    setDefaults(entity);         // 设置默认值(createTime, createdBy...)
    userRepo.save(entity);       // 持久化
    return toVO(entity);         // Entity -> VO
}

// OrderService.java
public OrderVO create(OrderDTO dto) {
    validateOrder(dto);
    Order entity = toEntity(dto);
    setDefaults(entity);
    orderRepo.save(entity);
    return toVO(entity);
}

// ProductService.java
public ProductVO create(ProductDTO dto) {
    validateProduct(dto);
    Product entity = toEntity(dto);
    setDefaults(entity);
    productRepo.save(entity);
    return toVO(entity);
}
```

```java
// After: 抽取 BaseService<E, D, V>
public abstract class BaseService<E extends BaseEntity, D, V> {

    protected abstract JpaRepository<E, Long> getRepository();

    public V create(D dto) {
        validate(dto);
        E entity = toEntity(dto);
        setDefaults(entity);
        getRepository().save(entity);
        return toVO(entity);
    }

    public V update(Long id, D dto) {
        E entity = getRepository().findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        validate(dto);
        updateEntity(entity, dto);
        getRepository().save(entity);
        return toVO(entity);
    }

    public void delete(Long id) {
        E entity = getRepository().findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        entity.setIsDeleted(true);
        getRepository().save(entity);
    }

    public V getById(Long id) {
        E entity = getRepository().findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        return toVO(entity);
    }

    public PageResult<V> page(PageQuery query) {
        Page<E> page = getRepository().findAll(buildSpec(query), query.toPageable());
        return PageResult.of(page.map(this::toVO));
    }

    // 子类实现差异部分
    protected abstract void validate(D dto);
    protected abstract E toEntity(D dto);
    protected abstract void updateEntity(E entity, D dto);
    protected abstract V toVO(E entity);

    protected void setDefaults(E entity) {
        entity.setCreateTime(LocalDateTime.now());
        entity.setIsDeleted(false);
    }
}
```

```java
// 子类只需实现差异逻辑
public class UserService extends BaseService<User, UserDTO, UserVO> {
    @Override protected JpaRepository<User, Long> getRepository() { return userRepo; }
    @Override protected void validate(UserDTO dto) { /* 用户特有验证 */ }
    @Override protected User toEntity(UserDTO dto) { /* 用户特有转换 */ }
    @Override protected void updateEntity(User entity, UserDTO dto) { /* 用户特有更新 */ }
    @Override protected UserVO toVO(User entity) { /* 用户特有VO映射 */ }
}
```

### Go 语言中的等价模式

Go 没有继承，使用嵌入 struct + 泛型（Go 1.18+）实现类似效果：

```go
// 通过泛型函数 + interface 约束实现
type Entity interface {
    SetCreateTime(t time.Time)
    SetDeleted(d bool)
}

func Create[E Entity, D any, V any](
    repo Repository[E],
    toEntity func(D) E,
    toVO func(E) V,
    validate func(D) error,
) func(D) (V, error) {
    return func(dto D) (V, error) {
        if err := validate(dto); err != nil { return *new(V), err }
        entity := toEntity(dto)
        entity.SetCreateTime(time.Now())
        if err := repo.Save(entity); err != nil { return *new(V), err }
        return toVO(entity), nil
    }
}
```

### 何时不应抽取基类

识别以下情况时，不建议抽取垂直抽象，即使表面结构相似：

- **业务逻辑即将分化**：当前 create 流程相同，但已知不同实体的 create 逻辑将沿不同方向演化（例如订单 create 即将加入库存锁定、支付流程，而用户 create 保持简单）
- **方法签名相似但语义不同**：`validate()` 虽然签名相同，但各类的验证逻辑完全不同且复杂，抽取基类后 abstract 方法过多，基类变成空壳
- **强制继承破坏单一职责**：某些类已有其他继承关系（框架要求），再加一层继承会导致继承链过深
- **团队对泛型/模板不熟悉**：抽取后代码可读性反而下降，维护成本增加

判断规则：如果抽取基类后，子类需要 override 超过 50% 的模板方法，说明差异大于共性，不应抽取。

---

## 3-2. 横向抽象（组合/工具方法）

### 检测目标

找出散落在多个文件中的相似代码片段，评估是否适合抽取为共享 utility 或 service。

### 检测方法

1. 从 Phase 2 的重复检测结果中提取跨文件的代码片段重复
2. 对非完整方法级别的重复（代码块级别），分析其功能共性
3. 统计同一模式出现的文件数，出现在 >= 3 个文件中的模式优先处理
4. 评估参数化可行性：差异部分是否可以通过参数、回调、配置抽离

### 常见模式

**Excel/CSV 导出逻辑**

多个 Controller 或 Service 中包含相似的导出流程：查询数据 -> 构建表头 -> 填充行 -> 设置样式 -> 写入流 -> 返回响应。差异仅在于查询方法、列定义、数据映射。

```
// 散落在 UserController, OrderController, ProductController 中
query data → build header → fill rows → set style → write stream → response
```

建议：抽取 `ExportService.export(query, columnDefs, rowMapper)` 或 `ExcelExportUtil`。

**分页参数解析**

多处手动解析 `pageNum`、`pageSize`、`sortField`、`sortOrder`，做默认值处理和范围校验。

建议：抽取 `PageQuery` 值对象，统一在入口层解析。对于 Spring Boot 项目使用 `Pageable` 参数解析器；对于 Go 项目使用 middleware 统一解析。

**响应包装**

多处手动构建统一响应格式 `{ code, message, data }`，包括成功响应和错误响应。

建议：抽取 `Result<T>` 响应包装类 + 全局异常处理器，Controller 方法直接返回业务数据，包装由框架层自动处理。

**文件上传处理**

多处包含相同的文件校验（大小、类型）、存储路径生成、保存逻辑。

建议：抽取 `FileStorageService`，提供 `upload(file, config)` 方法，config 包含允许的类型、大小限制、存储策略。

**日期/时间格式化**

多处包含相同的日期解析和格式化逻辑，尤其是处理多种输入格式的场景。

建议：抽取 `DateTimeUtil`，或统一使用框架级 serializer/deserializer 配置。

### 抽取原则

- 将差异部分参数化：通过方法参数、泛型、回调函数（Function/Consumer）、配置对象传入差异
- 保持工具方法无状态：不依赖类成员变量，纯输入输出
- 考虑职责归属：通用技术逻辑放 Utility 层，涉及业务概念的放 Business 层的共享 Service
- 命名反映功能而非调用者：用 `ExcelExportUtil` 而非 `UserExportHelper`

---

## 3-3. 接口合并（API 参数化）

### 检测目标

找出多个 API 端点逻辑完全相同、仅实体/资源类型不同的情况，评估是否可合并为参数化接口。

### 检测方法

1. 提取所有 Controller/Handler 的端点方法
2. 比较端点方法的操作序列签名（忽略具体实体类型）
3. 操作序列完全相同且 >= 3 个端点匹配时，标记为合并候选

### 典型模式

```
GET  /user/page    → parsePageParams → buildQuery → repo.page → wrapResponse
GET  /order/page   → parsePageParams → buildQuery → repo.page → wrapResponse
GET  /product/page → parsePageParams → buildQuery → repo.page → wrapResponse

POST /user/export    → queryAll → buildExcel → streamResponse
POST /order/export   → queryAll → buildExcel → streamResponse
POST /product/export → queryAll → buildExcel → streamResponse

GET  /user/{id}    → repo.findById → checkNull → toVO → wrapResponse
GET  /order/{id}   → repo.findById → checkNull → toVO → wrapResponse
GET  /product/{id} → repo.findById → checkNull → toVO → wrapResponse
```

### 合并策略（按语言）

**Java / Spring Boot**

方案 A：泛型 Controller 基类

```java
public abstract class BaseCrudController<E, D, V> {
    protected abstract BaseService<E, D, V> getService();

    @GetMapping("/page")
    public PageResult<V> page(PageQuery query) {
        return getService().page(query);
    }

    @GetMapping("/{id}")
    public V getById(@PathVariable Long id) {
        return getService().getById(id);
    }

    @PostMapping
    public V create(@RequestBody @Valid D dto) {
        return getService().create(dto);
    }
}
```

方案 B：共享 Mixin/Trait（Kotlin interface with default methods）

方案 C：通用 middleware + 路由配置（适合高度动态的场景）

**Go / Gin or Echo**

使用高阶函数生成 handler：

```go
func CrudHandlers[E Entity, D any, V any](svc Service[E, D, V]) {
    return func(r *gin.RouterGroup) {
        r.GET("/page", PageHandler(svc))
        r.GET("/:id", GetByIdHandler(svc))
        r.POST("", CreateHandler(svc))
    }
}
```

**Node.js / NestJS**

使用 Mixin 模式或动态 module：

```typescript
function CrudController<E, D, V>(entityCls: Type<E>): Type<ICrudController<D, V>> {
    class BaseCrud implements ICrudController<D, V> {
        constructor(private service: BaseService<E, D, V>) {}
        @Get('page') page(@Query() q: PageQuery) { return this.service.page(q); }
        @Get(':id') getById(@Param('id') id: string) { return this.service.getById(id); }
    }
    return BaseCrud;
}
```

### 何时不应合并

识别以下情况时，不建议合并 API 端点：

- **鉴权策略不同**：用户列表只有管理员可查，订单列表用户自己可查 — 合并后权限控制变复杂
- **过滤条件不同**：用户列表按角色过滤，订单列表按状态+时间过滤，产品列表按分类+价格过滤 — 查询构建器无法统一
- **响应格式不同**：用户返回脱敏信息，订单返回关联商品，产品返回库存信息 — VO 结构差异大
- **性能特征不同**：某些端点需要缓存，某些需要实时查询，某些需要关联查询 — 统一处理会拖慢简单场景或遗漏优化
- **端点即将分化**：业务需求明确不同端点将沿不同方向演化

判断规则：如果合并后需要在通用逻辑中加入 >= 3 个 `if entity == "xxx"` 的分支判断，说明差异已超过共性，不应合并。

---

## 3-4. 验证逻辑分析

### 分层验证原则（宽进严出 / Postel's Law）

验证逻辑的位置和策略直接影响代码质量和可维护性。遵循 Postel's Law（宽进严出）：

- **宽进（入口层）**：接受各种合理的输入格式，做容错处理。执行简单格式校验：非空、长度、正则匹配、类型转换。目的是拦截明显无效的输入，减轻后续层的负担。格式校验放在入口层的原因是业务层可能被多个入口调用（HTTP API、MQ consumer、定时任务、RPC），每个入口的输入格式可能不同，格式校验不应下沉到业务层重复编写。
- **严出（返回值）**：返回给调用方的数据必须结构完整、格式统一。null 值处理一致（是返回 null 还是空集合还是抛异常），错误响应格式统一（统一 error code + message 结构），日期/金额等格式标准化。

### 反模式：严进宽出

入口层对输入格式要求极其严格（不做容错），但输出给前端的数据格式却不统一（有时返回 null，有时返回空数组，有时字段缺失）。这是最常见的验证反模式。

### 检查项

| 检查项 | 问题描述 | 检测方法 |
|--------|----------|----------|
| 验证逻辑位置是否合理 | 格式校验（regex、length、null check）出现在 Service/Business 层 | 在 Business layer files 中 grep regex patterns、`.length()`/`len()`、`== null`/`== nil` 等格式校验特征 |
| 业务校验位置是否合理 | 业务规则（余额、库存、状态流转）出现在 Controller/Entry 层 | 在 Entry layer files 中 grep balance、inventory、stock、status 等业务概念 |
| 验证逻辑是否重复 | 同一字段在多处重复校验 | 找相同的正则表达式或相同字段名的校验逻辑出现在多个文件中 |
| 是否严进宽出（反模式） | 入口层严格拒绝各种输入，但输出格式却不一致 | 检查返回值中 null vs `[]` vs `{}` 的混用、日期格式不统一、error 结构不统一 |
| 错误响应是否统一 | 验证失败时的响应格式不一致 | 检查异常处理返回值格式：有的返回 `{code, msg}`，有的返回 `{error}`，有的直接返回 string |
| 校验注解/装饰器是否生效 | 声明了 `@Valid` / `@Validated` 等注解但未触发 | 检查 Controller 参数是否有 `@Valid`（Java）、`validate` pipe（NestJS）、binding tag（Go） |

### 检测流程

1. 从 `tuner-profile.json` 获取层级映射，确定每个文件属于哪一层
2. 在 Entry layer 文件中搜索业务概念关键词（balance, inventory, stock, status, permission 等），标记为"业务校验位置不当"
3. 在 Business layer 文件中搜索格式校验特征（regex, length, pattern, email format, phone format 等），标记为"格式校验位置不当"
4. 跨文件搜索相同的正则表达式或相同字段名 + 校验方法的组合，标记为"验证逻辑重复"
5. 分析返回值格式一致性：抽样检查各端点的成功响应和错误响应格式
6. 汇总验证问题，生成建议

### 验证模式（按语言/框架）

不同技术栈有不同的验证最佳实践，检测时需识别并匹配：

**Java / Spring Boot**

- Bean Validation（JSR 380）：`@NotNull`、`@NotBlank`、`@Size`、`@Pattern`、`@Email`、`@Min`、`@Max`
- 分组校验：`@Validated(CreateGroup.class)` 区分新增和更新的校验规则
- 自定义 Validator：实现 `ConstraintValidator` 接口
- 全局异常处理：`@ControllerAdvice` + `@ExceptionHandler(MethodArgumentNotValidException.class)`

检测要点：检查是否使用了 Bean Validation 而非手写 if-else 校验；检查 `@Valid` / `@Validated` 是否遗漏。

**Go**

- struct tags：`validate:"required,min=1,max=100"`（配合 go-playground/validator）
- 自定义 middleware 校验
- 手动校验函数

检测要点：检查是否统一使用 validator 库而非散落的 if 判断；检查 struct tag 是否完整。

**Node.js / TypeScript**

- class-validator decorators：`@IsNotEmpty()`、`@IsEmail()`、`@MinLength()`
- Joi schema validation
- Zod schema validation
- NestJS ValidationPipe（全局或局部）

检测要点：检查是否有统一的 validation pipe；检查 DTO class 是否使用了装饰器。

**Python**

- Pydantic validators（v2: `@field_validator`）
- Django forms / serializers（`serializers.CharField(max_length=100)`）
- marshmallow schemas
- 手动 raise ValueError / ValidationError

检测要点：检查是否使用了框架级验证而非手写 if-raise；检查 Pydantic model 的 field 约束是否完整。

**.NET / C#**

- Data Annotations：`[Required]`、`[StringLength]`、`[RegularExpression]`
- FluentValidation：`RuleFor(x => x.Name).NotEmpty().MaximumLength(100)`
- 自定义 ActionFilter

检测要点：检查是否使用了 Data Annotations 或 FluentValidation；检查 `[ApiController]` 是否启用了自动模型验证。

---

## 3-5. 过度抽象检测（反向检查）

### 检测目标

在检测"缺少抽象"的同时，反向检测"过度抽象"——不必要的复杂性。过度抽象同样是代码质量问题，增加阅读成本、维护成本、调试难度。

### 检查项

| 坏味道 | 检测方法 | 建议 |
|--------|----------|------|
| 只有 1 个实现的接口 | 找所有 interface/trait/protocol 定义，统计其 implements/实现类数量 | 无需接口，直接用具体类。例外：DDD 中 Domain 定义接口、Infrastructure 实现 → 合理（依赖倒置） |
| 只被调用 1 次的工具方法 | 在 Utility 层找所有 public 方法，统计每个方法在整个项目中的调用次数 | 内联回唯一调用处。工具方法的价值在于复用，只用一次则没有抽取意义 |
| 层层转发无增值 | 找 Service 方法，检查方法体是否仅 `return repo.xxx()` 或仅调用一个下层方法无额外逻辑 | 跳过中间层，让上层直接调下层（参考 T-03 规则）。除非该 Service 方法是事务边界或有明确的扩展计划 |
| 过深的继承链 (>3 层) | 分析 `extends`/`implements`/`embed` 链的深度，从具体类向上追溯到根基类 | 优先使用组合替代继承。超过 3 层的继承链通常意味着职责划分有问题 |
| 不必要的 Builder/Factory | 找 Builder pattern 或 Factory pattern 的实现，检查是否只有 1 种构建方式 | 只有 1 种构建方式时直接用构造函数或 static factory method，无需完整 Builder |
| 不必要的 Event/Observer | 找事件发布/订阅机制，检查某事件是否只有 1 个 subscriber | 只有 1 个 subscriber 时直接方法调用即可，事件机制增加了调试追踪难度 |
| 空 abstract method 过多的基类 | 统计基类中 abstract method 占比，超过 70% 则基类几乎无共享逻辑 | 基类变成纯接口定义，无共享实现 → 改用接口；或基类 abstract method 过多说明子类差异大于共性，不应强行抽取 |

### 检测流程

1. **单实现接口检测**

   扫描所有 interface/trait/abstract class 定义。对每个定义，在整个项目中搜索 `implements`/`extends`/嵌入引用。统计实现数量。

   ```
   interface PaymentGateway → 实现: StripeGateway, AlipayGateway → 合理（多实现）
   interface UserService    → 实现: UserServiceImpl              → 可疑（单实现）
   ```

2. **单次调用工具方法检测**

   扫描 Utility 层所有 public 方法。对每个方法名，在整个项目中 grep 调用点（排除定义本身）。调用次数 == 1 时标记。

3. **透传方法检测**

   扫描 Business layer 的所有方法。分析方法体：如果方法体只有 1 行且该行是调用 Data layer 的方法并直接返回结果（可能有简单的参数转发），标记为透传。

   ```java
   // 透传示例
   public User getById(Long id) { return userRepo.findById(id).orElse(null); }
   // 非透传（有业务逻辑）
   public User getById(Long id) {
       User user = userRepo.findById(id).orElseThrow(...);
       checkPermission(user);
       return user;
   }
   ```

4. **继承深度检测**

   从每个具体类出发，沿 extends 链向上遍历，记录深度。框架基类（如 Spring 的 `JpaRepository`、Django 的 `ModelViewSet`）不计入深度，只统计项目内自定义的继承层级。

5. **Builder/Factory 必要性检测**

   找所有 Builder class 和 Factory class。检查 Builder 是否只有一种 build 路径（所有字段都在一个 build 方法中设置）。检查 Factory 是否只创建一种类型的对象。

### 何时接口是合理的（即使只有 1 个实现）

不是所有单实现接口都需要消除。以下情况是合理的：

- **DDD 依赖倒置**：Domain 层定义 Repository 接口，Infrastructure 层提供实现。即使只有一个实现，接口的目的是保持 Domain 层的纯净性和可替换性。这是架构约束，不是过度设计。
- **明确的多实现计划**：当前只有 Redis 缓存实现，但路线图中明确计划添加 Memory 缓存和 Memcached 实现。接口为未来扩展做准备。
- **外部依赖隔离**：封装第三方 SDK（支付、短信、OSS）的接口，即使当前只对接一个供应商，接口便于未来切换供应商。
- **测试需要**：需要 mock 的依赖通过接口注入。但注意现代测试框架（Mockito、gomock、jest）可以 mock 具体类，不一定需要接口。评估具体测试框架能力后再判断。

判断规则：如果移除接口后，代码的可维护性和可测试性没有实质性下降，则接口是不必要的。

---

## 输出格式

分析完成后，将结果写入 `.allforai/code-tuner/phase3-abstractions.json`。Schema 如下：

```json
{
  "vertical_abstractions": [
    {
      "id": "ABS-V-001",
      "candidates": ["UserService", "OrderService", "ProductService"],
      "overlap_percentage": 75,
      "overlapping_methods": ["create", "update", "delete", "getById", "page"],
      "diverging_methods": ["UserService.resetPassword", "OrderService.cancelOrder"],
      "suggested_base": "BaseService<E, D, V>",
      "estimated_reduction_lines": 120,
      "suggestion": {
        "pre-launch": "抽取 BaseService<E, D, V> 基类，将 CRUD 模板方法统一。子类只实现 validate/toEntity/toVO。预计减少 120 行重复代码。",
        "maintenance": "标记为重构机会。当下次修改任一 Service 的 CRUD 逻辑时，同步抽取基类。预计减少 120 行重复代码，消除 3 处重复。"
      }
    }
  ],
  "horizontal_abstractions": [
    {
      "id": "ABS-H-001",
      "pattern": "Excel export logic",
      "occurrences": [
        {"file": "UserController.java", "line": 45, "method": "exportUsers"},
        {"file": "OrderController.java", "line": 67, "method": "exportOrders"},
        {"file": "ProductController.java", "line": 32, "method": "exportProducts"}
      ],
      "similarity_percentage": 85,
      "suggested_extraction": "ExcelExportService.export(queryFn, columnDefs, rowMapper)",
      "estimated_reduction_lines": 90,
      "suggestion": {
        "pre-launch": "抽取 ExcelExportService，参数化查询函数、列定义、行映射。3 处调用改为委托调用。",
        "maintenance": "抽取 ExcelExportService，原调用点改为委托。不改变外部行为，风险低。"
      }
    }
  ],
  "api_consolidations": [
    {
      "id": "ABS-A-001",
      "endpoints": [
        "GET /user/page",
        "GET /order/page",
        "GET /product/page"
      ],
      "operation_signature": "parsePageParams → buildQuery → repo.page → wrapResponse",
      "suggested_approach": "generic BaseCrudController<E, D, V> with /page endpoint",
      "blockers": [],
      "suggestion": {
        "pre-launch": "抽取 BaseCrudController<E, D, V>，统一分页端点。子 Controller 继承并指定泛型参数。",
        "maintenance": "创建 BaseCrudController 后逐步迁移，每次迁移一个 Controller 并回归测试。"
      }
    }
  ],
  "validation_issues": [
    {
      "id": "VAL-001",
      "type": "wrong-layer",
      "subtype": "format-in-business",
      "file": "UserService.java",
      "line": 23,
      "code_snippet": "if (dto.getEmail() == null || !dto.getEmail().matches(\"^[\\\\w@.]+$\")) { throw ... }",
      "description": "格式校验（email 正则匹配）出现在 Business 层。应移至 Entry 层使用 @Email 注解。",
      "suggestion": "在 UserDTO 的 email 字段添加 @NotNull @Email 注解，删除 Service 中的手动校验。"
    },
    {
      "id": "VAL-002",
      "type": "duplicate",
      "file": "OrderController.java",
      "line": 15,
      "related_files": ["OrderService.java:34"],
      "description": "orderId 非空校验在 Controller 和 Service 中重复出现。",
      "suggestion": "只在 Controller 层（入口层）保留 @NotNull 校验，Service 层移除。"
    },
    {
      "id": "VAL-003",
      "type": "strict-in-loose-out",
      "file": "ProductController.java",
      "line": 78,
      "description": "入口层严格拒绝不带分页参数的请求，但分页响应在无数据时有时返回 null 有时返回空 []。",
      "suggestion": "统一分页响应格式：无数据时返回 { list: [], total: 0, page: 1 }，不返回 null。"
    },
    {
      "id": "VAL-004",
      "type": "inconsistent-error",
      "file": "multiple",
      "description": "验证失败时，UserController 返回 {code: 400, msg: '...'}, OrderController 返回 {error: '...'}，格式不统一。",
      "suggestion": "实现全局异常处理器（@ControllerAdvice），统一验证异常响应格式为 {code, message, details}。"
    }
  ],
  "over_abstractions": [
    {
      "id": "OVER-001",
      "type": "single-impl-interface",
      "file": "UserService.java",
      "interface_file": "IUserService.java",
      "description": "IUserService 接口只有 UserServiceImpl 一个实现，且不属于 DDD 依赖倒置场景。",
      "suggestion": "删除 IUserService 接口，直接使用 UserService 具体类。其他类注入 UserService 而非 IUserService。"
    },
    {
      "id": "OVER-002",
      "type": "single-use-util",
      "file": "StringUtils.java",
      "method": "formatOrderNumber",
      "call_count": 1,
      "caller": "OrderService.java:56",
      "description": "StringUtils.formatOrderNumber() 只在 OrderService 中调用 1 次。",
      "suggestion": "将 formatOrderNumber 逻辑内联到 OrderService 中。如果未来有复用需求再抽取。"
    },
    {
      "id": "OVER-003",
      "type": "passthrough",
      "file": "ProductService.java",
      "method": "getById",
      "description": "ProductService.getById(id) 仅 return productRepo.findById(id)，无任何业务逻辑。",
      "suggestion": "让 Controller 直接调用 productRepo.findById(id)，跳过 Service 层透传。（参考 T-03 规则）"
    },
    {
      "id": "OVER-004",
      "type": "deep-inheritance",
      "file": "VipOrderService.java",
      "chain": "VipOrderService → OrderService → BaseService → AbstractEntity",
      "depth": 4,
      "description": "继承链深度为 4 层（不含框架类），超过 3 层阈值。",
      "suggestion": "将 VipOrderService 的差异逻辑改为组合模式（注入策略对象），而非继承 OrderService。"
    },
    {
      "id": "OVER-005",
      "type": "unnecessary-builder",
      "file": "UserBuilder.java",
      "description": "UserBuilder 只有 1 种构建方式，所有字段都在一次调用链中设置。",
      "suggestion": "删除 UserBuilder，使用构造函数或 static factory method：User.of(name, email, role)。"
    }
  ]
}
```

### 字段说明

- `id`：唯一标识符。垂直抽象用 `ABS-V-NNN`，横向抽象用 `ABS-H-NNN`，接口合并用 `ABS-A-NNN`，验证问题用 `VAL-NNN`，过度抽象用 `OVER-NNN`
- `type`：问题分类，用于过滤和统计
- `suggestion`：对象形式，包含 `pre-launch` 和 `maintenance` 两种模式下的不同建议
- `estimated_reduction_lines`：预估可减少的代码行数（仅抽象类问题包含此字段）
- 验证问题的 `type` 取值：`wrong-layer`（校验位置不当）、`duplicate`（重复校验）、`strict-in-loose-out`（严进宽出反模式）、`inconsistent-error`（错误响应不统一）
- 过度抽象的 `type` 取值：`single-impl-interface`（单实现接口）、`single-use-util`（单次调用工具方法）、`passthrough`（透传方法）、`deep-inheritance`（过深继承链）、`unnecessary-builder`（不必要的 Builder）

---

## 模式区分

Phase 3 的每条发现都必须提供两种模式下的差异化建议：

### Pre-launch 模式

- 积极建议实施抽象，提供目标代码结构
- 建议重组目录结构（如创建 `base/` 目录存放基类）
- 建议引入新的设计模式（策略模式替代继承链、模板方法模式统一流程）
- 对过度抽象直接建议删除/简化
- 给出预估减少的代码行数和受影响的文件数
- 提供具体的目标代码骨架（伪代码或模板）

### Maintenance 模式

- 仅标记抽象机会和预期收益（减少 N 行代码 / 消除 N 处重复），不建议大规模重写
- 建议增量式重构：下次修改相关代码时顺便实施
- 对过度抽象评估移除风险：涉及多少调用点、是否有外部依赖该接口
- 验证问题按影响范围排序：全局性问题（错误响应不统一）优先于局部问题（某个字段重复校验）
- 不建议修改已稳定运行的代码，除非有明确的 bug 或性能问题

### 优先级排序

无论哪种模式，发现项按以下优先级排序：

1. 验证问题中的 `wrong-layer`（影响正确性）
2. 验证问题中的 `inconsistent-error`（影响 API 一致性）
3. 过度抽象中的 `passthrough`（简单修复，收益明确）
4. 垂直/横向抽象（减少重复代码量最大的优先）
5. 接口合并（通常改动范围大，优先级较低）
6. 过度抽象中的 `single-impl-interface`（移除风险需评估）
7. 验证问题中的 `duplicate`（不影响正确性，只是冗余）

---

## 与其他 Phase 的关系

- **Phase 2 -> Phase 3**：Phase 2 的重复检测结果是 Phase 3 的输入。Phase 2 识别出的重复对，Phase 3 进一步分析是否适合抽象以及抽象方式。
- **Phase 1 -> Phase 3**：Phase 1 的层级违规结果用于辅助验证逻辑分析（已知哪些文件属于哪一层）。Phase 1 中 T-03（简单 CRUD 跳层）的判断结果与 Phase 3 的透传方法检测互相印证。
- **Phase 3 -> Phase 4**：Phase 3 的所有发现项进入 Phase 4 的评分计算（抽象合理度、验证规范度两个维度）和重构任务清单生成。
