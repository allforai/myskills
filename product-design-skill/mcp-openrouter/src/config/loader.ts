import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { parse as parseYaml } from "yaml";
import { defaultRouting } from "./defaults.js";
import { getCachedRegion, detectRegion, getRegionRoutes } from "./region-detector.js";

const CONFIG_PATH = ".allforai/openrouter-config.yaml";

interface UserConfig {
  routing?: Record<string, string>;
  region?: "auto" | "china" | "global";
}

let cachedRouting: Record<string, string> | null = null;

export async function loadRouting(): Promise<Record<string, string>> {
  // 返回缓存
  if (cachedRouting) {
    return cachedRouting;
  }

  const userConfig = await loadUserConfig();
  
  // 检查用户是否指定区域
  if (userConfig.region && userConfig.region !== "auto") {
    const region = userConfig.region as "china" | "global";
    const regionRoutes = getRegionRoutes(region);
    cachedRouting = { ...regionRoutes, ...userConfig.routing };
    return cachedRouting;
  }

  // 自动检测区域
  const cachedRegion = await getCachedRegion();
  let region;
  
  if (cachedRegion) {
    region = cachedRegion;
  } else {
    region = await detectRegion();
  }

  // 加载区域特定路由
  const regionRoutes = getRegionRoutes(region);
  
  // 用户自定义路由优先
  cachedRouting = { ...regionRoutes, ...userConfig.routing };
  
  return cachedRouting;
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

export function resolveFamily(
  routing: Record<string, string>,
  task: string,
  familyOverride?: string,
): string {
  if (familyOverride) return familyOverride;
  return routing[task] ?? routing["general"] ?? "qwen";
}

// 导出区域检测函数供外部调用
export { detectRegion, getCachedRegion } from "./region-detector.js";
