import { CheckCircle2, Play, Check } from "lucide-react";

export function VerificationStage() {
  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
        <div className="bg-brand-green/10 text-brand-green text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wider">Stage 3</div>
        <div className="bg-gray-100 text-gray-500 text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider">POST /decompress</div>
      </div>
      
      <div className="p-6 flex flex-col flex-1">
        <h2 className="text-lg font-bold text-gray-900 mb-6 tracking-tight">Lossless recovery check</h2>
        
        {/* Output area */}
        <div className="mb-6">
          <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2">Decompressed Output</h3>
          <div className="bg-[#f0f2f5] border border-gray-200 rounded-xl p-3.5 font-mono text-xs text-gray-800 shadow-inner overflow-hidden relative">
            <div className="whitespace-nowrap overflow-x-auto pb-1 relative z-10">
              Invoice #4821 - Fox jumps over lazy dog - Total: $482.00
            </div>
            {/* Subtle glow / match highlight effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-brand-green/5 to-transparent pointer-events-none"></div>
          </div>
        </div>

        {/* Success Alert */}
        <div className="bg-[#f0fdf4] border border-brand-green/30 rounded-xl p-4 flex items-start mb-8 shadow-sm">
          <CheckCircle2 className="w-5 h-5 text-brand-green shrink-0 mt-0.5" />
          <div className="ml-3">
            <h4 className="text-sm font-bold text-brand-green mb-0.5">Exact match — lossless</h4>
            <p className="text-[11px] font-medium text-brand-green/70">Original and decompressed text are byte-identical</p>
          </div>
        </div>

        {/* Match Breakdown */}
        <div className="mb-8 flex-1">
          <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-4">Match Breakdown</h3>
          <ul className="space-y-4">
            <li className="flex justify-between items-center border-b border-gray-100 pb-3">
              <span className="text-xs font-semibold text-gray-600">Chars in</span>
              <span className="text-sm font-bold text-gray-900 font-mono">312</span>
            </li>
            <li className="flex justify-between items-center border-b border-gray-100 pb-3">
              <span className="text-xs font-semibold text-gray-600">Chars recovered</span>
              <span className="text-sm font-bold text-brand-green font-mono">312</span>
            </li>
            <li className="flex justify-between items-center">
              <span className="text-xs font-semibold text-gray-600">Byte match</span>
              <span className="text-sm font-bold text-brand-green font-mono">100%</span>
            </li>
          </ul>
        </div>

        {/* Controls */}
        <div className="mt-auto">
          <div className="flex space-x-3 mb-4">
            <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold py-2 rounded-lg transition-colors flex items-center justify-center">
              <Play className="w-3.5 h-3.5 mr-2" /> Decompress
            </button>
            <button className="flex-1 bg-brand-green hover:bg-green-600 text-white text-sm font-semibold py-2 rounded-lg transition-colors flex items-center justify-center shadow-md shadow-brand-green/20">
              <Check className="w-3.5 h-3.5 mr-2 stroke-[3px]" /> Verify match
            </button>
          </div>
          
          <div className="text-[11px] font-medium text-gray-400 flex items-center bg-gray-50 px-2 py-1 rounded w-max border border-gray-100 mt-2">
            <div className="w-1.5 h-1.5 bg-brand-green rounded-full mr-2"></div>
            Decompress: 12 ms - E2E total: 230 ms
          </div>
        </div>
      </div>
    </div>
  );
}
