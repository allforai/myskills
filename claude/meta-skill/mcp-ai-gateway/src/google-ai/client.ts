const TTS_BASE = "https://texttospeech.googleapis.com/v1";

function getApiKey(): string {
  const key = process.env.GOOGLE_API_KEY;
  if (!key) throw new Error("GOOGLE_API_KEY environment variable is not set");
  return key;
}

export interface TTSResult {
  base64: string;
  mimeType: string;
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

  const body = (await res.json()) as { audioContent: string };

  return {
    base64: body.audioContent,
    mimeType: options.audioEncoding === "OGG_OPUS" ? "audio/ogg" : "audio/mpeg",
  };
}
