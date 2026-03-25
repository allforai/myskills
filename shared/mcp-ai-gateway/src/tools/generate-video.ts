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
    .optional()
    .describe("Video duration in seconds: 4, 6, or 8 (default: 8)"),
  aspect_ratio: z
    .enum(["16:9", "9:16"])
    .optional()
    .describe("Aspect ratio (default: 16:9)"),
  resolution: z
    .enum(["720p", "1080p", "4k"])
    .optional()
    .describe("Video resolution (default: 720p)"),
  save_path: z
    .string()
    .optional()
    .describe("Optional file path to download and save the video (e.g. ./assets/demo.mp4)"),
};

export function registerGenerateVideo(server: McpServer): void {
  server.tool(
    "generate_video",
    "Generate a video using Google Veo 3.1. Submits async task, polls for completion, returns video URL. Optionally downloads to file.",
    generateVideoSchema,
    async (params) => {
      try {
        const result = await generateVideo(params.prompt, {
          durationSeconds: params.duration_seconds,
          aspectRatio: params.aspect_ratio,
          resolution: params.resolution,
        });

        let savedPath: string | undefined;
        if (params.save_path && result.videoUrl) {
          const dir = dirname(params.save_path);
          if (!existsSync(dir)) await mkdir(dir, { recursive: true });
          const videoRes = await fetch(result.videoUrl);
          if (videoRes.ok) {
            const buffer = Buffer.from(await videoRes.arrayBuffer());
            await writeFile(params.save_path, buffer);
            savedPath = params.save_path;
          }
        }

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  video_url: result.videoUrl,
                  saved_to: savedPath,
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
