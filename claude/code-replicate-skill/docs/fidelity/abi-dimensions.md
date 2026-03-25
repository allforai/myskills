# ABI 兼容性维度

> 仅当 project_archetype 表明项目是 SDK/Library 且目标需要保持 ABI 兼容时由 LLM 加载。
> 适用于：C/Rust FFI 库、JNI 桥接、Dart FFI、React Native NativeModules 等。

## B1 — 函数签名兼容

对比 test-vectors.json 中模型 D（ABI 签名）的向量与目标代码的导出函数：
- 每个导出函数的名称是否完全相同？
- 参数类型和顺序是否 ABI 兼容？
- 返回类型是否相同？
- 调用约定（cdecl/stdcall）是否一致？
- 评分 = 签名匹配的函数数 / 总导出函数数 × 100
- 任何签名不匹配 → critical gap（所有 wrapper 会崩溃）

## B2 — 内存布局兼容

对比源码头文件（.h）中 struct 定义与目标代码中对应 struct：
- 字段名称和类型是否匹配？
- 字段顺序是否相同？（影响内存偏移）
- 是否有正确的对齐标记（`#[repr(C)]` / `__attribute__((packed))` 等）？
- 评分 = 布局匹配的 struct 数 / 总导出 struct 数 × 100

## B3 — 内存所有权模型

对比 test-vectors.json 中 ABI 签名的 `memory_ownership` 与目标代码的实现：
- 每个"SDK 分配 → 调用方释放"的模式是否保留？
- 每个"调用方分配 → SDK 填充"的模式是否保留？
- Rust 的所有权模型（Box::into_raw / Box::from_raw）是否正确对应 C 的 malloc/free？
- 评分 = 所有权模型正确的函数数 / 总涉及内存分配的函数数 × 100

## B4 — Wrapper 集成验证

对比源码 wrapper（iOS/Android/Flutter/RN）的调用方式与目标库的导出：
- 每个 wrapper 的 dlopen/System.loadLibrary/DynamicLibrary.open 能否加载目标库？
- LLM 生成最小集成脚本：调用一个简单导出函数 → 验证链接成功 + 返回值正确
- 无法实际编译 wrapper 时（缺少平台工具链）→ 静态对比 wrapper 的 extern 声明 vs 目标导出
- 评分 = 链接成功的 wrapper 数 / 总 wrapper 数 × 100
