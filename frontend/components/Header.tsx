import { ChevronRight } from "lucide-react";
import { PipelineStatus } from "../lib/types";

export function Header({ status, onAction }: { status: PipelineStatus, onAction: () => void }) {
  let buttonText = "Run full pipeline";
  if (status !== 'idle' && status !== 'complete') buttonText = "Running...";
  if (status === 'complete') buttonText = "Run new pipeline";

  return (
    <header className="flex flex-col items-center pt-4 pb-3 bg-white/90 backdrop-blur-md sticky top-0 z-50 border-b border-gray-200 shrink-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-1 tracking-tight">Neural compression pipeline</h1>
      <p className="text-xs text-gray-500 mb-4 font-medium">
        Scanned image &rarr; CNN OCR &rarr; adaptive Huffman encoding &rarr; lossless recovery
      </p>

      {/* Step Indicator */}
      <div className="flex items-center space-x-2 bg-gray-50/80 border border-gray-200 rounded-full px-4 py-1.5 mb-5 shadow-sm backdrop-blur transition-all">
        <div className={`flex items-center space-x-2 transition-opacity ${status === 'idle' || status === 'ocr' ? 'opacity-100' : 'opacity-40'}`}>
          <div className="w-2 h-2 rounded-full bg-brand-blue"></div>
          <span className="text-sm font-semibold text-gray-800 tracking-wide">01 OCR</span>
        </div>
        <ChevronRight className="w-4 h-4 text-gray-400 mx-2" />
        <div className={`flex items-center space-x-2 transition-opacity ${status === 'compress' ? 'opacity-100' : 'opacity-40'}`}>
          <div className="w-2 h-2 rounded-full bg-brand-purple"></div>
          <span className="text-sm font-semibold text-gray-800 tracking-wide">02 Compress</span>
        </div>
        <ChevronRight className="w-4 h-4 text-gray-400 mx-2" />
        <div className={`flex items-center space-x-2 transition-opacity ${status === 'verify' || status === 'complete' ? 'opacity-100' : 'opacity-40'}`}>
          <div className="w-2 h-2 rounded-full bg-brand-green"></div>
          <span className="text-sm font-semibold text-gray-800 tracking-wide">03 Verify</span>
        </div>
      </div>

      {/* Selectors Bar */}
      <div className="w-full max-w-[1440px] px-8 flex items-center justify-between">
        <div className="flex space-x-8">
          <div className="flex items-center space-x-3">
            <span className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Framework</span>
            <div className="text-sm font-semibold bg-white border border-gray-200 rounded-md py-1.5 px-4 text-brand-blue shadow-sm">
              PyTorch
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Noise</span>
            <div className="text-sm font-semibold bg-white border border-gray-200 rounded-md py-1.5 px-4 text-brand-purple shadow-sm">
              Gaussian
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-[11px] font-bold text-gray-400 tracking-widest uppercase">Dataset</span>
            <div className="text-sm font-semibold bg-white border border-gray-200 rounded-md py-1.5 px-4 text-gray-800 shadow-sm">
              MNIST
            </div>
          </div>
        </div>
        
        <button 
          onClick={onAction}
          disabled={status !== 'idle' && status !== 'complete'}
          className={`text-white text-sm font-semibold py-2 px-5 rounded-full transition-all duration-200 flex items-center shadow-md hover:shadow-lg active:scale-95 ${status === 'complete' ? 'bg-gray-800 hover:bg-black' : 'bg-brand-blue hover:bg-blue-600'} disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100`}
        >
          {status !== 'idle' && status !== 'complete' && <div className="w-2 h-2 rounded-full bg-white mr-2 animate-pulse"></div>}
          {buttonText}
        </button>
      </div>
    </header>
  );
}
