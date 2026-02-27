import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAskModel } from "./tools/ask-model.js";

const server = new McpServer({
  name: "openrouter",
  version: "1.1.0",
});

registerAskModel(server);

const transport = new StdioServerTransport();
await server.connect(transport);
