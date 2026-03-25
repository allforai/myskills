import { fetchModels, chatCompletion } from "./client.js";
import { getCache, setCache } from "./cache.js";
import modelFamiliesData from "../data/model-families.json" with { type: "json" };
const families = modelFamiliesData.families;
const GLOBAL_EXCLUDED_SUFFIXES = [":free", ":extended", ":exacto"];
const CACHE_TTL = 24 * 60 * 60 * 1000;
const JUDGE_MODEL_ID = "qwen/qwen3-coder-plus";
async function getAllModels() {
    const cached = await getCache();
    if (cached)
        return cached;
    const models = await fetchModels();
    await setCache(models);
    return models;
}
async function resolveLatestModelWithLLM(familyId, candidates) {
    if (candidates.length === 0)
        return null;
    if (candidates.length === 1)
        return candidates[0].id;
    const family = families[familyId];
    const modelList = candidates.map(m => `- ${m.id} (created: ${m.created ? new Date(m.created * 1000).toISOString() : 'unknown'})`).join('\n');
    const prompt = `You are an AI model expert. Given the following models from the ${family.display_name} family, identify the LATEST and MOST CAPABLE model for general use. Consider: 1) Model version numbers (higher = newer), 2) Release dates, 3) Model capabilities. Respond with ONLY the model ID.`;
    try {
        const result = await chatCompletion(JUDGE_MODEL_ID, [{ role: 'user', content: prompt }], 0);
        const selectedModel = result.content.trim();
        if (candidates.some(m => m.id === selectedModel)) {
            console.error(`  🤖 LLM 选择：${selectedModel}`);
            return selectedModel;
        }
        console.error(`  ⚠️ LLM 返回无效，回退到时间排序`);
        return candidates.sort((a, b) => (b.created ?? 0) - (a.created ?? 0))[0]?.id ?? null;
    }
    catch (e) {
        console.error(`  ⚠️ LLM 判断失败：${e}, 回退到时间排序`);
        return candidates.sort((a, b) => (b.created ?? 0) - (a.created ?? 0))[0]?.id ?? null;
    }
}
async function readLLMCache(familyId) {
    try {
        const fs = await import("fs");
        const path = await import("path");
        const cacheFile = path.join(".allforai", "llm-model-cache.json");
        if (!fs.existsSync(cacheFile))
            return null;
        const data = JSON.parse(fs.readFileSync(cacheFile, "utf-8"));
        const cache = data[familyId];
        if (!cache || Date.now() > cache.expiresAt)
            return null;
        console.error(`  📦 使用 LLM 缓存 (${new Date(cache.expiresAt - CACHE_TTL).toLocaleDateString()})`);
        return cache.modelId;
    }
    catch {
        return null;
    }
}
async function writeLLMCache(familyId, modelId) {
    try {
        const fs = await import("fs");
        const path = await import("path");
        const cacheFile = path.join(".allforai", "llm-model-cache.json");
        const dir = path.dirname(cacheFile);
        if (!fs.existsSync(dir))
            fs.mkdirSync(dir, { recursive: true });
        const data = {
            [familyId]: { familyId, modelId, expiresAt: Date.now() + CACHE_TTL }
        };
        if (fs.existsSync(cacheFile)) {
            const existing = JSON.parse(fs.readFileSync(cacheFile, "utf-8"));
            Object.assign(data, existing);
        }
        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
    }
    catch (e) {
        console.warn(`  ⚠️ 无法写入 LLM 缓存：${e}`);
    }
}
export async function resolveLatestModel(familyId) {
    const family = families[familyId];
    if (!family)
        return null;
    const cached = await readLLMCache(familyId);
    if (cached)
        return cached;
    const models = await getAllModels();
    const candidates = models.filter((m) => {
        const matchesPrefix = family.id_prefixes.some((p) => m.id.startsWith(p));
        if (!matchesPrefix)
            return false;
        if (family.exclude_prefixes?.some((p) => m.id.startsWith(p)))
            return false;
        const allExcludedSuffixes = [...GLOBAL_EXCLUDED_SUFFIXES, ...(family.exclude_suffixes || [])];
        if (allExcludedSuffixes.some((s) => m.id.endsWith(s)))
            return false;
        return true;
    });
    if (candidates.length === 0)
        return null;
    console.error(`  📋 候选模型 (${candidates.length}个):`);
    candidates.slice(0, 5).forEach(m => console.error(`    - ${m.id}`));
    if (candidates.length > 5)
        console.error(`    ... 还有 ${candidates.length - 5} 个`);
    const latestModel = await resolveLatestModelWithLLM(familyId, candidates);
    if (latestModel)
        await writeLLMCache(familyId, latestModel);
    return latestModel;
}
export async function resolveAllFamilies() {
    const result = {};
    for (const [familyId, family] of Object.entries(families)) {
        const modelId = await resolveLatestModel(familyId);
        result[familyId] = { model_id: modelId, display_name: family.display_name };
    }
    return result;
}
export function getFamilies() {
    return { families };
}
