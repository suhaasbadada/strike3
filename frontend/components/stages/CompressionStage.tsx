import { Download, Play } from "lucide-react";

export function CompressionStage() {
  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
        <div className="bg-brand-purple/10 text-brand-purple text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wider">Stage 2</div>
        <div className="bg-gray-100 text-gray-500 text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider">POST /compress</div>
      </div>
      
      <div className="p-6 flex flex-col flex-1">
        <h2 className="text-lg font-bold text-gray-900 mb-6 tracking-tight">Huffman compression</h2>
        
        {/* Input area */}
        <div className="mb-5">
          <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2">Input (Piped from OCR)</h3>
          <div className="bg-[#f0f2f5] border border-gray-200 rounded-xl p-3.5 font-mono text-xs text-gray-800 shadow-inner overflow-x-auto whitespace-nowrap">
            Invoice #4821 - Fox jumps over lazy dog - Total: $482.00
          </div>
        </div>

        {/* Metrics Blocks */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-[#fcf8ff] border border-brand-purple/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold text-brand-purple mb-0.5">3.21<span className="text-sm">x</span></div>
            <div className="text-[9px] font-bold text-brand-purple/50 tracking-widest uppercase">Ratio</div>
          </div>
          <div className="bg-[#fff7ed] border border-orange-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold text-orange-500 mb-0.5">4.87</div>
            <div className="text-[9px] font-bold text-orange-500/50 tracking-widest uppercase">Entropy</div>
          </div>
          <div className="bg-[#f0fdf4] border border-brand-green/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold text-brand-green mb-0.5">96.2<span className="text-sm">%</span></div>
            <div className="text-[9px] font-bold text-brand-green/50 tracking-widest uppercase">Efficiency</div>
          </div>
        </div>

        {/* Compression Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center text-[10px] text-gray-400 font-semibold mb-1.5 uppercase tracking-wider">
            <span>Original 312 B</span>
            <span className="text-brand-purple font-bold">Compressed 97 B</span>
          </div>
          <div className="w-full bg-brand-purple/10 rounded-full h-2 overflow-hidden flex">
            <div className="bg-brand-purple h-2 rounded-full" style={{ width: '31.08%' }}></div>
          </div>
        </div>

        {/* Tree Preview */}
        <div className="mb-5 flex-1">
          <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2">Huffman Tree Preview</h3>
          <div className="border border-gray-200 rounded-xl bg-[#fcfcfd] flex items-center justify-center p-3 w-full max-h-[160px] overflow-hidden">
            <svg width="220" height="120" viewBox="0 0 240 140" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
              <path d="M 120 20 L 70 70" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <path d="M 120 20 L 170 70" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <path d="M 70 70 L 40 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <path d="M 70 70 L 100 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <path d="M 170 70 L 140 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <path d="M 170 70 L 200 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              
              <circle cx="120" cy="20" r="16" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5"/>
              <text x="120" y="24" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#7e22ce">312</text>
              
              <circle cx="70" cy="70" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5"/>
              <text x="70" y="74" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">148</text>
              
              <circle cx="170" cy="70" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5"/>
              <text x="170" y="74" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">164</text>
              
              <circle cx="40" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5"/>
              <text x="40" y="124" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">e</text>
              
              <circle cx="100" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5"/>
              <text x="100" y="124" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">o</text>
              
              <circle cx="140" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5"/>
              <text x="140" y="124" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">a</text>
              
              <circle cx="200" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5"/>
              <text x="200" y="124" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">t</text>
            </svg>
          </div>
        </div>

        {/* Extracted Text */}
        <div className="mt-auto">
          <div className="bg-[#f0f2f5] border border-gray-200 text-gray-500 rounded-lg p-2.5 font-mono text-[10px] break-all mb-4 shadow-inner">
            01101000 01100101 01101100 01100110...01101111 01110010 01101110 01101110
          </div>
          
          <div className="flex space-x-3 mb-4">
            <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold py-2 rounded-lg transition-colors flex items-center justify-center">
              <Play className="w-3.5 h-3.5 mr-2" /> Compress
            </button>
            <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold py-2 rounded-lg transition-colors flex items-center justify-center">
              <Download className="w-3.5 h-3.5 mr-2" /> Download .huff
            </button>
          </div>
          
          <div className="text-[11px] font-medium text-gray-400 flex items-center bg-gray-50 px-2 py-1 rounded w-max border border-gray-100">
            <div className="w-1.5 h-1.5 bg-gray-300 rounded-full mr-2"></div>
            Huffman latency: 76 ms - custom impl.
          </div>
        </div>
      </div>
    </div>
  );
}
