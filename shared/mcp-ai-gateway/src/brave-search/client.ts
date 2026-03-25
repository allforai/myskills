const WEB_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search";
const IMAGE_SEARCH_URL = "https://api.search.brave.com/res/v1/images/search";
const VIDEO_SEARCH_URL = "https://api.search.brave.com/res/v1/videos/search";

function getApiKey(): string {
  const key = process.env.BRAVE_API_KEY;
  if (!key) throw new Error("BRAVE_API_KEY environment variable is not set");
  return key;
}

export interface WebSearchResult {
  title: string;
  url: string;
  description: string;
  extraSnippets?: string[];
}

export interface WebSearchResponse {
  query: string;
  results: WebSearchResult[];
  moreResultsAvailable: boolean;
}

export interface ImageSearchResult {
  title: string;
  url: string;
  sourceUrl: string;
  width: number;
  height: number;
  thumbnail: string;
}

export interface ImageSearchResponse {
  query: string;
  results: ImageSearchResult[];
}

/**
 * Brave Web Search
 */
export async function webSearch(
  query: string,
  options: {
    count?: number;       // 1-20, default 10
    offset?: number;      // 0-9
    country?: string;     // 2-char country code
    searchLang?: string;  // ISO 639-1
    freshness?: string;   // pd/pw/pm/py or YYYY-MM-DDtoYYYY-MM-DD
    safesearch?: string;  // off/moderate/strict
  } = {},
): Promise<WebSearchResponse> {
  const apiKey = getApiKey();
  const params = new URLSearchParams({ q: query });

  if (options.count) params.set("count", String(options.count));
  if (options.offset) params.set("offset", String(options.offset));
  if (options.country) params.set("country", options.country);
  if (options.searchLang) params.set("search_lang", options.searchLang);
  if (options.freshness) params.set("freshness", options.freshness);
  if (options.safesearch) params.set("safesearch", options.safesearch);

  const res = await fetch(`${WEB_SEARCH_URL}?${params}`, {
    headers: {
      Accept: "application/json",
      "Accept-Encoding": "gzip",
      "X-Subscription-Token": apiKey,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Brave web search failed: ${res.status} ${res.statusText}\n${body}`);
  }

  const data = (await res.json()) as {
    query: { original: string; more_results_available: boolean };
    web?: {
      results: Array<{
        title: string;
        url: string;
        description: string;
        extra_snippets?: string[];
      }>;
    };
  };

  return {
    query: data.query.original,
    moreResultsAvailable: data.query.more_results_available,
    results: (data.web?.results ?? []).map((r) => ({
      title: r.title,
      url: r.url,
      description: r.description,
      extraSnippets: r.extra_snippets,
    })),
  };
}

/**
 * Brave Image Search
 */
export async function imageSearch(
  query: string,
  options: {
    count?: number;       // 1-200, default 50
    country?: string;
    searchLang?: string;
    safesearch?: string;  // off/strict
  } = {},
): Promise<ImageSearchResponse> {
  const apiKey = getApiKey();
  const params = new URLSearchParams({ q: query });

  if (options.count) params.set("count", String(options.count));
  if (options.country) params.set("country", options.country);
  if (options.searchLang) params.set("search_lang", options.searchLang);
  if (options.safesearch) params.set("safesearch", options.safesearch);

  const res = await fetch(`${IMAGE_SEARCH_URL}?${params}`, {
    headers: {
      Accept: "application/json",
      "Accept-Encoding": "gzip",
      "X-Subscription-Token": apiKey,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Brave image search failed: ${res.status} ${res.statusText}\n${body}`);
  }

  const data = (await res.json()) as {
    query: { original: string };
    results?: Array<{
      title: string;
      url: string;
      source: string;
      width: number;
      height: number;
      thumbnail?: { src: string };
      properties?: { url: string };
    }>;
  };

  return {
    query: data.query.original,
    results: (data.results ?? []).map((r) => ({
      title: r.title,
      url: r.properties?.url ?? r.url,
      sourceUrl: r.source,
      width: r.width,
      height: r.height,
      thumbnail: r.thumbnail?.src ?? r.url,
    })),
  };
}

export interface VideoSearchResult {
  title: string;
  url: string;
  description: string;
  thumbnail: string;
  duration?: string;
  publisher?: string;
}

export interface VideoSearchResponse {
  query: string;
  results: VideoSearchResult[];
}

/**
 * Brave Video Search
 */
export async function videoSearch(
  query: string,
  options: {
    count?: number;       // 1-50, default 20
    offset?: number;      // 0-9
    country?: string;
    searchLang?: string;
    freshness?: string;
    safesearch?: string;
  } = {},
): Promise<VideoSearchResponse> {
  const apiKey = getApiKey();
  const params = new URLSearchParams({ q: query });

  if (options.count) params.set("count", String(options.count));
  if (options.offset) params.set("offset", String(options.offset));
  if (options.country) params.set("country", options.country);
  if (options.searchLang) params.set("search_lang", options.searchLang);
  if (options.freshness) params.set("freshness", options.freshness);
  if (options.safesearch) params.set("safesearch", options.safesearch);

  const res = await fetch(`${VIDEO_SEARCH_URL}?${params}`, {
    headers: {
      Accept: "application/json",
      "Accept-Encoding": "gzip",
      "X-Subscription-Token": apiKey,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Brave video search failed: ${res.status} ${res.statusText}\n${body}`);
  }

  const data = (await res.json()) as {
    query: { original: string };
    results?: Array<{
      title: string;
      url: string;
      description?: string;
      thumbnail?: { src: string };
      video?: { duration?: string; publisher?: string };
    }>;
  };

  return {
    query: data.query.original,
    results: (data.results ?? []).map((r) => ({
      title: r.title,
      url: r.url,
      description: r.description ?? "",
      thumbnail: r.thumbnail?.src ?? "",
      duration: r.video?.duration,
      publisher: r.video?.publisher,
    })),
  };
}
