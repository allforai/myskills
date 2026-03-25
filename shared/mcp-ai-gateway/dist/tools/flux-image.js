import { z } from "zod";
import { generateImageFlux } from "../fal/client.js";
import { writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname } from "node:path";
export const fluxImageSchema = {
    prompt: z.string().describe("Image generation prompt"),
    model: z
        .enum(["fal-ai/flux-2-pro", "fal-ai/flux-2-dev", "fal-ai/flux-2-schnell"])
        .optional()
        .describe("Model (default: flux-2-pro). Pro=$0.055, Dev=$0.025, Schnell=$0.015 per image"),
    image_size: z
        .enum(["square", "landscape_4_3", "portrait_4_3", "landscape_16_9", "portrait_16_9"])
        .optional()
        .describe("Image size/aspect ratio (default: landscape_4_3)"),
    count: z
        .number()
        .min(1)
        .max(4)
        .optional()
        .describe("Number of images (1-4, default: 1)"),
    save_path: z
        .string()
        .optional()
        .describe("Optional file path to save the image"),
};
export function registerFluxImage(server) {
    server.tool("flux_generate_image", "Generate image using FLUX 2 Pro via fal.ai. Top Elo score, excellent prompt adherence and photorealism.", fluxImageSchema, async (params) => {
        try {
            const results = await generateImageFlux(params.prompt, {
                model: params.model,
                imageSize: params.image_size,
                numImages: params.count,
            });
            const saved = [];
            if (params.save_path && results.length > 0) {
                for (let i = 0; i < results.length; i++) {
                    const imgUrl = results[i].url;
                    if (!imgUrl)
                        continue;
                    const path = results.length === 1
                        ? params.save_path
                        : params.save_path.replace(/(\.\w+)$/, `-${i + 1}$1`);
                    const dir = dirname(path);
                    if (!existsSync(dir))
                        await mkdir(dir, { recursive: true });
                    const imgRes = await fetch(imgUrl);
                    if (imgRes.ok) {
                        const buffer = Buffer.from(await imgRes.arrayBuffer());
                        await writeFile(path, buffer);
                        saved.push(path);
                    }
                }
            }
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            count: results.length,
                            model: params.model ?? "fal-ai/flux-2-pro",
                            images: results.map((r) => ({
                                url: r.url,
                                width: r.width,
                                height: r.height,
                            })),
                            saved_to: saved.length > 0 ? saved : undefined,
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
