import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAskModel } from "./tools/ask-model.js";
import { registerTextToSpeech } from "./tools/text-to-speech.js";
import { registerBraveSearch } from "./tools/brave-search.js";

const server = new McpServer({
  name: "ai-gateway",
  version: "3.0.0",
});

// OpenRouter tools (cross-model validation). Image generation is Codex's job and
// video generation is the Grok CLI's (see game-art image-generation-contract).
registerAskModel(server);

// Google AI text-to-speech — only register if GOOGLE_API_KEY is set
if (process.env.GOOGLE_API_KEY) {
  registerTextToSpeech(server);
}

// Brave Search tools (web/image/video search) — only register if BRAVE_API_KEY is set
if (process.env.BRAVE_API_KEY) {
  registerBraveSearch(server);
}

const transport = new StdioServerTransport();
await server.connect(transport);
