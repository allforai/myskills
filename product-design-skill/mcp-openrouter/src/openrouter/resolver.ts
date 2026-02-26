import { fetchModels, type OpenRouterModel } from "./client.js";
import { getCache, setCache } from "./cache.js";
import modelFamiliesData from "../data/model-families.json" with { type: "json" };

type FamilyId = string;

interface FamilyDef {
  provider: string;
  id_prefixes: string[];
  display_name: string;
  strengths: string[];
  best_for: string[];
}

interface FamiliesData {
  families: Record<FamilyId, FamilyDef>;
}

const families = (modelFamiliesData as FamiliesData).families;

// Suffixes to exclude from latest-model resolution
const EXCLUDED_SUFFIXES = [":free", ":extended"];

async function getAllModels(): Promise<OpenRouterModel[]> {
  const cached = await getCache<OpenRouterModel[]>();
  if (cached) return cached;
  const models = await fetchModels();
  await setCache(models);
  return models;
}

export async function resolveLatestModel(familyId: string): Promise<string | null> {
  const family = families[familyId];
  if (!family) return null;

  const models = await getAllModels();
  const candidates = models
    .filter((m) => {
      const matchesPrefix = family.id_prefixes.some((p) => m.id.startsWith(p));
      if (!matchesPrefix) return false;
      return !EXCLUDED_SUFFIXES.some((s) => m.id.endsWith(s));
    })
    .sort((a, b) => (b.created ?? 0) - (a.created ?? 0));

  return candidates[0]?.id ?? null;
}

export async function resolveAllFamilies(): Promise<
  Record<string, { model_id: string | null; display_name: string }>
> {
  const models = await getAllModels();
  const result: Record<string, { model_id: string | null; display_name: string }> = {};

  for (const [familyId, family] of Object.entries(families)) {
    const candidates = models
      .filter((m) => {
        const matchesPrefix = family.id_prefixes.some((p) => m.id.startsWith(p));
        if (!matchesPrefix) return false;
        return !EXCLUDED_SUFFIXES.some((s) => m.id.endsWith(s));
      })
      .sort((a, b) => (b.created ?? 0) - (a.created ?? 0));

    result[familyId] = {
      model_id: candidates[0]?.id ?? null,
      display_name: family.display_name,
    };
  }

  return result;
}

export function getFamilies(): FamiliesData {
  return { families };
}
