import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
export declare const textToSpeechSchema: {
    text: z.ZodString;
    language: z.ZodOptional<z.ZodString>;
    voice: z.ZodOptional<z.ZodString>;
    speaking_rate: z.ZodOptional<z.ZodNumber>;
    format: z.ZodOptional<z.ZodEnum<["MP3", "OGG_OPUS", "LINEAR16"]>>;
    save_path: z.ZodOptional<z.ZodString>;
};
export declare function registerTextToSpeech(server: McpServer): void;
