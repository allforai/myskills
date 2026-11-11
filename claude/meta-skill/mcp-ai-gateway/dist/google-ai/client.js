const TTS_BASE = "https://texttospeech.googleapis.com/v1";
function getApiKey() {
    const key = process.env.GOOGLE_API_KEY;
    if (!key)
        throw new Error("GOOGLE_API_KEY environment variable is not set");
    return key;
}
/**
 * Text-to-speech using Google Cloud TTS
 */
export async function textToSpeech(text, options = {}) {
    const res = await fetch(`${TTS_BASE}/text:synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": getApiKey() },
        body: JSON.stringify({
            input: { text },
            voice: {
                languageCode: options.languageCode ?? "en-US",
                ...(options.voiceName && { name: options.voiceName }),
            },
            audioConfig: {
                audioEncoding: options.audioEncoding ?? "MP3",
                ...(options.speakingRate && { speakingRate: options.speakingRate }),
            },
        }),
    });
    if (!res.ok) {
        const errorBody = await res.text();
        throw new Error(`Google TTS failed: ${res.status} ${res.statusText}\n${errorBody}`);
    }
    const body = (await res.json());
    return {
        base64: body.audioContent,
        mimeType: options.audioEncoding === "OGG_OPUS" ? "audio/ogg" : "audio/mpeg",
    };
}
