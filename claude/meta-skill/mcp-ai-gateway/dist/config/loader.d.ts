export declare function loadRouting(): Promise<Record<string, string>>;
export declare function getRegion(): Promise<"china" | "global" | "unknown">;
export declare function getModelIdForTask(task: string, familyOverride?: string): Promise<string>;
export declare function resolveFamily(routing: Record<string, string>, task: string, familyOverride?: string): string;
export { detectRegion, getCachedRegion, getModelForTask, getModelFamilyMap, getTaskFamilyMap } from "./region-detector.js";
