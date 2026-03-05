import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { generateImage } from "../google-ai/client.js";
import { writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname } from "node:path";

export const generateImageSchema = {
  prompt: z.string().describe("Image generation prompt describing the desired image"),
  aspect_ratio: z
    .enum(["1:1", "16:9", "9:16", "4:3", "3:4"])
    .optional()
    .describe("Aspect ratio (default: 1:1)"),
  count: z
    .number()
    .min(1)
    .max(4)
    .optional()
    .describe("Number of images to generate (1-4, default: 1)"),
  save_path: z
    .string()
    .optional()
    .describe("Optional file path to save the image (e.g. ./assets/avatar.png)"),
  project_id: z
    .string()
    .optional()
    .describe("Google Cloud project ID (uses GOOGLE_CLOUD_PROJECT env if not set)"),
};

export function registerGenerateImage(server: McpServer): void {
  server.tool(
    "generate_image",
    "Generate an image using Google Imagen 3. Returns base64 data; optionally saves to file.",
    generateImageSchema,
    async (params) => {
      try {
        const results = await generateImage(params.prompt, {
          aspectRatio: params.aspect_ratio,
          numberOfImages: params.count,
          projectId: params.project_id,
        });

        const saved: string[] = [];
        if (params.save_path && results.length > 0) {
          for (let i = 0; i < results.length; i++) {
            const path = results.length === 1
              ? params.save_path
              : params.save_path.replace(/(\.\w+)$/, `-${i + 1}$1`);
            const dir = dirname(path);
            if (!existsSync(dir)) await mkdir(dir, { recursive: true });
            await writeFile(path, Buffer.from(results[i].base64, "base64"));
            saved.push(path);
          }
        }

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  count: results.length,
                  mime_type: results[0]?.mimeType,
                  saved_to: saved.length > 0 ? saved : undefined,
                  base64_preview: results.map((r) => r.base64.substring(0, 100) + "..."),
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
