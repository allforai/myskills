import { z } from "zod";
import { writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname } from "node:path";
const BASE_URL = "https://openrouter.ai/api/v1";
function getApiKey() {
    const key = process.env.OPENROUTER_API_KEY;
    if (!key)
        throw new Error("OPENROUTER_API_KEY is not set");
    return key;
}
export const openrouterImageSchema = {
    prompt: z.string().describe("Image generation prompt"),
    model: z
        .enum([
        "openai/gpt-5-image",
        "openai/gpt-5-image-mini",
        "google/gemini-2.5-flash-image",
        "google/gemini-3.1-flash-image-preview",
        "google/gemini-3-pro-image-preview",
    ])
        .optional()
        .describe("Model (default: openai/gpt-5-image-mini). Mini is cheapest ~$0.02/img"),
    save_path: z
        .string()
        .optional()
        .describe("Optional file path to save the image (e.g. ./assets/hero.png)"),
};
export function registerOpenRouterImage(server) {
    server.tool("openrouter_generate_image", "Generate image via OpenRouter using GPT-5 Image or Gemini Image models. Uses existing OpenRouter key, no extra API key needed.", openrouterImageSchema, async (params) => {
        try {
            const model = params.model ?? "openai/gpt-5-image-mini";
            const isGemini = model.startsWith("google/");
            const res = await fetch(`${BASE_URL}/chat/completions`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${getApiKey()}`,
                },
                body: JSON.stringify({
                    model,
                    messages: [{ role: "user", content: params.prompt }],
                    modalities: isGemini ? ["image", "text"] : ["image"],
                }),
            });
            if (!res.ok) {
                const errorBody = await res.text();
                throw new Error(`OpenRouter image failed: ${res.status} ${res.statusText}\n${errorBody}`);
            }
            const body = (await res.json());
            const msg = body.choices?.[0]?.message;
            const images = msg?.images ?? [];
            const saved = [];
            if (params.save_path && images.length > 0) {
                for (let i = 0; i < images.length; i++) {
                    const dataUrl = images[i].image_url?.url;
                    if (!dataUrl)
                        continue;
                    // data:image/png;base64,xxxxx
                    const base64Match = dataUrl.match(/^data:image\/\w+;base64,(.+)$/);
                    if (!base64Match)
                        continue;
                    const path = images.length === 1
                        ? params.save_path
                        : params.save_path.replace(/(\.\w+)$/, `-${i + 1}$1`);
                    const dir = dirname(path);
                    if (!existsSync(dir))
                        await mkdir(dir, { recursive: true });
                    await writeFile(path, Buffer.from(base64Match[1], "base64"));
                    saved.push(path);
                }
            }
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            model,
                            image_count: images.length,
                            text_response: msg?.content ?? null,
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
