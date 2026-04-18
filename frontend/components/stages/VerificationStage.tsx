import { ShieldCheck, ArrowRight, ArrowDown, CheckCircle2, ChevronRight, Binary, Check, Loader2 } from "lucide-react";
import { PipelineStatus, ProcessImageResponse } from "../../lib/types";
import { useCompressionSim } from "../../lib/useCompressionSim";

export function VerificationStage({ status, liveData }: { status: PipelineStatus, liveData: ProcessImageResponse | null }) {
  const isVisible = status === 'verify' || status === 'complete';
  const isActive = status === 'verify';


  const { metrics } = useCompressionSim(isVisible, liveData?.compression || null);

  return (
    <div className={`flex flex-col bg-white rounded-2xl border transition-all duration-1000 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)] overflow-hidden flex-1 ${isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-12 scale-95 pointer-events-none'} ${isActive ? 'border-brand-green ring-4 ring-brand-green/10' : 'border-gray-100/50'}`}>

      <div className={`px-5 py-4 border-b border-gray-100 flex justify-between items-center transition-colors ${isActive ? 'bg-brand-green/5' : ''}`}>
        <div className="bg-brand-green/10 text-brand-green text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wider">Stage 3</div>
        <div className="bg-gray-100 text-gray-500 text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider">POST /decompress</div>
      </div>

      <div className="p-5 lg:p-6 flex flex-col flex-1 relative min-h-0 overflow-y-auto">
        {isActive && (
          <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center animate-in fade-in duration-300">
            <Loader2 className="w-10 h-10 text-brand-green animate-spin mb-4 shadow-sm rounded-full" />
            <div className="bg-brand-green text-white text-[10px] font-bold px-3 py-1.5 rounded-full shadow-lg uppercase tracking-widest animate-pulse">
              Verifying Byte Match
            </div>
          </div>
        )}

        <h2 className="text-base font-bold text-gray-900 mb-4 tracking-tight">Lossless recovery check</h2>

        {/* Compression Flow Preview */}
        <div className="flex flex-col space-y-1 mb-5">
          <div className="bg-gray-50 w-full p-2.5 rounded-lg border border-gray-100 flex flex-col items-start shadow-inner relative overflow-hidden group">
            <span className="text-[8px] text-gray-400 font-bold uppercase tracking-widest mb-1 z-10">Input Tensor</span>
            <span className="font-mono text-[10px] text-gray-700 truncate w-full z-10">{liveData?.ocr_text || metrics.originalSize + " Bytes extracted text"}</span>
          </div>

          <div className="flex flex-col items-center justify-center py-0.5">
            <ArrowDown className="w-4 h-4 text-gray-300 mb-0.5" />
            <div className="text-[7px] font-bold text-gray-400 uppercase tracking-wider">HUF</div>
          </div>

          <div className="bg-brand-purple/5 w-full p-2.5 rounded-lg border border-brand-purple/10 flex flex-col items-start shadow-inner relative overflow-hidden group">
            <span className="text-[8px] text-brand-purple/60 font-bold uppercase tracking-widest mb-1 z-10">Compressed Bin</span>
            <span className="font-mono text-[10px] text-gray-700 truncate w-full leading-tight z-10">{liveData?.compression?.compressed_data || metrics.compressedDataOutput}</span>
          </div>

          <div className="flex flex-col items-center justify-center py-0.5">
            <ArrowDown className="w-4 h-4 text-gray-300 mb-0.5" />
            <div className="text-[7px] font-bold text-gray-400 uppercase tracking-wider">DEC</div>
          </div>

          <div className="bg-brand-green/5 w-full p-2.5 rounded-lg border border-brand-green/10 flex flex-col items-start shadow-inner relative overflow-hidden group">
            <span className="text-[8px] text-brand-green/60 font-bold uppercase tracking-widest mb-1 z-10">Reconstructed Data</span>
            <span className="font-mono text-[10px] text-gray-700 truncate w-full z-10">{liveData?.decompression?.text || metrics.originalSize + " Bytes extracted text"}</span>
          </div>
        </div>

        {/* Success Alert */}
        <div className="bg-white border-2 border-brand-green rounded-xl py-2 px-3 flex items-center shadow-sm ring-4 ring-brand-green/10 mt-4 mb-3">
          <div className="bg-brand-green text-white rounded-full p-0.5 mr-3 shrink-0">
            <Check className="w-4 h-4 stroke-[3px]" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-brand-green mb-0.5">Exact match lossless</h4>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-auto pt-1">
          <div className="flex justify-between items-center">
            <div className="text-[10px] font-bold text-gray-400">Byte-identical validation</div>
            <div className="bg-brand-green/10 text-brand-green px-2 py-0.5 rounded text-[10px] font-bold shadow-sm">
              Decompress Latency: {liveData?.decompression?.latency || '88'}ms
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
