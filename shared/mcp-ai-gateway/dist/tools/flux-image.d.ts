import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const fluxImageSchema: {
    prompt: z.ZodString;
    model: z.ZodOptional<z.ZodEnum<["fal-ai/flux-2-pro", "fal-ai/flux-2-dev", "fal-ai/flux-2-schnell"]>>;
    image_size: z.ZodOptional<z.ZodEnum<["square", "landscape_4_3", "portrait_4_3", "landscape_16_9", "portrait_16_9"]>>;
    count: z.ZodOptional<z.ZodNumber>;
    save_path: z.ZodOptional<z.ZodString>;
};
export declare function registerFluxImage(server: McpServer): void;
