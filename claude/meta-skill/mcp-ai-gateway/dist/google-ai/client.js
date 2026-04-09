const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta";
const TTS_BASE = "https://texttospeech.googleapis.com/v1";
const VIDEO_POLL_INTERVAL_MS = 10000;
const VIDEO_MAX_POLL_ATTEMPTS = 60; // 10 min max
function getApiKey() {
    const key = process.env.GOOGLE_API_KEY;
    if (!key)
        throw new Error("GOOGLE_API_KEY environment variable is not set");
    return key;
}
function geminiHeaders() {
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": getApiKey(),
    };
}
/**
 * Generate image using Imagen 4 via Gemini API
 */
export async function generateImage(prompt, options = {}) {
    const model = options.model ?? "imagen-4.0-generate-001";
    const url = `${GEMINI_BASE}/models/${model}:predict`;
    const res = await fetch(url, {
        method: "POST",
        headers: geminiHeaders(),
        body: JSON.stringify({
            instances: [{ prompt }],
            parameters: {
                sampleCount: options.numberOfImages ?? 1,
                aspectRatio: options.aspectRatio ?? "1:1",
            },
        }),
    });
    if (!res.ok) {
        const errorBody = await res.text();
        throw new Error(`Imagen 4 failed: ${res.status} ${res.statusText}\n${errorBody}`);
    }
    const body = (await res.json());
    return (body.predictions ?? []).map((p) => ({
        base64: p.bytesBase64Encoded,
        mimeType: p.mimeType || "image/png",
    }));
}
/**
 * Generate video using Veo 3.1 via Gemini API (async with polling)
 */
export async function generateVideo(prompt, options = {}) {
    const model = options.model ?? "veo-3.1-generate-preview";
    const url = `${GEMINI_BASE}/models/${model}:predictLongRunning`;
    const res = await fetch(url, {
        method: "POST",
        headers: geminiHeaders(),
        body: JSON.stringify({
            instances: [{ prompt }],
            parameters: {
                aspectRatio: options.aspectRatio ?? "16:9",
                durationSeconds: options.durationSeconds ?? 8,
                resolution: options.resolution ?? "720p",
            },
        }),
    });
    if (!res.ok) {
        const errorBody = await res.text();
        throw new Error(`Veo 3.1 failed: ${res.status} ${res.statusText}\n${errorBody}`);
    }
    const initBody = (await res.json());
    const operationName = initBody.name;
    // Poll for completion
    for (let i = 0; i < VIDEO_MAX_POLL_ATTEMPTS; i++) {
        await new Promise((r) => setTimeout(r, VIDEO_POLL_INTERVAL_MS));
        const pollRes = await fetch(`${GEMINI_BASE}/${operationName}`, {
            headers: geminiHeaders(),
        });
        if (!pollRes.ok) {
            const errorBody = await pollRes.text();
            throw new Error(`Veo poll failed: ${pollRes.status} ${pollRes.statusText}\n${errorBody}`);
        }
        const pollBody = (await pollRes.json());
        if (pollBody.done) {
            const videoUri = pollBody.response?.generateVideoResponse?.generatedSamples?.[0]?.video?.uri;
            if (!videoUri)
                throw new Error("Veo 3.1 completed but returned no video URI");
            return { videoUrl: videoUri };
        }
    }
    throw new Error(`Veo 3.1 timed out after ${(VIDEO_MAX_POLL_ATTEMPTS * VIDEO_POLL_INTERVAL_MS) / 1000}s`);
}
/**
 * Text-to-speech using Google Cloud TTS
 */
export async function textToSpeech(text, options = {}) {
    const apiKey = getApiKey();
    const url = `${TTS_BASE}/text:synthesize?key=${apiKey}`;
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
