import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const openrouterImageSchema: {
    prompt: z.ZodString;
    model: z.ZodOptional<z.ZodEnum<["openai/gpt-5-image", "openai/gpt-5-image-mini", "google/gemini-2.5-flash-image", "google/gemini-3.1-flash-image-preview", "google/gemini-3-pro-image-preview"]>>;
    save_path: z.ZodOptional<z.ZodString>;
};
export declare function registerOpenRouterImage(server: McpServer): void;
