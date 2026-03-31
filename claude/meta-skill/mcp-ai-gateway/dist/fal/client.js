const FAL_BASE = "https://fal.run";
const FAL_QUEUE_BASE = "https://queue.fal.run";
const POLL_INTERVAL_MS = 5000;
const MAX_POLL_ATTEMPTS = 120; // 10 min
function getApiKey() {
    const key = process.env.FAL_KEY;
    if (!key)
        throw new Error("FAL_KEY environment variable is not set");
    return key;
}
function headers() {
    return {
        "Content-Type": "application/json",
        Authorization: `Key ${getApiKey()}`,
    };
}
// ---------- Synchronous call (fast models like FLUX) ----------
async function falRun(modelId, input) {
    const res = await fetch(`${FAL_BASE}/${modelId}`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(input),
    });
    if (!res.ok) {
        const errorBody = await res.text();
        throw new Error(`fal.ai ${modelId} failed: ${res.status} ${res.statusText}\n${errorBody}`);
    }
    return (await res.json());
}
// ---------- Queue-based call (slow models like Kling video) ----------
async function falQueue(modelId, input) {
    // Submit
    const submitRes = await fetch(`${FAL_QUEUE_BASE}/${modelId}`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(input),
    });
    if (!submitRes.ok) {
        const errorBody = await submitRes.text();
        throw new Error(`fal.ai queue submit failed: ${submitRes.status} ${submitRes.statusText}\n${errorBody}`);
    }
    const submitBody = (await submitRes.json());
    const { status_url, response_url } = submitBody;
    // Poll for completion using the URLs returned by fal
    for (let i = 0; i < MAX_POLL_ATTEMPTS; i++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        const statusRes = await fetch(status_url, { headers: headers() });
        if (!statusRes.ok)
            continue;
        const status = (await statusRes.json());
        if (status.status === "COMPLETED") {
            const resultRes = await fetch(response_url, { headers: headers() });
            if (!resultRes.ok) {
                const errorBody = await resultRes.text();
                throw new Error(`fal.ai result fetch failed: ${resultRes.status}\n${errorBody}`);
            }
            return (await resultRes.json());
        }
        if (status.status === "FAILED") {
            throw new Error(`fal.ai ${modelId} job failed (request_id: ${submitBody.request_id})`);
        }
    }
    throw new Error(`fal.ai ${modelId} timed out after ${(MAX_POLL_ATTEMPTS * POLL_INTERVAL_MS) / 1000}s`);
}
// ---------- FLUX 2 Pro ----------
export async function generateImageFlux(prompt, options = {}) {
    const modelId = options.model ?? "fal-ai/flux-2-pro";
    const result = await falRun(modelId, {
        prompt,
        image_size: options.imageSize ?? "landscape_4_3",
        num_images: options.numImages ?? 1,
    });
    return result.images ?? [];
}
// ---------- Kling Video ----------
export async function generateVideoKling(prompt, options = {}) {
    const modelId = options.model ?? "fal-ai/kling-video/v2.1/master/text-to-video";
    const result = await falQueue(modelId, {
        prompt,
        duration: options.duration ?? "5",
        aspect_ratio: options.aspectRatio ?? "16:9",
    });
    if (!result.video?.url)
        throw new Error("Kling completed but returned no video URL");
    return result.video;
}
