import { z } from "zod";
import { textToSpeech } from "../google-ai/client.js";
import { writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname } from "node:path";
export const textToSpeechSchema = {
    text: z.string().describe("Text to convert to speech"),
    language: z
        .string()
        .optional()
        .describe("Language code (e.g. en-US, zh-CN, ja-JP). Default: en-US"),
    voice: z
        .string()
        .optional()
        .describe("Voice name (e.g. en-US-Neural2-F). Uses default if not set"),
    speaking_rate: z
        .number()
        .min(0.25)
        .max(4.0)
        .optional()
        .describe("Speaking rate (0.25-4.0, default: 1.0)"),
    format: z
        .enum(["MP3", "OGG_OPUS", "LINEAR16"])
        .optional()
        .describe("Audio format (default: MP3)"),
    save_path: z
        .string()
        .optional()
        .describe("Optional file path to save the audio (e.g. ./assets/narration.mp3)"),
};
export function registerTextToSpeech(server) {
    server.tool("text_to_speech", "Convert text to speech using Google Cloud TTS. Returns base64 audio; optionally saves to file.", textToSpeechSchema, async (params) => {
        try {
            const result = await textToSpeech(params.text, {
                languageCode: params.language,
                voiceName: params.voice,
                speakingRate: params.speaking_rate,
                audioEncoding: params.format,
            });
            let savedPath;
            if (params.save_path) {
                const dir = dirname(params.save_path);
                if (!existsSync(dir))
                    await mkdir(dir, { recursive: true });
                await writeFile(params.save_path, Buffer.from(result.base64, "base64"));
                savedPath = params.save_path;
            }
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            mime_type: result.mimeType,
                            saved_to: savedPath,
                            base64_length: result.base64.length,
                        }, null, 2),
                    },
                ],
            };
        }
        catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            return {
                content: [{ type: "text", text: JSON.stringify({ error: message }, null, 2) }],
                isError: true,
            };
        }
    });
}
