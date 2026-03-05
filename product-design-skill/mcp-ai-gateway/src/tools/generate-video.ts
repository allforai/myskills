import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { generateVideo } from "../google-ai/client.js";
import { writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname } from "node:path";

export const generateVideoSchema = {
  prompt: z.string().describe("Video generation prompt describing the desired video"),
  duration_seconds: z
    .number()
    .min(5)
    .max(10)
    .optional()
    .describe("Video duration in seconds (5-10, default: 5)"),
  aspect_ratio: z
    .enum(["16:9", "9:16"])
    .optional()
    .describe("Aspect ratio (default: 16:9)"),
  save_path: z
    .string()
    .optional()
    .describe("Optional file path to save the video (e.g. ./assets/demo.mp4)"),
  project_id: z
    .string()
    .optional()
    .describe("Google Cloud project ID (uses GOOGLE_CLOUD_PROJECT env if not set)"),
};

export function registerGenerateVideo(server: McpServer): void {
  server.tool(
    "generate_video",
    "Generate a video using Google Veo 2. Returns base64 data; optionally saves to file.",
    generateVideoSchema,
    async (params) => {
      try {
        const result = await generateVideo(params.prompt, {
          durationSeconds: params.duration_seconds,
          aspectRatio: params.aspect_ratio,
          projectId: params.project_id,
        });

        let savedPath: string | undefined;
        if (params.save_path) {
          const dir = dirname(params.save_path);
          if (!existsSync(dir)) await mkdir(dir, { recursive: true });
          await writeFile(params.save_path, Buffer.from(result.base64, "base64"));
          savedPath = params.save_path;
        }

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  mime_type: result.mimeType,
                  saved_to: savedPath,
                  base64_length: result.base64.length,
                },
                null,
                2,
              ),
            },
          ],
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [{ type: "text" as const, text: JSON.stringify({ error: message }, null, 2) }],
          isError: true,
        };
      }
    },
  );
}
