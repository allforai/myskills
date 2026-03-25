const BASE_URL = "https://openrouter.ai/api/v1";

export interface OpenRouterModel {
  id: string;
  name: string;
  created: number;
  context_length?: number;
  pricing?: {
    prompt?: string;
    completion?: string;
  };
}

interface ModelsResponse {
  data: OpenRouterModel[];
}

interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

interface ChatChoice {
  message: {
    role: string;
    content: string;
  };
}

interface ChatResponse {
  id: string;
  model: string;
  choices: ChatChoice[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

function getApiKey(): string {
  const key = process.env.OPENROUTER_API_KEY;
  if (!key) throw new Error("OPENROUTER_API_KEY environment variable is not set");
  return key;
}

export async function fetchModels(): Promise<OpenRouterModel[]> {
  const res = await fetch(`${BASE_URL}/models`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`OpenRouter /models failed: ${res.status} ${res.statusText}`);
  }
  const body = (await res.json()) as ModelsResponse;
  return body.data;
}

export async function chatCompletion(
  model: string,
  messages: ChatMessage[],
  temperature?: number,
): Promise<{ content: string; model: string; usage?: ChatResponse["usage"] }> {
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
  const body = (await res.json()) as ChatResponse;
  const content = body.choices[0]?.message?.content ?? "";
  return { content, model: body.model, usage: body.usage };
}
