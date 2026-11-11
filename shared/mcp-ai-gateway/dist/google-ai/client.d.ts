export interface TTSResult {
    base64: string;
    mimeType: string;
}
/**
 * Text-to-speech using Google Cloud TTS
 */
export declare function textToSpeech(text: string, options?: {
    languageCode?: string;
    voiceName?: string;
    speakingRate?: number;
    audioEncoding?: string;
}): Promise<TTSResult>;
