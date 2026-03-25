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
export declare function fetchModels(): Promise<OpenRouterModel[]>;
export declare function chatCompletion(model: string, messages: ChatMessage[], temperature?: number): Promise<{
    content: string;
    model: string;
    usage?: ChatResponse["usage"];
}>;
export {};
