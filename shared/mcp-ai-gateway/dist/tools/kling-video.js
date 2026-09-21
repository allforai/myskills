import { z } from "zod";
import { generateVideoKling } from "../fal/client.js";
import { checkSavePath, saveFile } from "./save-file.js";
export const klingVideoSchema = {
    prompt: z.string().describe("Video generation prompt"),
    duration: z
        .enum(["5", "10"])
        .optional()
        .describe("Video duration in seconds: 5 or 10 (default: 5)"),
    aspect_ratio: z
        .enum(["16:9", "9:16", "1:1"])
        .optional()
        .describe("Aspect ratio (default: 16:9)"),
    save_path: z
        .string()
        .optional()
        .describe("Optional file path to download and save the video"),
};
export function registerKlingVideo(server) {
    server.tool("kling_generate_video", "Generate video using Kling 2.1 Master via fal.ai. Best value at ~$0.03/sec, 4K support, native audio.", klingVideoSchema, async (params) => {
        try {
            if (params.save_path)
                checkSavePath(params.save_path);
            const result = await generateVideoKling(params.prompt, {
                duration: params.duration,
                aspectRatio: params.aspect_ratio,
            });
            let savedPath;
            if (params.save_path && result.url) {
                const videoRes = await fetch(result.url);
                if (videoRes.ok) {
                    const buffer = Buffer.from(await videoRes.arrayBuffer());
                    await saveFile(params.save_path, buffer);
                    savedPath = params.save_path;
                }
            }
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            video_url: result.url,
                            saved_to: savedPath,
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
