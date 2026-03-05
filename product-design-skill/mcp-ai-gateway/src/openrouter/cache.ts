import { readFile, writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname } from "node:path";

const CACHE_PATH = "/tmp/myskills-openrouter-models-cache.json";
const TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

interface CacheEntry {
  timestamp: number;
  data: unknown;
}

export async function getCache<T>(): Promise<T | null> {
  try {
    if (!existsSync(CACHE_PATH)) return null;
    const raw = await readFile(CACHE_PATH, "utf-8");
    const entry: CacheEntry = JSON.parse(raw);
    if (Date.now() - entry.timestamp > TTL_MS) return null;
    return entry.data as T;
  } catch {
    return null;
  }
}

export async function setCache(data: unknown): Promise<void> {
  const entry: CacheEntry = { timestamp: Date.now(), data };
  const dir = dirname(CACHE_PATH);
  if (!existsSync(dir)) await mkdir(dir, { recursive: true });
  await writeFile(CACHE_PATH, JSON.stringify(entry), "utf-8");
}
