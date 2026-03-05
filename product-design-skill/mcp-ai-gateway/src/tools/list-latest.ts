import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { resolveAllFamilies } from "../openrouter/resolver.js";

export function registerListLatest(server: McpServer): void {
  server.tool("list_latest_models", "Query OpenRouter and return the latest resolved model for each family", {}, async () => {
    try {
      const result = await resolveAllFamilies();
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(result, null, 2),
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
