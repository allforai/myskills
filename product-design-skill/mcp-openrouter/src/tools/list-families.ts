import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { getFamilies } from "../openrouter/resolver.js";

export function registerListFamilies(server: McpServer): void {
  server.tool("list_families", "List all supported model families with their strengths and best-for tasks", {}, async () => {
    const data = getFamilies();
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  });
}
