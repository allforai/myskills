export const defaultRouting: Record<string, string> = {
  // === 创新流程专用（7 个新增 task_type）===
  // Step 0 Phase C: 假设清零
  // 中国区可用模型：qwen/deepseek 替代 gpt/gemini
  assumption_challenge: "qwen",        // 挑战者：质疑行业共识
  constraint_classification: "deepseek", // 守护者：区分物理/人为
  
  // Step 0 Phase B+: 创新机会
  innovation_exploration: "qwen",      // 探索者 A
  innovation_exploration_alt: "deepseek", // 探索者 B（独立）
  
  // Step 3 Phase B: 对抗性生成
  disruptive_innovation: "qwen",       // 颠覆者：激进方案
  boundary_enforcement: "deepseek",     // 守护者：边界约束
  cross_domain_research: "deepseek",  // 考古学家：跨域案例
  synthesis_innovation: "llama",       // 炼金师：预整合
  
  // === 产品概念阶段（原有）===
  competitive_analysis: "qwen",
  market_research: "deepseek",
  user_persona_validation: "qwen",
  // 产品地图阶段
  task_completeness_review: "deepseek",
  conflict_detection: "qwen",
  constraint_analysis: "deepseek",
  // 界面地图阶段
  ux_review: "qwen",
  accessibility_check: "deepseek",
  // 用例阶段
  edge_case_generation: "deepseek",
  acceptance_criteria_review: "qwen",
  // 功能查漏阶段
  journey_validation: "deepseek",
  gap_prioritization: "qwen",
  // 功能剪枝阶段
  pruning_second_opinion: "deepseek",
  competitive_benchmark: "deepseek",
  // UI 设计阶段
  design_review: "qwen",
  visual_consistency: "deepseek",
  // 设计审计阶段
  cross_layer_validation: "qwen",
  coverage_analysis: "deepseek",
  // 通用
  general: "qwen",
  chinese_analysis: "qwen",
};
