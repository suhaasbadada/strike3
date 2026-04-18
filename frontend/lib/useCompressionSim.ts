import { useState, useEffect } from "react";
import { CompressionData } from "./types";

export function useCompressionSim(isActive: boolean, liveData: CompressionData | null) {
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [isComplete, setIsComplete] = useState(false);

    const totalSteps = liveData?.steps?.length || 1;

    useEffect(() => {
        if (!isActive || !liveData) {
            setCurrentStepIndex(0);
            setIsComplete(false);
            return;
        }

        if (currentStepIndex >= totalSteps) {
            setIsComplete(true);
            return;
        }

        const latencyMs = Math.max(10, Math.min(50, 1000 / totalSteps));
        const timer = setTimeout(() => {
            setCurrentStepIndex(prev => prev + 1);
        }, latencyMs);

        return () => clearTimeout(timer);
    }, [isActive, currentStepIndex, totalSteps, liveData]);

    if (!liveData) {
        return {
            treeData: { nodes: [], edges: [] },
            processedRatio: 0,
            isComplete: false,
            metrics: {
                ratio: 0,
                entropy: 0,
                efficiency: 0,
                originalSize: 0,
                compressedSize: 0,
                latency: 0,
            }
        };
    }

    const currentStepIndexCapped = Math.min(currentStepIndex, totalSteps - 1);

    const treeData = liveData.steps[currentStepIndexCapped]?.tree || { nodes: [], edges: [] };
    const processedRatio = ((currentStepIndexCapped + 1) / totalSteps) * 100;

    return {
        treeData,
        processedRatio,
        isComplete,
        allSteps: liveData.steps,
        metrics: {
            ratio: liveData.compression_ratio,
            entropy: liveData.entropy,
            efficiency: liveData.encoding_efficiency,
            originalSize: liveData.original_size,
            compressedSize: liveData.compressed_size,
            latency: liveData.latency,
            compressedDataOutput: liveData.compressed_data
        }
    };
}
