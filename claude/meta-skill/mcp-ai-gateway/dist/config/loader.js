import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { parse as parseYaml } from "yaml";
import { getCachedRegion, detectRegion, getModelForTask, getModelFamilyMap } from "./region-detector.js";
const CONFIG_PATH = ".allforai/openrouter-config.yaml";
let cachedRegion = null;
export async function loadRouting() {
    // 这个函数保留向后兼容，返回家族映射
    const region = await getRegion();
    return await getModelFamilyMap(region);
}
export async function getRegion() {
    if (cachedRegion) {
        return cachedRegion;
    }
    const userConfig = await loadUserConfig();
    // 用户指定区域
    if (userConfig.region && userConfig.region !== "auto") {
        cachedRegion = userConfig.region;
        return cachedRegion;
    }
    // 自动检测
    const cached = await getCachedRegion();
    if (cached) {
        cachedRegion = cached;
    }
    else {
        cachedRegion = await detectRegion();
    }
    return cachedRegion;
}
// 根据任务类型获取模型 ID（新函数）
export async function getModelIdForTask(task, familyOverride) {
    const region = await getRegion();
    // 用户指定家族优先
    if (familyOverride) {
        const familyMap = await getModelFamilyMap(region);
        return familyMap[familyOverride] || familyMap.qwen;
    }
    // 否则根据任务特性选择
    return await getModelForTask(task, region);
}
export function resolveFamily(routing, task, familyOverride) {
    if (familyOverride)
        return familyOverride;
    return routing[task] ?? routing["general"] ?? "qwen";
}
async function loadUserConfig() {
    if (!existsSync(CONFIG_PATH))
        return {};
    try {
        const raw = await readFile(CONFIG_PATH, "utf-8");
        const parsed = parseYaml(raw);
        return parsed ?? {};
    }
    catch {
        return {};
    }
}
// 导出供外部使用
export { detectRegion, getCachedRegion, getModelForTask, getModelFamilyMap, getTaskFamilyMap } from "./region-detector.js";
