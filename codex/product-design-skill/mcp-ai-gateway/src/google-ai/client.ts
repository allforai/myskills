const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta";
const TTS_BASE = "https://texttospeech.googleapis.com/v1";
const VIDEO_POLL_INTERVAL_MS = 10000;
const VIDEO_MAX_POLL_ATTEMPTS = 60; // 10 min max

function getApiKey(): string {
  const key = process.env.GOOGLE_API_KEY;
  if (!key) throw new Error("GOOGLE_API_KEY environment variable is not set");
  return key;
}

function geminiHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "x-goog-api-key": getApiKey(),
  };
}

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
export async function generateImage(
  prompt: string,
  options: {
    aspectRatio?: string;     // "1:1" | "16:9" | "9:16" | "4:3" | "3:4"
    numberOfImages?: number;  // 1-4
    model?: string;           // imagen-4.0-generate-001 (default) | imagen-4.0-fast-generate-001
  } = {},
): Promise<ImageResult[]> {
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

  const body = (await res.json()) as {
    predictions: Array<{ bytesBase64Encoded: string; mimeType: string }>;
  };

  return (body.predictions ?? []).map((p) => ({
    base64: p.bytesBase64Encoded,
    mimeType: p.mimeType || "image/png",
  }));
}

/**
 * Generate video using Veo 3.1 via Gemini API (async with polling)
 */
export async function generateVideo(
  prompt: string,
  options: {
    durationSeconds?: number; // 4 | 6 | 8
    aspectRatio?: string;     // "16:9" | "9:16"
    resolution?: string;      // "720p" | "1080p" | "4k"
    model?: string;           // veo-3.1-generate-preview (default)
  } = {},
): Promise<VideoResult> {
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

  const initBody = (await res.json()) as { name: string };
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

    const pollBody = (await pollRes.json()) as {
      done?: boolean;
      response?: {
        generateVideoResponse?: {
          generatedSamples?: Array<{ video?: { uri?: string } }>;
        };
      };
    };

    if (pollBody.done) {
      const videoUri =
        pollBody.response?.generateVideoResponse?.generatedSamples?.[0]?.video?.uri;
      if (!videoUri) throw new Error("Veo 3.1 completed but returned no video URI");
      return { videoUrl: videoUri };
    }
  }

  throw new Error(`Veo 3.1 timed out after ${(VIDEO_MAX_POLL_ATTEMPTS * VIDEO_POLL_INTERVAL_MS) / 1000}s`);
}

/**
 * Text-to-speech using Google Cloud TTS
 */
export async function textToSpeech(
  text: string,
  options: {
    languageCode?: string;    // "en-US" | "zh-CN" etc.
    voiceName?: string;       // e.g. "en-US-Neural2-F"
    speakingRate?: number;    // 0.25-4.0
    audioEncoding?: string;   // "MP3" | "LINEAR16" | "OGG_OPUS"
  } = {},
): Promise<TTSResult> {
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

  const body = (await res.json()) as { audioContent: string };

  return {
    base64: body.audioContent,
    mimeType: options.audioEncoding === "OGG_OPUS" ? "audio/ogg" : "audio/mpeg",
  };
}
