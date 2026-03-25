import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const generateImageSchema: {
    prompt: z.ZodString;
    aspect_ratio: z.ZodOptional<z.ZodEnum<["1:1", "16:9", "9:16", "4:3", "3:4"]>>;
    count: z.ZodOptional<z.ZodNumber>;
    save_path: z.ZodOptional<z.ZodString>;
};
export declare function registerGenerateImage(server: McpServer): void;
