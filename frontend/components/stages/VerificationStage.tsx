import { CheckCircle2, Play, Check, Loader2 } from "lucide-react";
import { PipelineStatus } from "../../lib/types";
import { useCompressionSim } from "../../lib/useCompressionSim";

export function VerificationStage({ status }: { status: PipelineStatus }) {
  const isVisible = status === 'verify' || status === 'complete';
  const isActive = status === 'verify';

  // Bring in the mocked pipeline data for rendering the input
  const { metrics } = useCompressionSim(isVisible);

  return (
    <div className={`flex flex-col bg-white rounded-2xl border transition-all duration-700 shadow-sm overflow-hidden flex-1 ${isActive ? 'border-brand-green ring-4 ring-brand-green/10 scale-[1.02] z-10' : 'border-gray-200'} ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}>

      <div className={`px-5 py-4 border-b border-gray-100 flex justify-between items-center transition-colors ${isActive ? 'bg-brand-green/5' : ''}`}>
        <div className="bg-brand-green/10 text-brand-green text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wider">Stage 3</div>
        <div className="bg-gray-100 text-gray-500 text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider">POST /decompress</div>
      </div>

      <div className="p-6 flex flex-col flex-1 relative min-h-0">
        {isActive && (
          <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center animate-in fade-in duration-300">
            <Loader2 className="w-10 h-10 text-brand-green animate-spin mb-4 shadow-sm rounded-full" />
            <div className="bg-brand-green text-white text-[10px] font-bold px-3 py-1.5 rounded-full shadow-lg uppercase tracking-widest animate-pulse">
              Verifying Byte Match
            </div>
          </div>
        )}

        <h2 className="text-base font-bold text-gray-900 mb-4 tracking-tight">Lossless recovery check</h2>

        {/* Compressed Input */}
        <div className="mb-4">
          <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1.5 mt-1">Compressed Input Bitstream</h3>
          <div className="bg-[#f0f2f5] border border-gray-200 text-gray-400 rounded-lg p-2.5 font-mono text-[9px] break-all shadow-inner leading-relaxed overflow-y-auto max-h-[55px]">
            {metrics.compressedDataOutput}
          </div>
        </div>

        {/* Output area */}
        <div className="mb-5">
          <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1.5 mt-1">Decompressed Output</h3>
          <div className="bg-[#f0fdf4] border border-brand-green/20 rounded-xl p-3 font-mono text-[11px] text-gray-800 shadow-inner overflow-hidden relative">
            <div className="whitespace-nowrap overflow-x-auto relative z-10">
              Invoice #4821 - Fox jumps over lazy dog - Total: $482.00
            </div>
            <div className="absolute inset-0 bg-gradient-to-r from-brand-green/5 to-transparent pointer-events-none"></div>
          </div>
        </div>

        {/* Success Alert */}
        <div className="bg-white border-2 border-brand-green rounded-xl p-3 flex items-center mb-6 shadow-sm ring-4 ring-brand-green/10">
          <div className="bg-brand-green text-white rounded-full p-0.5 mr-3 shrink-0">
            <Check className="w-4 h-4 stroke-[3px]" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-brand-green mb-0.5">Exact match lossless</h4>
            <p className="text-[9px] font-medium text-brand-green/70">Original and decompressed text are byte-identical</p>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-auto pt-1">
          <div className="flex justify-end items-center">
            <div className="bg-brand-green/10 text-brand-green px-2 py-0.5 rounded text-[10px] font-bold shadow-sm">
              Decompress Latency: 12ms
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
