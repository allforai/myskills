import { z } from "zod";
import { getModelIdForTask, getRegion, getTaskFamilyMap } from "../config/loader.js";
import { chatCompletion } from "../openrouter/client.js";
export const askModelSchema = {
    task: z.string().describe("Task type for routing, e.g. 'assumption_challenge', 'general'"),
    prompt: z.string().describe("The prompt to send to the model"),
    model_family: z
        .string()
        .optional()
        .describe("Override: force a specific model family (e.g. 'gpt', 'qwen', 'deepseek')"),
    system_prompt: z.string().optional().describe("Optional system prompt"),
    temperature: z.number().min(0).max(2).optional().describe("Sampling temperature (0-2)"),
};
export function registerAskModel(server) {
    server.tool("ask_model", "Send a prompt to the best AI model for the task type via OpenRouter", askModelSchema, async (params) => {
        try {
            // 根据任务特性自动选择最佳模型
            const modelId = await getModelIdForTask(params.task, params.model_family);
            const region = await getRegion();
            const messages = [];
            if (params.system_prompt) {
                messages.push({ role: "system", content: params.system_prompt });
            }
            messages.push({ role: "user", content: params.prompt });
            const result = await chatCompletion(modelId, messages, params.temperature);
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            response: result.content,
                            model_used: result.model,
                            task: params.task,
                            region: region,
                            usage: result.usage,
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
    // 区域检测工具
    server.tool("detect_region", "Detect available region and show model routing strategy", {}, async () => {
        try {
            const region = await getRegion();
            const taskMap = getTaskFamilyMap();
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            region,
                            task_routing: taskMap,
                            message: region === "china"
                                ? "中国区模式：Qwen(中文理解) + DeepSeek(推理) + Llama(严谨)"
                                : region === "global"
                                    ? "国际区模式：GPT(通用) + Gemini(发散) + Claude(严谨)"
                                    : "未知区域：使用保守路由",
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
