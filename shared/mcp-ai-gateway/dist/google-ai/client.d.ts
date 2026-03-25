export interface ImageResult {
    base64: string;
    mimeType: string;
}
export interface VideoResult {
    videoUrl: string;
}
export interface TTSResult {
    base64: string;
    mimeType: string;
}
/**
 * Generate image using Imagen 4 via Gemini API
 */
export declare function generateImage(prompt: string, options?: {
    aspectRatio?: string;
    numberOfImages?: number;
    model?: string;
}): Promise<ImageResult[]>;
/**
 * Generate video using Veo 3.1 via Gemini API (async with polling)
 */
export declare function generateVideo(prompt: string, options?: {
    durationSeconds?: number;
    aspectRatio?: string;
    resolution?: string;
    model?: string;
}): Promise<VideoResult>;
/**
 * Text-to-speech using Google Cloud TTS
 */
export declare function textToSpeech(text: string, options?: {
    languageCode?: string;
    voiceName?: string;
    speakingRate?: number;
    audioEncoding?: string;
}): Promise<TTSResult>;
