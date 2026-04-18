// Force Turbopack invalidation
import { useState, useEffect } from "react";
import dummyDataRaw from "../dummy.json";
import { CompressionData, Step } from "./types";

export const dummyData = dummyDataRaw as unknown as CompressionData;

export function useCompressionSim(isActive: boolean) {
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    
    const totalSteps = dummyData.steps.length;

    useEffect(() => {
        if (!isActive) {
            setCurrentStepIndex(0);
            setIsComplete(false);
            return;
        }

        if (currentStepIndex >= totalSteps) {
            setIsComplete(true);
            return;
        }

        // Delay between steps
        const latencyMs = dummyData.latency * 10; // rough scale
        const timer = setTimeout(() => {
            setCurrentStepIndex(prev => prev + 1);
        }, latencyMs);

        return () => clearTimeout(timer);
    }, [isActive, currentStepIndex, totalSteps]);

    const currentStepIndexCapped = Math.min(currentStepIndex, totalSteps - 1);
    
    // Safety check just in case
    const treeData = dummyData.steps[currentStepIndexCapped]?.tree || { nodes: [], edges: [] };
    const processedRatio = ((currentStepIndexCapped + 1) / totalSteps) * 100;

    return {
        treeData,
        processedRatio,
        isComplete,
        allSteps: dummyData.steps,
        metrics: {
            ratio: dummyData.compression_ratio,
            entropy: dummyData.entropy,
            efficiency: dummyData.encoding_efficiency,
            originalSize: dummyData.original_size,
            compressedSize: dummyData.compressed_size,
            latency: dummyData.latency,
            compressedDataOutput: dummyData.compressed_data
        }
    };
}
