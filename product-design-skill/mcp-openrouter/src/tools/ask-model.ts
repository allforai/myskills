import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { loadRouting, resolveFamily } from "../config/loader.js";
import { resolveLatestModel } from "../openrouter/resolver.js";
import { chatCompletion } from "../openrouter/client.js";

export const askModelSchema = {
  task: z.string().describe("Task type for routing, e.g. 'competitive_analysis', 'general'"),
  prompt: z.string().describe("The prompt to send to the model"),
  model_family: z
    .string()
    .optional()
    .describe("Override: force a specific model family (e.g. 'gpt', 'gemini')"),
  system_prompt: z.string().optional().describe("Optional system prompt"),
  temperature: z.number().min(0).max(2).optional().describe("Sampling temperature (0-2)"),
};

export function registerAskModel(server: McpServer): void {
  server.tool("ask_model", "Send a prompt to an AI model selected by task type via OpenRouter", askModelSchema, async (params) => {
    try {
      const routing = await loadRouting();
      const familyId = resolveFamily(routing, params.task, params.model_family);
      const modelId = await resolveLatestModel(familyId);

      if (!modelId) {
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                { error: `No model found for family "${familyId}"` },
                null,
                2,
              ),
            },
          ],
        };
      }

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
                family: familyId,
                task: params.task,
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
}
