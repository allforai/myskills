import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { webSearch, imageSearch, videoSearch } from "../brave-search/client.js";

export function registerBraveSearch(server: McpServer): void {
  // Web search
  server.tool(
    "brave_web_search",
    "Search the web using Brave Search. Returns titles, URLs, and descriptions.",
    {
      query: z.string().describe("Search query (supports operators: quotes, minus, site:, filetype:)"),
      count: z.number().min(1).max(20).optional().describe("Number of results (1-20, default: 10)"),
      offset: z.number().min(0).max(9).optional().describe("Result offset for pagination (0-9)"),
      country: z.string().optional().describe("2-char country code for localized results (e.g. US, CN, JP)"),
      search_lang: z.string().optional().describe("ISO 639-1 language code (e.g. en, zh, ja)"),
      freshness: z
        .string()
        .optional()
        .describe("Time filter: pd=24h, pw=7d, pm=31d, py=1yr, or YYYY-MM-DDtoYYYY-MM-DD"),
      safesearch: z.enum(["off", "moderate", "strict"]).optional().describe("Content filter (default: moderate)"),
    },
    async (params) => {
      try {
        const result = await webSearch(params.query, {
          count: params.count,
          offset: params.offset,
          country: params.country,
          searchLang: params.search_lang,
          freshness: params.freshness,
          safesearch: params.safesearch,
        });

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
    },
  );

  // Image search
  server.tool(
    "brave_image_search",
    "Search for images using Brave Image Search. Returns image URLs, dimensions, and thumbnails.",
    {
      query: z.string().describe("Image search query"),
      count: z.number().min(1).max(200).optional().describe("Number of images (1-200, default: 50)"),
      country: z.string().optional().describe("2-char country code"),
      search_lang: z.string().optional().describe("ISO 639-1 language code"),
      safesearch: z.enum(["off", "strict"]).optional().describe("Content filter (default: strict)"),
    },
    async (params) => {
      try {
        const result = await imageSearch(params.query, {
          count: params.count,
          country: params.country,
          searchLang: params.search_lang,
          safesearch: params.safesearch,
        });

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
    },
  );

  // Video search
  server.tool(
    "brave_video_search",
    "Search for videos using Brave Video Search. Returns video URLs, thumbnails, and metadata.",
    {
      query: z.string().describe("Video search query"),
      count: z.number().min(1).max(50).optional().describe("Number of videos (1-50, default: 20)"),
      offset: z.number().min(0).max(9).optional().describe("Result offset for pagination (0-9)"),
      country: z.string().optional().describe("2-char country code"),
      search_lang: z.string().optional().describe("ISO 639-1 language code"),
      freshness: z
        .string()
        .optional()
        .describe("Time filter: pd=24h, pw=7d, pm=31d, py=1yr, or YYYY-MM-DDtoYYYY-MM-DD"),
      safesearch: z.enum(["off", "moderate", "strict"]).optional().describe("Content filter (default: moderate)"),
    },
    async (params) => {
      try {
        const result = await videoSearch(params.query, {
          count: params.count,
          offset: params.offset,
          country: params.country,
          searchLang: params.search_lang,
          freshness: params.freshness,
          safesearch: params.safesearch,
        });

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
    },
  );
}
