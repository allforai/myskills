const BASE_URL = "https://openrouter.ai/api/v1";
function getApiKey() {
    const key = process.env.OPENROUTER_API_KEY;
    if (!key)
        throw new Error("OPENROUTER_API_KEY environment variable is not set");
    return key;
}
export async function fetchModels() {
    const res = await fetch(`${BASE_URL}/models`, {
        headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
        throw new Error(`OpenRouter /models failed: ${res.status} ${res.statusText}`);
    }
    const body = (await res.json());
    return body.data;
}
export async function chatCompletion(model, messages, temperature) {
    const apiKey = getApiKey();
    const res = await fetch(`${BASE_URL}/chat/completions`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
            model,
            messages,
            ...(temperature !== undefined && { temperature }),
        }),
    });
    if (!res.ok) {
        const errorBody = await res.text();
        throw new Error(`OpenRouter chat failed: ${res.status} ${res.statusText}\n${errorBody}`);
    }
    const body = (await res.json());
    const content = body.choices[0]?.message?.content ?? "";
    return { content, model: body.model, usage: body.usage };
}
