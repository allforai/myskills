import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const askModelSchema: {
    task: z.ZodString;
    prompt: z.ZodString;
    model_family: z.ZodOptional<z.ZodString>;
    system_prompt: z.ZodOptional<z.ZodString>;
    temperature: z.ZodOptional<z.ZodNumber>;
};
export declare function registerAskModel(server: McpServer): void;
