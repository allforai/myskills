import { chatCompletion } from "../openrouter/client.js";

export type Region = "china" | "global" | "unknown";

interface ModelAvailability {
  region: Region;
  availableModels: Record<string, string>;
  testedAt: number;
}

const CACHE_FILE = ".allforai/mcp-region-cache.json";

// 测试模型列表（按区域可用性）
const TEST_MODELS = {
  global: [
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-lite",
    "anthropic/claude-3.5-sonnet",
  ],
  china: [
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat-v3",
    "meta-llama/llama-3.3-70b-instruct",
  ],
};

// 区域特定路由映射 - 移到这里避免循环引用
function getRegionRoutes(region: Region): Record<string, string> {
  if (region === "global") {
    return {
      // 创新流程
      assumption_challenge: "gpt",
      constraint_classification: "gemini",
      innovation_exploration: "gpt",
      innovation_exploration_alt: "gemini",
      disruptive_innovation: "gpt",
      boundary_enforcement: "gemini",
      cross_domain_research: "deepseek",
      synthesis_innovation: "claude",
      // 通用
      competitive_analysis: "gpt",
      market_research: "gemini",
      user_persona_validation: "gpt",
      task_completeness_review: "gemini",
      conflict_detection: "gpt",
      constraint_analysis: "deepseek",
      ux_review: "gpt",
      accessibility_check: "gemini",
      edge_case_generation: "deepseek",
      acceptance_criteria_review: "gpt",
      journey_validation: "gemini",
      gap_prioritization: "gpt",
      pruning_second_opinion: "deepseek",
      competitive_benchmark: "gemini",
      design_review: "gpt",
      visual_consistency: "gemini",
      cross_layer_validation: "gpt",
      coverage_analysis: "deepseek",
      general: "gpt",
      chinese_analysis: "qwen",
    };
  } else {
    // 中国区（包括 unknown）
    return {
      // 创新流程 - 全部使用中国区可用模型
      assumption_challenge: "qwen",
      constraint_classification: "deepseek",
      innovation_exploration: "qwen",
      innovation_exploration_alt: "deepseek",
      disruptive_innovation: "qwen",
      boundary_enforcement: "deepseek",
      cross_domain_research: "deepseek",
      synthesis_innovation: "llama",
      // 通用 - 替换不可用模型
      competitive_analysis: "qwen",
      market_research: "deepseek",
      user_persona_validation: "qwen",
      task_completeness_review: "deepseek",
      conflict_detection: "qwen",
      constraint_analysis: "deepseek",
      ux_review: "qwen",
      accessibility_check: "deepseek",
      edge_case_generation: "deepseek",
      acceptance_criteria_review: "qwen",
      journey_validation: "deepseek",
      gap_prioritization: "qwen",
      pruning_second_opinion: "deepseek",
      competitive_benchmark: "deepseek",
      design_review: "qwen",
      visual_consistency: "deepseek",
      cross_layer_validation: "qwen",
      coverage_analysis: "deepseek",
      general: "qwen",
      chinese_analysis: "qwen",
    };
  }
}

async function testModel(modelId: string): Promise<boolean> {
  try {
    await chatCompletion(modelId, [{ role: "user", content: "Hi" }], 0.5);
    return true;
  } catch {
    return false;
  }
}

export async function detectRegion(): Promise<Region> {
  console.log("🔍 检测可用区域...");

  // 测试全球模型
  let globalAvailable = 0;
  for (const model of TEST_MODELS.global) {
    const available = await testModel(model);
    if (available) globalAvailable++;
    console.log(`  ${model}: ${available ? "✅" : "❌"}`);
  }

  // 测试中国区模型
  let chinaAvailable = 0;
  for (const model of TEST_MODELS.china) {
    const available = await testModel(model);
    if (available) chinaAvailable++;
    console.log(`  ${model}: ${available ? "✅" : "❌"}`);
  }

  // 判定区域
  let region: Region;
  if (globalAvailable >= 2) {
    region = "global";
    console.log(`✅ 判定为国际区 (${globalAvailable}/${TEST_MODELS.global.length} 模型可用)`);
  } else if (chinaAvailable >= 2) {
    region = "china";
    console.log(`✅ 判定为中国区 (${chinaAvailable}/${TEST_MODELS.china.length} 模型可用)`);
  } else {
    region = "unknown";
    console.log(`⚠️ 无法判定区域，使用默认路由`);
  }

  // 缓存结果
  const cache: ModelAvailability = {
    region,
    availableModels: getAvailableModelsForRegion(region),
    testedAt: Date.now(),
  };

  await writeCache(cache);

  return region;
}

export function getAvailableModelsForRegion(region: Region): Record<string, string> {
  if (region === "global") {
    return {
      gpt: "openai/gpt-4o",
      gemini: "google/gemini-2.0-flash",
      claude: "anthropic/claude-3.5-sonnet",
      deepseek: "deepseek/deepseek-chat-v3",
      qwen: "qwen/qwen-2.5-72b-instruct",
      llama: "meta-llama/llama-3.3-70b-instruct",
    };
  } else {
    return {
      gpt: "qwen/qwen-2.5-72b-instruct", // 用 Qwen 替代
      gemini: "deepseek/deepseek-chat-v3", // 用 DeepSeek 替代
      claude: "llama/llama-3.3-70b-instruct", // 用 Llama 替代
      deepseek: "deepseek/deepseek-chat-v3",
      qwen: "qwen/qwen-2.5-72b-instruct",
      llama: "meta-llama/llama-3.3-70b-instruct",
    };
  }
}

async function readCache(): Promise<ModelAvailability | null> {
  try {
    const fs = await import("fs");
    if (!fs.existsSync(CACHE_FILE)) return null;
    const data = fs.readFileSync(CACHE_FILE, "utf-8");
    const cache = JSON.parse(data) as ModelAvailability | null;
    // 缓存有效期 24 小时
    if (!cache || Date.now() - cache.testedAt > 24 * 60 * 60 * 1000) {
      return null;
    }
    return cache;
  } catch {
    return null;
  }
}

async function writeCache(cache: ModelAvailability): Promise<void> {
  try {
    const fs = await import("fs");
    const path = await import("path");
    const dir = path.dirname(CACHE_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
  } catch (e) {
    console.warn("⚠️ 无法写入区域缓存:", e);
  }
}

export async function getCachedRegion(): Promise<Region | null> {
  const cache = await readCache();
  if (cache) {
    console.log(`📦 使用缓存的区域：${cache.region} (测试于 ${new Date(cache.testedAt).toLocaleString()})`);
    return cache.region;
  }
  return null;
}

// 重新导出给 loader 使用
export { getRegionRoutes };
