export interface FalImageResult {
    url: string;
    width: number;
    height: number;
    content_type: string;
}
export interface FalVideoResult {
    url: string;
}
export declare function generateImageFlux(prompt: string, options?: {
    imageSize?: string;
    numImages?: number;
    model?: string;
}): Promise<FalImageResult[]>;
export declare function generateVideoKling(prompt: string, options?: {
    duration?: string;
    aspectRatio?: string;
    model?: string;
}): Promise<FalVideoResult>;
