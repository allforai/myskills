const WEB_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search";
const IMAGE_SEARCH_URL = "https://api.search.brave.com/res/v1/images/search";
const VIDEO_SEARCH_URL = "https://api.search.brave.com/res/v1/videos/search";
function getApiKey() {
    const key = process.env.BRAVE_API_KEY;
    if (!key)
        throw new Error("BRAVE_API_KEY environment variable is not set");
    return key;
}
/**
 * Brave Web Search
 */
export async function webSearch(query, options = {}) {
    const apiKey = getApiKey();
    const params = new URLSearchParams({ q: query });
    if (options.count)
        params.set("count", String(options.count));
    if (options.offset)
        params.set("offset", String(options.offset));
    if (options.country)
        params.set("country", options.country);
    if (options.searchLang)
        params.set("search_lang", options.searchLang);
    if (options.freshness)
        params.set("freshness", options.freshness);
    if (options.safesearch)
        params.set("safesearch", options.safesearch);
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
    const data = (await res.json());
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
export async function imageSearch(query, options = {}) {
    const apiKey = getApiKey();
    const params = new URLSearchParams({ q: query });
    if (options.count)
        params.set("count", String(options.count));
    if (options.country)
        params.set("country", options.country);
    if (options.searchLang)
        params.set("search_lang", options.searchLang);
    if (options.safesearch)
        params.set("safesearch", options.safesearch);
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
    const data = (await res.json());
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
/**
 * Brave Video Search
 */
export async function videoSearch(query, options = {}) {
    const apiKey = getApiKey();
    const params = new URLSearchParams({ q: query });
    if (options.count)
        params.set("count", String(options.count));
    if (options.offset)
        params.set("offset", String(options.offset));
    if (options.country)
        params.set("country", options.country);
    if (options.searchLang)
        params.set("search_lang", options.searchLang);
    if (options.freshness)
        params.set("freshness", options.freshness);
    if (options.safesearch)
        params.set("safesearch", options.safesearch);
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
    const data = (await res.json());
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
