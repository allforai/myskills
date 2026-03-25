export type Region = "china" | "global" | "unknown";
export declare function detectRegion(): Promise<Region>;
export declare function getModelForTask(task: string, region: Region): string;
export declare function getModelFamilyMap(region: Region): Record<string, string>;
export declare function getTaskFamilyMap(): Record<string, string>;
export declare function getCachedRegion(): Promise<Region | null>;
