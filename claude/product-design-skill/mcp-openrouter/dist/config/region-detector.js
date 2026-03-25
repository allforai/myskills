import { chatCompletion } from "../openrouter/client.js";
const CACHE_FILE = ".allforai/mcp-region-cache.json";
// 测试模型列表 - 用于区域检测
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
// 模型家族 → 实际模型 ID 映射（根据区域动态选择）
const MODEL_FAMILY_MAP = {
    global: {
        gpt: "openai/gpt-4o",
        gemini: "google/gemini-2.0-flash",
        claude: "anthropic/claude-3.5-sonnet",
        deepseek: "deepseek/deepseek-chat-v3",
        qwen: "qwen/qwen-2.5-72b-instruct",
        llama: "meta-llama/llama-3.3-70b-instruct",
    },
    china: {
        gpt: "qwen/qwen-2.5-72b-instruct", // GPT 不可用 → 用 Qwen 替代（中文理解好）
        gemini: "deepseek/deepseek-chat-v3", // Gemini 不可用 → 用 DeepSeek 替代（推理强）
        claude: "meta-llama/llama-3.3-70b-instruct", // Claude 不可用 → 用 Llama 替代（严谨）
        deepseek: "deepseek/deepseek-chat-v3",
        qwen: "qwen/qwen-2.5-72b-instruct",
        llama: "meta-llama/llama-3.3-70b-instruct",
    },
    unknown: {
        // 保守策略：全部使用中国区可用模型
        gpt: "qwen/qwen-2.5-72b-instruct",
        gemini: "deepseek/deepseek-chat-v3",
        claude: "meta-llama/llama-3.3-70b-instruct",
        deepseek: "deepseek/deepseek-chat-v3",
        qwen: "qwen/qwen-2.5-72b-instruct",
        llama: "meta-llama/llama-3.3-70b-instruct",
    },
};
// 任务类型 → 模型家族映射（固定，不随区域变化）
// 每个任务选择最擅长的模型家族
const TASK_FAMILY_MAP = {
    // 创新流程
    assumption_challenge: "qwen", // 中文理解好，准确识别共识
    constraint_classification: "llama", // 逻辑分类强
    innovation_exploration: "qwen", // 发散思维
    innovation_exploration_alt: "deepseek", // 独立视角
    disruptive_innovation: "qwen", // 创意丰富
    boundary_enforcement: "llama", // 严谨，边界清晰
    cross_domain_research: "deepseek", // 推理链强，跨域分析
    synthesis_innovation: "llama", // 整合能力强
    // 产品概念
    competitive_analysis: "qwen", // 中文市场理解
    market_research: "deepseek", // 数据推理
    user_persona_validation: "qwen", // 共情理解
    // 产品地图
    task_completeness_review: "llama", // 逻辑严密
    conflict_detection: "qwen", // 语义理解
    constraint_analysis: "deepseek", // 技术推理
    // 界面地图
    ux_review: "qwen", // 用户体验理解
    accessibility_check: "llama", // 规范遵循
    // 用例
    edge_case_generation: "deepseek", // 推理边缘情况
    acceptance_criteria_review: "qwen", // 需求理解
    // 功能查漏
    journey_validation: "llama", // 流程逻辑
    gap_prioritization: "qwen", // 业务理解
    // 功能剪枝
    pruning_second_opinion: "deepseek", // 客观分析
    competitive_benchmark: "qwen", // 中文竞品理解
    // UI 设计
    design_review: "qwen", // 审美理解
    visual_consistency: "llama", // 细节观察
    // 设计审计
    cross_layer_validation: "deepseek", // 深度推理
    coverage_analysis: "llama", // 系统性检查
    // 通用
    general: "qwen",
    chinese_analysis: "qwen",
};
async function testModel(modelId) {
    try {
        await chatCompletion(modelId, [{ role: "user", content: "Hi" }], 0.5);
        return true;
    }
    catch {
        return false;
    }
}
export async function detectRegion() {
    console.log("🔍 检测可用区域...");
    // 测试全球模型
    let globalAvailable = 0;
    for (const model of TEST_MODELS.global) {
        const available = await testModel(model);
        if (available)
            globalAvailable++;
        console.log(`  ${model}: ${available ? "✅" : "❌"}`);
    }
    // 测试中国区模型
    let chinaAvailable = 0;
    for (const model of TEST_MODELS.china) {
        const available = await testModel(model);
        if (available)
            chinaAvailable++;
        console.log(`  ${model}: ${available ? "✅" : "❌"}`);
    }
    // 判定区域
    let region;
    if (globalAvailable >= 2) {
        region = "global";
        console.log(`✅ 判定为国际区 (${globalAvailable}/${TEST_MODELS.global.length} 模型可用)`);
    }
    else if (chinaAvailable >= 2) {
        region = "china";
        console.log(`✅ 判定为中国区 (${chinaAvailable}/${TEST_MODELS.china.length} 模型可用)`);
    }
    else {
        region = "unknown";
        console.log(`⚠️ 无法判定区域，使用保守路由`);
    }
    // 缓存结果
    const cache = {
        region,
        availableModels: MODEL_FAMILY_MAP[region],
        testedAt: Date.now(),
    };
    await writeCache(cache);
    return region;
}
// 根据任务类型获取模型 ID（核心函数）
export function getModelForTask(task, region) {
    const family = TASK_FAMILY_MAP[task] || TASK_FAMILY_MAP.general;
    return MODEL_FAMILY_MAP[region][family] || MODEL_FAMILY_MAP[region].qwen;
}
// 获取区域特定的模型家族映射
export function getModelFamilyMap(region) {
    return MODEL_FAMILY_MAP[region];
}
// 获取任务家族映射（固定）
export function getTaskFamilyMap() {
    return TASK_FAMILY_MAP;
}
async function readCache() {
    try {
        const fs = await import("fs");
        if (!fs.existsSync(CACHE_FILE))
            return null;
        const data = fs.readFileSync(CACHE_FILE, "utf-8");
        const cache = JSON.parse(data);
        // 缓存有效期 24 小时
        if (!cache || Date.now() - cache.testedAt > 24 * 60 * 60 * 1000) {
            return null;
        }
        return cache;
    }
    catch {
        return null;
    }
}
async function writeCache(cache) {
    try {
        const fs = await import("fs");
        const path = await import("path");
        const dir = path.dirname(CACHE_FILE);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
    }
    catch (e) {
        console.warn("⚠️ 无法写入区域缓存:", e);
    }
}
export async function getCachedRegion() {
    const cache = await readCache();
    if (cache) {
        console.log(`📦 使用缓存的区域：${cache.region} (测试于 ${new Date(cache.testedAt).toLocaleString()})`);
        return cache.region;
    }
    return null;
}
