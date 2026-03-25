import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAskModel } from "./tools/ask-model.js";
import { registerGenerateImage } from "./tools/generate-image.js";
import { registerGenerateVideo } from "./tools/generate-video.js";
import { registerTextToSpeech } from "./tools/text-to-speech.js";
import { registerBraveSearch } from "./tools/brave-search.js";
import { registerOpenRouterImage } from "./tools/openrouter-image.js";
import { registerFluxImage } from "./tools/flux-image.js";
import { registerKlingVideo } from "./tools/kling-video.js";
const server = new McpServer({
    name: "ai-gateway",
    version: "3.0.0",
});
// OpenRouter tools (cross-model validation + image generation)
registerAskModel(server);
registerOpenRouterImage(server);
// Google AI tools (media generation) — only register if GOOGLE_API_KEY is set
if (process.env.GOOGLE_API_KEY) {
    registerGenerateImage(server);
    registerGenerateVideo(server);
    registerTextToSpeech(server);
}
// fal.ai tools (FLUX image + Kling video) — only register if FAL_KEY is set
if (process.env.FAL_KEY) {
    registerFluxImage(server);
    registerKlingVideo(server);
}
// Brave Search tools (web/image/video search) — only register if BRAVE_API_KEY is set
if (process.env.BRAVE_API_KEY) {
    registerBraveSearch(server);
}
const transport = new StdioServerTransport();
await server.connect(transport);
