export const defaultRouting: Record<string, string> = {
  // === 创新流程专用 ===
  // Step 0 Phase C: 假设清零
  assumption_challenge: "qwen",        // 挑战者：中文理解好，能准确识别行业共识
  constraint_classification: "llama",  // 守护者：逻辑分类能力强
  
  // Step 0 Phase B+: 创新机会
  innovation_exploration: "qwen",      // 探索者 A：发散思维，生成多样方案
  innovation_exploration_alt: "deepseek", // 探索者 B：独立视角，避免同质化
  
  // Step 3 Phase B: 对抗性生成
  disruptive_innovation: "qwen",       // 颠覆者：高 temperature 下创意丰富
  boundary_enforcement: "llama",       // 守护者：严谨，识别边界清晰
  cross_domain_research: "deepseek",   // 考古学家：推理链强，擅长跨域分析
  synthesis_innovation: "llama",       // 炼金师：整合能力强，输出平衡
  
  // === 产品概念阶段 ===
  competitive_analysis: "qwen",        // 竞品分析：中文市场理解
  market_research: "deepseek",         // 市场研究：数据推理
  user_persona_validation: "qwen",     // 用户画像：共情理解
  
  // === 产品地图阶段 ===
  task_completeness_review: "llama",   // 任务完整性审查：逻辑严密
  conflict_detection: "qwen",          // 冲突检测：语义理解
  constraint_analysis: "deepseek",     // 约束分析：技术推理
  
  // === 界面地图阶段 ===
  ux_review: "qwen",                   // UX 审查：用户体验理解
  accessibility_check: "llama",        // 无障碍检查：规范遵循
  
  // === 用例阶段 ===
  edge_case_generation: "deepseek",    // 边界用例：推理边缘情况
  acceptance_criteria_review: "qwen",  // 验收标准：需求理解
  
  // === 功能查漏阶段 ===
  journey_validation: "llama",         // 旅程验证：流程逻辑
  gap_prioritization: "qwen",          // 缺口优先级：业务理解
  
  // === 功能剪枝阶段 ===
  pruning_second_opinion: "deepseek",  // 剪枝二意见：客观分析
  competitive_benchmark: "qwen",       // 竞品对比：中文竞品理解
  
  // === UI 设计阶段 ===
  design_review: "qwen",               // 设计审查：审美理解
  visual_consistency: "llama",         // 视觉一致性：细节观察
  
  // === 创新验证专用（新增） ===
  innovation_review: "qwen",           // 创新特性审查：screen-map 阶段验证
  innovation_design_review: "llama",   // 创新设计审查：ui-design 阶段验证
  innovation_priority_review: "qwen",  // 创新优先级审查：task-execute 阶段验证
  innovation_use_case_review: "qwen",  // 创新用例审查：use-case 阶段验证
  innovation_gap_review: "llama",      // 创新缺口审查：feature-gap 阶段验证
  
  // === 代码复刻阶段 ===
  behavior_completeness_review: "qwen",     // 行为完整性：生态广度好，识别框架隐式行为
  cross_stack_risk_review: "deepseek",      // 跨栈风险：推理链强，语义漂移深度分析
  mapping_decision_review: "deepseek",       // 映射决策审查：推理链强，擅长方案优劣的逻辑判断

  // === 设计审计阶段 ===
  cross_layer_validation: "deepseek",  // 跨层验证：深度推理
  coverage_analysis: "llama",          // 覆盖分析：系统性检查
  
  // === 通用 ===
  general: "qwen",                     // 通用：中文理解最佳
  chinese_analysis: "qwen",            // 中文分析：母语优势
};
