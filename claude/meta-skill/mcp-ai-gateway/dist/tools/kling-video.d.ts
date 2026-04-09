import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const klingVideoSchema: {
    prompt: z.ZodString;
    duration: z.ZodOptional<z.ZodEnum<["5", "10"]>>;
    aspect_ratio: z.ZodOptional<z.ZodEnum<["16:9", "9:16", "1:1"]>>;
    save_path: z.ZodOptional<z.ZodString>;
};
export declare function registerKlingVideo(server: McpServer): void;
