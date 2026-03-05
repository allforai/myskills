import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAskModel } from "./tools/ask-model.js";
import { registerGenerateImage } from "./tools/generate-image.js";
import { registerGenerateVideo } from "./tools/generate-video.js";
import { registerTextToSpeech } from "./tools/text-to-speech.js";
import { registerBraveSearch } from "./tools/brave-search.js";

const server = new McpServer({
  name: "ai-gateway",
  version: "2.1.0",
});

// OpenRouter tools (cross-model validation)
registerAskModel(server);

// Google AI tools (media generation) — only register if GOOGLE_API_KEY is set
if (process.env.GOOGLE_API_KEY) {
  registerGenerateImage(server);
  registerGenerateVideo(server);
  registerTextToSpeech(server);
}

// Brave Search tools (web/image/video search) — only register if BRAVE_API_KEY is set
if (process.env.BRAVE_API_KEY) {
  registerBraveSearch(server);
}

const transport = new StdioServerTransport();
await server.connect(transport);
