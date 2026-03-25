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
export declare function resolveLatestModel(familyId: string): Promise<string | null>;
export declare function resolveAllFamilies(): Promise<Record<string, {
    model_id: string | null;
    display_name: string;
}>>;
export declare function getFamilies(): FamiliesData;
export {};
