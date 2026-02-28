export const defaultRouting: Record<string, string> = {
  // === 创新流程专用（7 个新增 task_type）===
  // Step 0 Phase C: 假设清零
  assumption_challenge: "gpt",        // 挑战者：质疑行业共识
  constraint_classification: "gemini", // 守护者：区分物理/人为
  
  // Step 0 Phase B+: 创新机会
  innovation_exploration: "gpt",      // 探索者 A
  innovation_exploration_alt: "gemini", // 探索者 B（独立）
  
  // Step 3 Phase B: 对抗性生成
  disruptive_innovation: "gpt",       // 颠覆者：激进方案
  boundary_enforcement: "gemini",     // 守护者：边界约束
  cross_domain_research: "deepseek",  // 考古学家：跨域案例
  synthesis_innovation: "qwen",       // 炼金师：预整合
  
  // === 产品概念阶段（原有）===
  competitive_analysis: "gpt",
  market_research: "gemini",
  user_persona_validation: "gpt",
  // 产品地图阶段
  task_completeness_review: "gemini",
  conflict_detection: "gpt",
  constraint_analysis: "deepseek",
  // 界面地图阶段
  ux_review: "gpt",
  accessibility_check: "gemini",
  // 用例阶段
  edge_case_generation: "deepseek",
  acceptance_criteria_review: "gpt",
  // 功能查漏阶段
  journey_validation: "gemini",
  gap_prioritization: "gpt",
  // 功能剪枝阶段
  pruning_second_opinion: "deepseek",
  competitive_benchmark: "gemini",
  // UI 设计阶段
  design_review: "gpt",
  visual_consistency: "gemini",
  // 设计审计阶段
  cross_layer_validation: "gpt",
  coverage_analysis: "deepseek",
  // 通用
  general: "gpt",
  chinese_analysis: "qwen",
};
