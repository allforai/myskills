import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { getModelIdForTask, getRegion, getTaskFamilyMap, getModelFamilyMap } from "../config/loader.js";
import { refreshModels } from "../config/region-detector.js";
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

export function registerAskModel(server: McpServer): void {
  server.tool("ask_model", "Send a prompt to the best AI model for the task type via OpenRouter", askModelSchema, async (params) => {
    try {
      // 根据任务特性自动选择最佳模型
      const modelId = await getModelIdForTask(params.task, params.model_family);
      const region = await getRegion();

      const messages: { role: "system" | "user"; content: string }[] = [];
      if (params.system_prompt) {
        messages.push({ role: "system", content: params.system_prompt });
      }
      messages.push({ role: "user", content: params.prompt });

      const result = await chatCompletion(modelId, messages, params.temperature);

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              {
                response: result.content,
                model_used: result.model,
                task: params.task,
                region: region,
                usage: result.usage,
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
  });

  // 刷新模型缓存 + 显示区域和路由信息
  server.tool("refresh_models", "Refresh model cache from OpenRouter API (normally cached 24h) and show current region/routing", {}, async () => {
    try {
      const familyMap = await refreshModels();
      const region = await getRegion();
      const regionMap = await getModelFamilyMap(region);
      const taskMap = getTaskFamilyMap();

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              {
                region,
                latest_models: familyMap,
                active_routing: regionMap,
                task_family_map: taskMap,
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
  });
}
