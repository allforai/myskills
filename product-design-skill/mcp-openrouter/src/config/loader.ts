import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { parse as parseYaml } from "yaml";
import { defaultRouting } from "./defaults.js";

const CONFIG_PATH = ".allforai/openrouter-config.yaml";

interface UserConfig {
  routing?: Record<string, string>;
}

export async function loadRouting(): Promise<Record<string, string>> {
  const userConfig = await loadUserConfig();
  return { ...defaultRouting, ...userConfig.routing };
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
  return routing[task] ?? routing["general"] ?? "gpt";
}
