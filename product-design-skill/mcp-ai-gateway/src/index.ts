import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAskModel } from "./tools/ask-model.js";
import { registerGenerateImage } from "./tools/generate-image.js";
import { registerGenerateVideo } from "./tools/generate-video.js";
import { registerTextToSpeech } from "./tools/text-to-speech.js";

const server = new McpServer({
  name: "ai-gateway",
  version: "2.0.0",
});

// OpenRouter tools (cross-model validation)
registerAskModel(server);

// Google AI tools (media generation) — only register if GOOGLE_API_KEY is set
if (process.env.GOOGLE_API_KEY) {
  registerGenerateImage(server);
  registerGenerateVideo(server);
  registerTextToSpeech(server);
}

const transport = new StdioServerTransport();
await server.connect(transport);
