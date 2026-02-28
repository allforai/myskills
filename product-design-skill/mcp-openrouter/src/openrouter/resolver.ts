import { fetchModels, type OpenRouterModel, chatCompletion } from "./client.js";
import { getCache, setCache } from "./cache.js";
import modelFamiliesData from "../data/model-families.json" with { type: "json" };

type FamilyId = string;

interface FamilyDef {
  provider: string;
  id_prefixes: string[];
  display_name: string;
  strengths: string[];
  best_for: string[];
  exclude_prefixes?: string[];
  exclude_suffixes?: string[];
}

interface FamiliesData {
  families: Record<FamilyId, FamilyDef>;
}

const families = (modelFamiliesData as FamiliesData).families;

// Global suffixes to exclude
const GLOBAL_EXCLUDED_SUFFIXES = [":free", ":extended", ":exacto"];

// Cache duration: 24 hours (一天一更新)
const CACHE_TTL = 24 * 60 * 60 * 1000;

// 用于判断的模型 ID（使用稳定可用的模型）
const JUDGE_MODEL_ID = "qwen/qwen3-coder-plus";

async function getAllModels(): Promise<OpenRouterModel[]> {
  const cached = await getCache<OpenRouterModel[]>();
  if (cached) return cached;
  const models = await fetchModels();
  await setCache(models);
  return models;
}

// 使用 LLM 判断哪个模型是最新的
async function resolveLatestModelWithLLM(familyId: string, candidates: OpenRouterModel[]): Promise<string | null> {
  if (candidates.length === 0) return null;
  if (candidates.length === 1) return candidates[0].id;

  const family = families[familyId];
  
  // 构建提示词，让 LLM 判断哪个模型最新
  const modelList = candidates.map(m => `- ${m.id} (created: ${m.created ? new Date(m.created * 1000).toISOString() : 'unknown'})`).join('\n');
  
  const prompt = `You are an AI model expert. Given the following models from the ${family.display_name} family, identify the LATEST and MOST CAPABLE model for general use.

Consider:
1. Model version numbers (higher = newer)
2. Release dates (created timestamp)
3. Model capabilities (prefer full models over specialized variants)

Models:
${modelList}

Respond with ONLY the model ID of the latest and most capable model, nothing else.`;

  try {
    const result = await chatCompletion(JUDGE_MODEL_ID, [
      { role: 'user', content: prompt }
    ], 0);
    
    const selectedModel = result.content.trim();
    
    // 验证返回的模型 ID 是否在候选列表中
    if (candidates.some(m => m.id === selectedModel)) {
      console.log(`  🤖 LLM 选择：${selectedModel}`);
      return selectedModel;
    }
    
    // 如果 LLM 返回无效，回退到按时间排序
    console.log(`  ⚠️ LLM 返回无效 (${selectedModel})，回退到时间排序`);
    return candidates.sort((a, b) => (b.created ?? 0) - (a.created ?? 0))[0]?.id ?? null;
  } catch (e) {
    console.log(`  ⚠️ LLM 判断失败：${e}, 回退到时间排序`);
    return candidates.sort((a, b) => (b.created ?? 0) - (a.created ?? 0))[0]?.id ?? null;
  }
}

// 检查 LLM 缓存是否过期（一天一更新）
interface LLMCache {
  familyId: string;
  modelId: string;
  expiresAt: number;
}

async function readLLMCache(familyId: string): Promise<string | null> {
  try {
    const fs = await import("fs");
    const path = await import("path");
    const cacheFile = path.join(".allforai", "llm-model-cache.json");
    
    if (!fs.existsSync(cacheFile)) return null;
    
    const data = JSON.parse(fs.readFileSync(cacheFile, "utf-8")) as Record<string, LLMCache>;
    const cache = data[familyId];
    
    if (!cache || Date.now() > cache.expiresAt) {
      return null; // 缓存过期
    }
    
    console.log(`  📦 使用 LLM 缓存 (${new Date(cache.expiresAt - CACHE_TTL).toLocaleDateString()} 生成)`);
    return cache.modelId;
  } catch {
    return null;
  }
}

async function writeLLMCache(familyId: string, modelId: string): Promise<void> {
  try {
    const fs = await import("fs");
    const path = await import("path");
    const cacheFile = path.join(".allforai", "llm-model-cache.json");
    const dir = path.dirname(cacheFile);
    
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    const data: Record<string, LLMCache> = {
      [familyId]: {
        familyId,
        modelId,
        expiresAt: Date.now() + CACHE_TTL, // 24 小时后过期
      }
    };
    
    // 合并现有缓存
    if (fs.existsSync(cacheFile)) {
      const existing = JSON.parse(fs.readFileSync(cacheFile, "utf-8"));
      Object.assign(data, existing);
    }
    
    fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2));
  } catch (e) {
    console.warn(`  ⚠️ 无法写入 LLM 缓存：${e}`);
  }
}

export async function resolveLatestModel(familyId: string): Promise<string | null> {
  const family = families[familyId];
  if (!family) return null;

  // 检查 LLM 缓存（一天一更新）
  const cached = await readLLMCache(familyId);
  if (cached) {
    return cached;
  }

  const models = await getAllModels();
  const candidates = models
    .filter((m) => {
      // Must match at least one include prefix
      const matchesPrefix = family.id_prefixes.some((p) => m.id.startsWith(p));
      if (!matchesPrefix) return false;
      
      // Exclude family-specific prefixes
      if (family.exclude_prefixes?.some((p) => m.id.startsWith(p))) return false;
      
      // Exclude global and family-specific suffixes
      const allExcludedSuffixes = [...GLOBAL_EXCLUDED_SUFFIXES, ...(family.exclude_suffixes || [])];
      if (allExcludedSuffixes.some((s) => m.id.endsWith(s))) return false;
      
      return true;
    });

  if (candidates.length === 0) return null;

  console.log(`  📋 候选模型 (${candidates.length}个):`);
  candidates.slice(0, 5).forEach(m => {
    console.log(`    - ${m.id}`);
  });
  if (candidates.length > 5) {
    console.log(`    ... 还有 ${candidates.length - 5} 个`);
  }

  // 使用 LLM 判断最新模型
  const latestModel = await resolveLatestModelWithLLM(familyId, candidates);
  
  if (latestModel) {
    // 写入 LLM 缓存（24 小时有效）
    await writeLLMCache(familyId, latestModel);
  }
  
  return latestModel;
}

export async function resolveAllFamilies(): Promise<
  Record<string, { model_id: string | null; display_name: string }>
> {
  const result: Record<string, { model_id: string | null; display_name: string }> = {};

  for (const [familyId, family] of Object.entries(families)) {
    const modelId = await resolveLatestModel(familyId);
    result[familyId] = {
      model_id: modelId,
      display_name: family.display_name,
    };
  }

  return result;
}

export function getFamilies(): FamiliesData {
  return { families };
}
