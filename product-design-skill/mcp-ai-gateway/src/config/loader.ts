import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { parse as parseYaml } from "yaml";
import { getCachedRegion, detectRegion, getModelForTask, getModelFamilyMap } from "./region-detector.js";

const CONFIG_PATH = ".allforai/openrouter-config.yaml";

interface UserConfig {
  routing?: Record<string, string>;
  region?: "auto" | "china" | "global";
}

let cachedRegion: "china" | "global" | "unknown" | null = null;
let cachedFamilyMap: Record<string, string> | null = null;

export async function loadRouting(): Promise<Record<string, string>> {
  // 这个函数保留向后兼容，返回家族映射
  const region = await getRegion();
  return getModelFamilyMap(region);
}

export async function getRegion(): Promise<"china" | "global" | "unknown"> {
  if (cachedRegion) {
    return cachedRegion;
  }

  const userConfig = await loadUserConfig();
  
  // 用户指定区域
  if (userConfig.region && userConfig.region !== "auto") {
    cachedRegion = userConfig.region as "china" | "global";
    return cachedRegion;
  }

  // 自动检测
  const cached = await getCachedRegion();
  if (cached) {
    cachedRegion = cached;
  } else {
    cachedRegion = await detectRegion();
  }

  return cachedRegion;
}

// 根据任务类型获取模型 ID（新函数）
export async function getModelIdForTask(task: string, familyOverride?: string): Promise<string> {
  const region = await getRegion();
  
  // 用户指定家族优先
  if (familyOverride) {
    const familyMap = getModelFamilyMap(region);
    return familyMap[familyOverride] || familyMap.qwen;
  }
  
  // 否则根据任务特性选择
  return getModelForTask(task, region);
}

export function resolveFamily(
  routing: Record<string, string>,
  task: string,
  familyOverride?: string,
): string {
  if (familyOverride) return familyOverride;
  return routing[task] ?? routing["general"] ?? "qwen";
}

async function loadUserConfig(): Promise<UserConfig> {
  if (!existsSync(CONFIG_PATH)) return {};
  try {
    const raw = await readFile(CONFIG_PATH, "utf-8");
    const parsed = parseYaml(raw) as UserConfig | null;
    return parsed ?? {};
  } catch {
    return {};
  }
}

// 导出供外部使用
export { detectRegion, getCachedRegion, getModelForTask, getModelFamilyMap, getTaskFamilyMap } from "./region-detector.js";
