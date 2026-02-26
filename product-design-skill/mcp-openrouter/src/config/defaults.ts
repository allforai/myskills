export const defaultRouting: Record<string, string> = {
  // 产品概念阶段
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
