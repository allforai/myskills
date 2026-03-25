export type Region = "china" | "global" | "unknown";
export declare function detectRegion(): Promise<Region>;
export declare function getModelForTask(task: string, region: Region): Promise<string>;
export declare function getModelFamilyMap(region: Region): Promise<Record<string, string>>;
export declare function getTaskFamilyMap(): Record<string, string>;
export declare function getCachedRegion(): Promise<Region | null>;
export declare function refreshModels(): Promise<Record<string, string>>;
