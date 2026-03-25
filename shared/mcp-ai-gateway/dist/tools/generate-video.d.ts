import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const generateVideoSchema: {
    prompt: z.ZodString;
    duration_seconds: z.ZodOptional<z.ZodNumber>;
    aspect_ratio: z.ZodOptional<z.ZodEnum<["16:9", "9:16"]>>;
    resolution: z.ZodOptional<z.ZodEnum<["720p", "1080p", "4k"]>>;
    save_path: z.ZodOptional<z.ZodString>;
};
export declare function registerGenerateVideo(server: McpServer): void;
