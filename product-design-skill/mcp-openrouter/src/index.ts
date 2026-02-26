import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAskModel } from "./tools/ask-model.js";
import { registerListFamilies } from "./tools/list-families.js";
import { registerListLatest } from "./tools/list-latest.js";

const server = new McpServer({
  name: "openrouter",
  version: "1.0.0",
});

registerAskModel(server);
registerListFamilies(server);
registerListLatest(server);

const transport = new StdioServerTransport();
await server.connect(transport);
