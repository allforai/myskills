const IMAGEN_BASE = "https://us-central1-aiplatform.googleapis.com/v1";
const TTS_BASE = "https://texttospeech.googleapis.com/v1";

function getApiKey(): string {
  const key = process.env.GOOGLE_API_KEY;
  if (!key) throw new Error("GOOGLE_API_KEY environment variable is not set");
  return key;
}

export interface ImageResult {
  base64: string;
  mimeType: string;
}

export interface VideoResult {
  base64: string;
  mimeType: string;
}

export interface TTSResult {
  base64: string;
  mimeType: string;
}

/**
 * Generate image using Imagen 3
 */
export async function generateImage(
  prompt: string,
  options: {
    aspectRatio?: string;     // "1:1" | "16:9" | "9:16" | "4:3" | "3:4"
    numberOfImages?: number;  // 1-4
    projectId?: string;
  } = {},
): Promise<ImageResult[]> {
  const apiKey = getApiKey();
  const projectId = options.projectId || process.env.GOOGLE_CLOUD_PROJECT || "default";
  const model = "imagen-3.0-generate-002";
  const url = `${IMAGEN_BASE}/projects/${projectId}/locations/us-central1/publishers/google/models/${model}:predict`;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
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
    throw new Error(`Imagen 3 failed: ${res.status} ${res.statusText}\n${errorBody}`);
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
 * Generate video using Veo 2
 */
export async function generateVideo(
  prompt: string,
  options: {
    durationSeconds?: number; // 5-10
    aspectRatio?: string;     // "16:9" | "9:16"
    projectId?: string;
  } = {},
): Promise<VideoResult> {
  const apiKey = getApiKey();
  const projectId = options.projectId || process.env.GOOGLE_CLOUD_PROJECT || "default";
  const model = "veo-2.0-generate-exp";
  const url = `${IMAGEN_BASE}/projects/${projectId}/locations/us-central1/publishers/google/models/${model}:predict`;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      instances: [{ prompt }],
      parameters: {
        durationSeconds: options.durationSeconds ?? 5,
        aspectRatio: options.aspectRatio ?? "16:9",
      },
    }),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Veo 2 failed: ${res.status} ${res.statusText}\n${errorBody}`);
  }

  const body = (await res.json()) as {
    predictions: Array<{ bytesBase64Encoded: string; mimeType: string }>;
  };

  const prediction = body.predictions?.[0];
  if (!prediction) throw new Error("Veo 2 returned no predictions");

  return {
    base64: prediction.bytesBase64Encoded,
    mimeType: prediction.mimeType || "video/mp4",
  };
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
