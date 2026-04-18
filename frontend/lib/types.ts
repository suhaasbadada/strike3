export type PipelineStatus = 'idle' | 'ocr' | 'compress' | 'verify' | 'complete';

export interface TreeNode {
    id: number;
    weight: number;
    symbol: number | string | null;
    label: string;
}
  
export interface TreeEdge {
    from: number;
    to: number;
    label: string;
}

export interface TreeData {
    nodes: TreeNode[];
    edges: TreeEdge[];
}

export interface Step {
    index: number;
    symbol: number | null;
    char: string | null;
    tree: TreeData;
}
  
export interface CompressionData {
    compressed_data: string;
    compression_ratio: number;
    entropy: number;
    encoding_efficiency: number;
    original_size: number;
    compressed_size: number;
    latency: number;
    huffman_tree: {
        root: string;
        structure: TreeData;
    };
    steps: Step[];
}

export interface VerificationData {
    is_lossless: boolean;
    char_match: number;
    char_total: number;
    match_percentage: number;
}

export interface ProcessImageResponse {
    ocr_text: string;
    ocr_latency: number;
    compression: CompressionData;
    decompression: {
        text: string;
        latency: number;
    };
    verification: VerificationData;
    total_latency: number;
}
