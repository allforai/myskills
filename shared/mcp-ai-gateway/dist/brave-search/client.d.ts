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
export declare function webSearch(query: string, options?: {
    count?: number;
    offset?: number;
    country?: string;
    searchLang?: string;
    freshness?: string;
    safesearch?: string;
}): Promise<WebSearchResponse>;
/**
 * Brave Image Search
 */
export declare function imageSearch(query: string, options?: {
    count?: number;
    country?: string;
    searchLang?: string;
    safesearch?: string;
}): Promise<ImageSearchResponse>;
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
export declare function videoSearch(query: string, options?: {
    count?: number;
    offset?: number;
    country?: string;
    searchLang?: string;
    freshness?: string;
    safesearch?: string;
}): Promise<VideoSearchResponse>;
