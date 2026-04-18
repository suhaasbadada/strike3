"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Download, Play, Loader2, Maximize2, X } from "lucide-react";
import { PipelineStatus } from "../../lib/types";

export function CompressionStage({ status }: { status: PipelineStatus }) {
  const isVisible = status === 'compress' || status === 'verify' || status === 'complete';
  const isActive = status === 'compress';

  const [isTreeExpanded, setIsTreeExpanded] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const modal = (isTreeExpanded && mounted) ? createPortal(
    <div className="fixed inset-0 z-[100] bg-gray-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 rounded-full bg-brand-purple"></div>
            <h2 className="text-sm font-bold text-gray-900 tracking-tight">Full Huffman Tree Map</h2>
          </div>
          <button onClick={() => setIsTreeExpanded(false)} className="text-gray-400 hover:text-gray-900 bg-white hover:bg-gray-100 p-1.5 rounded-lg border border-gray-200 transition-colors shadow-sm">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="bg-[#fcfcfd] p-8 flex items-center justify-center">
          <svg viewBox="0 0 240 150" className="w-full h-[350px]">
            <path d="M 120 20 L 70 70" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
            <path d="M 120 20 L 170 70" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
            <path d="M 70 70 L 40 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
            <path d="M 70 70 L 100 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
            <path d="M 170 70 L 140 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
            <path d="M 170 70 L 200 120" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />

            <circle cx="120" cy="20" r="16" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
            <text x="120" y="24.5" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#7e22ce">312</text>
            <circle cx="70" cy="70" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
            <text x="70" y="74" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">148</text>
            <circle cx="170" cy="70" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
            <text x="170" y="74" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">164</text>

            <circle cx="40" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5" />
            <text x="40" y="123.5" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">e</text>
            <circle cx="100" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5" />
            <text x="100" y="123.5" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">o</text>
            <circle cx="140" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5" />
            <text x="140" y="123.5" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">a</text>
            <circle cx="200" cy="120" r="12" fill="white" stroke="#e9d5ff" strokeWidth="1.5" />
            <text x="200" y="123.5" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#9333ea">t</text>
          </svg>
        </div>
      </div>
    </div>,
    document.body
  ) : null;

  return (
    <>
      <div className={`flex flex-col bg-white rounded-2xl border transition-all duration-700 shadow-sm overflow-hidden flex-1 ${isActive ? 'border-brand-purple ring-4 ring-brand-purple/10 scale-[1.02] z-10' : 'border-gray-200'} ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}>

        <div className={`px-4 py-3 border-b border-gray-100 flex justify-between items-center transition-colors ${isActive ? 'bg-brand-purple/5' : ''}`}>
          <div className="bg-brand-purple/10 text-brand-purple text-[9px] font-bold px-2 py-1 rounded uppercase tracking-wider">Stage 2</div>
          <div className="bg-gray-100 text-gray-500 text-[9px] font-mono px-2 py-1 rounded uppercase tracking-wider">POST /compress</div>
        </div>

        <div className="p-4 lg:p-5 flex flex-col flex-1 relative min-h-0">
          {isActive && (
            <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center animate-in fade-in duration-300">
              <Loader2 className="w-8 h-8 text-brand-purple animate-spin mb-3 shadow-sm rounded-full" />
              <div className="bg-brand-purple text-white text-[9px] font-bold px-3 py-1.5 rounded-full shadow-lg uppercase tracking-widest animate-pulse">
                Building Huffman Tree
              </div>
            </div>
          )}

          <h2 className="text-base font-bold text-gray-900 mb-3 tracking-tight">Huffman compression</h2>

          {/* Input area */}
          <div className="mb-3">
            <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1.5">Input (Piped from OCR)</h3>
            <div className="bg-[#f0f2f5] border border-gray-200 rounded-lg p-2.5 font-mono text-[10px] text-gray-800 shadow-inner overflow-x-auto whitespace-nowrap">
              Invoice #4821 - Fox jumps over lazy dog - Total: $482.00
            </div>
          </div>

          {/* Metrics Blocks */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="bg-[#fcf8ff] border border-brand-purple/10 rounded-xl p-2.5 text-center shadow-sm">
              <div className="text-lg font-bold text-brand-purple leading-none mb-1">3.21<span className="text-xs">x</span></div>
              <div className="text-[8px] font-bold text-brand-purple/50 tracking-widest uppercase">Ratio</div>
            </div>
            <div className="bg-[#fff7ed] border border-orange-500/10 rounded-xl p-2.5 text-center shadow-sm">
              <div className="text-lg font-bold text-orange-500 leading-none mb-1">4.87</div>
              <div className="text-[8px] font-bold text-orange-500/50 tracking-widest uppercase">Entropy</div>
            </div>
            <div className="bg-[#f0fdf4] border border-brand-green/10 rounded-xl p-2.5 text-center shadow-sm">
              <div className="text-lg font-bold text-brand-green leading-none mb-1">96.2<span className="text-xs">%</span></div>
              <div className="text-[8px] font-bold text-brand-green/50 tracking-widest uppercase">Efficiency</div>
            </div>
          </div>

          {/* Compression Bar */}
          <div className="mb-3">
            <div className="flex justify-between items-center text-[9px] text-gray-400 font-bold mb-1 uppercase tracking-wider">
              <span>Original 312 B</span>
              <span className="text-brand-purple">Compressed 97 B</span>
            </div>
            <div className="w-full bg-brand-purple/10 rounded-full h-1.5 overflow-hidden flex">
              <div className={`bg-brand-purple h-1.5 rounded-full transition-all duration-1000 ease-out shadow-sm`} style={{ width: isActive ? '10%' : '31.08%' }}></div>
            </div>
          </div>

          {/* Tree Preview */}
          <div className="mb-3 flex-1 flex flex-col min-h-[90px]">
            <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1.5">Huffman Tree Preview</h3>
            <div className="border border-gray-200 rounded-xl bg-[#fcfcfd] flex-1 flex flex-col items-center justify-center p-2 relative shadow-inner min-h-[70px]">
              <svg viewBox="0 0 240 90" className="w-full h-full max-h-[80px]">
                <path d="M 120 25 L 75 65" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
                <path d="M 120 25 L 165 65" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />

                <circle cx="120" cy="25" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
                <text x="120" y="29" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">312</text>
                <circle cx="75" cy="65" r="12" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
                <text x="75" y="69" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#7e22ce">148</text>
                <circle cx="165" cy="65" r="12" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
                <text x="165" y="69" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#7e22ce">164</text>
              </svg>
              <button
                onClick={() => setIsTreeExpanded(true)}
                className="absolute bottom-2 right-2 flex items-center bg-white border border-gray-200 shadow-sm rounded-md px-2 py-1 text-[9px] font-bold text-brand-purple hover:bg-brand-purple/5 transition-colors cursor-pointer z-10"
              >
                <Maximize2 className="w-2.5 h-2.5 mr-1" /> Expand Tree
              </button>
            </div>
          </div>

          {/* Extracted Text */}
          <div className="mt-auto pt-1">
            <div className="bg-[#f0f2f5] border border-gray-200 text-gray-500 rounded-lg p-2 font-mono text-[9px] break-all mb-3 shadow-inner leading-relaxed line-clamp-2">
              01101000 01100101 01101100 01100110...01101111 01110010 01101110 01101110
            </div>

            <div className="text-[9px] font-medium text-gray-500 flex items-center bg-gray-50 px-2 py-1 rounded w-max border border-gray-100">
              <div className="w-1.5 h-1.5 bg-gray-300 rounded-full mr-1.5"></div>
              Huffman latency: 76 ms - custom impl.
            </div>
          </div>
        </div>
      </div>
      {modal}
    </>
  );
}
