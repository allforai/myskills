import { chatCompletion, fetchModels } from "../openrouter/client.js";
import type { OpenRouterModel } from "../openrouter/client.js";

export type Region = "china" | "global" | "unknown";

interface RegionCache {
  region: Region;
  availableModels: Record<string, string>;
  testedAt: number;
}

interface ModelCache {
  familyMap: Record<string, string>;  // family → best model ID
  fetchedAt: number;
}

const REGION_CACHE_FILE = ".allforai/mcp-region-cache.json";
const MODEL_CACHE_FILE = ".allforai/mcp-model-cache.json";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

// Family → OpenRouter provider prefix for filtering models
const FAMILY_PREFIX: Record<string, string> = {
  gpt: "openai/gpt-",
  gemini: "google/gemini-",
  claude: "anthropic/claude-",
  deepseek: "deepseek/deepseek-",
  qwen: "qwen/qwen",
  llama: "meta-llama/llama-",
};

// Cheap/fast test models per region (these are stable IDs unlikely to change)
const TEST_MODEL_FAMILIES = {
  global: ["gpt", "gemini", "claude"],
  china: ["qwen", "deepseek", "llama"],
};

// China region fallback mapping (which family to use when original is blocked)
const CHINA_FALLBACK: Record<string, string> = {
  gpt: "qwen",        // GPT blocked → Qwen (best Chinese understanding)
  gemini: "deepseek",  // Gemini blocked → DeepSeek (strong reasoning)
  claude: "llama",     // Claude blocked → Llama (rigorous)
  deepseek: "deepseek",
  qwen: "qwen",
  llama: "llama",
};

// Task → model family mapping (fixed, not region-dependent)
const TASK_FAMILY_MAP: Record<string, string> = {
  // Innovation
  assumption_challenge: "qwen",
  constraint_classification: "llama",
  innovation_exploration: "qwen",
  innovation_exploration_alt: "deepseek",
  disruptive_innovation: "qwen",
  boundary_enforcement: "llama",
  cross_domain_research: "deepseek",
  synthesis_innovation: "llama",
  // Product concept
  competitive_analysis: "qwen",
  market_research: "deepseek",
  user_persona_validation: "qwen",
  // Product map
  task_completeness_review: "llama",
  conflict_detection: "qwen",
  constraint_analysis: "deepseek",
  // Screen map
  ux_review: "qwen",
  accessibility_check: "llama",
  // Use cases
  edge_case_generation: "deepseek",
  acceptance_criteria_review: "qwen",
  // Feature gap
  journey_validation: "llama",
  gap_prioritization: "qwen",
  // Feature prune
  pruning_second_opinion: "deepseek",
  competitive_benchmark: "qwen",
  // UI design
  design_review: "qwen",
  visual_consistency: "llama",
  // Design audit
  cross_layer_validation: "deepseek",
  coverage_analysis: "llama",
  // General
  general: "qwen",
  chinese_analysis: "qwen",
};

// ---------- Dynamic model resolution (LLM-powered) ----------

function getCandidates(models: OpenRouterModel[], family: string): OpenRouterModel[] {
  const prefix = FAMILY_PREFIX[family];
  if (!prefix) return [];
  return models
    .filter((m) => m.id.startsWith(prefix) && !m.id.includes(":free") && !m.id.includes(":extended"))
    .sort((a, b) => b.created - a.created)
    .slice(0, 15); // top 15 newest to keep prompt small
}

async function selectBestModelsViaLLM(
  candidatesByFamily: Record<string, { id: string; ctx: number; date: string }[]>,
): Promise<Record<string, string>> {
  const prompt = `You are an AI model expert. For each model family below, select the single BEST flagship model for general-purpose chat/reasoning tasks.

Rules:
- Pick the most capable, latest FLAGSHIP model (not mini/lite/small/guard/safety/distill/vision-only variants)
- Prefer "pro" or largest parameter variant over "flash"/"lite"/"mini"
- Prefer stable releases over "preview"/"exp" when a stable version exists at similar capability
- If only preview versions exist, pick the best preview
- For deepseek, prefer reasoning models (r1) over chat models when available at similar recency

Return ONLY a JSON object mapping family name to the chosen model ID. No explanation.

${Object.entries(candidatesByFamily)
  .map(([fam, models]) => `### ${fam}\n${models.map((m) => `${m.id} (ctx=${m.ctx}, date=${m.date})`).join("\n")}`)
  .join("\n\n")}

Response format: {"gpt":"openai/...","gemini":"google/...","claude":"anthropic/...","deepseek":"deepseek/...","qwen":"qwen/...","llama":"meta-llama/..."}`;

  // Use a cheap, fast model for this meta-task
  const result = await chatCompletion(
    "openai/gpt-4.1-mini",
    [{ role: "user", content: prompt }],
    0,
  );

  // Parse JSON from response
  const text = result.content.trim();
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error("LLM did not return valid JSON: " + text);
  return JSON.parse(jsonMatch[0]) as Record<string, string>;
}

async function fetchBestModels(): Promise<Record<string, string>> {
  const models = await fetchModels();

  // Build candidate lists per family
  const candidatesByFamily: Record<string, { id: string; ctx: number; date: string }[]> = {};
  for (const family of Object.keys(FAMILY_PREFIX)) {
    const candidates = getCandidates(models, family);
    if (candidates.length > 0) {
      candidatesByFamily[family] = candidates.map((m) => ({
        id: m.id,
        ctx: m.context_length ?? 0,
        date: new Date(m.created * 1000).toISOString().slice(0, 10),
      }));
    }
  }

  // Ask LLM to pick the best model per family
  return selectBestModelsViaLLM(candidatesByFamily);
}

// ---------- Caching ----------

async function readJsonCache<T>(filePath: string): Promise<T | null> {
  try {
    const fs = await import("fs");
    if (!fs.existsSync(filePath)) return null;
    const data = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
}

async function writeJsonCache(filePath: string, data: unknown): Promise<void> {
  try {
    const fs = await import("fs");
    const path = await import("path");
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
  } catch (e) {
    console.warn("Failed to write cache:", e);
  }
}

// ---------- Model family map (dynamic, cached 24h) ----------

let cachedFamilyMap: Record<string, string> | null = null;

async function getLatestFamilyMap(): Promise<Record<string, string>> {
  // In-memory cache
  if (cachedFamilyMap) return cachedFamilyMap;

  // File cache
  const diskCache = await readJsonCache<ModelCache>(MODEL_CACHE_FILE);
  if (diskCache && Date.now() - diskCache.fetchedAt < CACHE_TTL_MS) {
    cachedFamilyMap = diskCache.familyMap;
    console.log(`Using cached model map (fetched ${new Date(diskCache.fetchedAt).toLocaleString()})`);
    return cachedFamilyMap;
  }

  // Fetch fresh from OpenRouter
  try {
    console.log("Fetching latest models from OpenRouter...");
    const familyMap = await fetchBestModels();
    cachedFamilyMap = familyMap;
    await writeJsonCache(MODEL_CACHE_FILE, { familyMap, fetchedAt: Date.now() });
    console.log("Model map updated:", Object.entries(familyMap).map(([k, v]) => `${k}=${v}`).join(", "));
    return familyMap;
  } catch (e) {
    console.warn("Failed to fetch models, using hardcoded fallback:", e);
    return FALLBACK_FAMILY_MAP;
  }
}

// Hardcoded fallback only used when API is completely unavailable
const FALLBACK_FAMILY_MAP: Record<string, string> = {
  gpt: "openai/gpt-4.1",
  gemini: "google/gemini-2.5-flash",
  claude: "anthropic/claude-sonnet-4",
  deepseek: "deepseek/deepseek-r1",
  qwen: "qwen/qwen3-max",
  llama: "meta-llama/llama-4-maverick",
};

// ---------- Region-aware model resolution ----------

function buildRegionMap(familyMap: Record<string, string>, region: Region): Record<string, string> {
  if (region === "global") return { ...familyMap };

  // China / unknown: remap blocked families
  const result: Record<string, string> = {};
  for (const family of Object.keys(FAMILY_PREFIX)) {
    const fallbackFamily = CHINA_FALLBACK[family] ?? family;
    result[family] = familyMap[fallbackFamily] ?? familyMap.qwen ?? FALLBACK_FAMILY_MAP.qwen;
  }
  return result;
}

// ---------- Region detection ----------

async function testModel(modelId: string): Promise<boolean> {
  try {
    await chatCompletion(modelId, [{ role: "user", content: "Hi" }], 0.5);
    return true;
  } catch {
    return false;
  }
}

export async function detectRegion(): Promise<Region> {
  console.log("Detecting region...");
  const familyMap = await getLatestFamilyMap();

  // Pick a cheap test model per family
  const testResults = { global: 0, china: 0 };

  for (const family of TEST_MODEL_FAMILIES.global) {
    const modelId = familyMap[family];
    if (!modelId) continue;
    const ok = await testModel(modelId);
    if (ok) testResults.global++;
    console.log(`  ${modelId}: ${ok ? "OK" : "BLOCKED"}`);
  }

  for (const family of TEST_MODEL_FAMILIES.china) {
    const modelId = familyMap[family];
    if (!modelId) continue;
    const ok = await testModel(modelId);
    if (ok) testResults.china++;
    console.log(`  ${modelId}: ${ok ? "OK" : "BLOCKED"}`);
  }

  let region: Region;
  if (testResults.global >= 2) {
    region = "global";
    console.log(`Region: global (${testResults.global}/${TEST_MODEL_FAMILIES.global.length} available)`);
  } else if (testResults.china >= 2) {
    region = "china";
    console.log(`Region: china (${testResults.china}/${TEST_MODEL_FAMILIES.china.length} available)`);
  } else {
    region = "unknown";
    console.log("Region: unknown, using conservative routing");
  }

  const regionCache: RegionCache = {
    region,
    availableModels: buildRegionMap(familyMap, region),
    testedAt: Date.now(),
  };
  await writeJsonCache(REGION_CACHE_FILE, regionCache);

  return region;
}

// ---------- Public API ----------

export async function getModelForTask(task: string, region: Region): Promise<string> {
  const familyMap = await getLatestFamilyMap();
  const regionMap = buildRegionMap(familyMap, region);
  const family = TASK_FAMILY_MAP[task] || TASK_FAMILY_MAP.general;
  return regionMap[family] || regionMap.qwen || FALLBACK_FAMILY_MAP.qwen;
}

export async function getModelFamilyMap(region: Region): Promise<Record<string, string>> {
  const familyMap = await getLatestFamilyMap();
  return buildRegionMap(familyMap, region);
}

export function getTaskFamilyMap(): Record<string, string> {
  return TASK_FAMILY_MAP;
}

export async function getCachedRegion(): Promise<Region | null> {
  const cache = await readJsonCache<RegionCache>(REGION_CACHE_FILE);
  if (cache && Date.now() - cache.testedAt < CACHE_TTL_MS) {
    console.log(`Using cached region: ${cache.region} (tested ${new Date(cache.testedAt).toLocaleString()})`);
    return cache.region;
  }
  return null;
}

export async function refreshModels(): Promise<Record<string, string>> {
  cachedFamilyMap = null; // clear in-memory cache
  // Delete disk cache to force refresh
  try {
    const fs = await import("fs");
    if (fs.existsSync(MODEL_CACHE_FILE)) fs.unlinkSync(MODEL_CACHE_FILE);
  } catch { /* ignore */ }
  return getLatestFamilyMap();
}
