import { Upload, CheckCircle2, RotateCcw, Loader2 } from "lucide-react";
import { PipelineStatus } from "../../lib/types";

export function OCRStage({ status, onReset }: { status: PipelineStatus, onReset: () => void }) {
  const isCompact = status === 'compress' || status === 'verify' || status === 'complete';
  const isActive = status === 'ocr';

  return (
    <div className={`flex flex-col bg-white rounded-2xl border transition-all duration-500 overflow-hidden shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)] ${isActive ? 'border-brand-blue ring-4 ring-brand-blue/10 scale-[1.02]' : 'border-gray-100/50'} ${isCompact ? 'h-max' : 'h-full flex-1'}`}>
      
      <div className={`px-5 py-4 flex justify-between items-center transition-colors ${isCompact ? 'bg-gray-50' : 'border-b border-gray-100'}`}>
        <div className="bg-brand-blue/10 text-brand-blue text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wider">Stage 1</div>
        <div className="bg-gray-100 text-gray-500 text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider">POST /ocr</div>
      </div>
      
      <div className="p-6 flex flex-col flex-1">
        {!isCompact && <h2 className="text-lg font-bold text-gray-900 mb-6 tracking-tight">OCR microservice — CNN</h2>}
        
        {status === 'idle' && (
          <>
            <div className="border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 flex flex-col items-center justify-center py-10 px-6 mb-6 hover:border-brand-blue/50 hover:bg-brand-blue/5 transition-all duration-200 cursor-pointer group">
              <Upload className="w-7 h-7 text-gray-400 group-hover:text-brand-blue mb-3 transition-colors" />
              <p className="text-sm font-semibold text-gray-700">Drop scanned image or browse</p>
              <p className="text-[10px] text-gray-400 mt-1.5 uppercase font-bold tracking-widest">PNG · JPG · TIFF · MAX 10 MB</p>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-8">
              <button className="bg-brand-blue text-white text-xs font-semibold py-2.5 rounded-lg shadow-sm">Gaussian</button>
              <button className="bg-brand-purple/20 text-brand-purple text-xs font-semibold py-2.5 rounded-lg hover:bg-brand-purple/30 transition-colors">Salt & pepper</button>
              <button className="bg-gray-100 text-gray-600 hover:bg-gray-200 text-xs font-semibold py-2.5 rounded-lg transition-colors">None</button>
            </div>
          </>
        )}

        {status === 'ocr' && (
          <div className="flex flex-col items-center justify-center flex-1 py-12 space-y-6 animate-pulse">
            <Loader2 className="w-10 h-10 text-brand-blue animate-spin" />
            <div className="text-center">
              <p className="text-sm font-bold text-gray-900">Running CNN Inference</p>
              <p className="text-xs text-brand-blue font-medium mt-1">Applying Gaussian filter & extracting text...</p>
            </div>
            
            <div className="w-full max-w-xs mt-4">
              <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                <div className="bg-brand-blue h-1.5 rounded-full w-2/3 animate-pulse"></div>
              </div>
            </div>
          </div>
        )}

        {isCompact && (
          <div className="flex flex-col animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-brand-blue" />
                <span className="font-bold text-gray-900 text-sm">OCR Complete</span>
              </div>
              <button onClick={onReset} className="text-[10px] font-bold text-gray-500 hover:text-brand-blue bg-gray-100 hover:bg-brand-blue/10 px-2 py-1 rounded-md transition-colors flex items-center shadow-sm">
                <RotateCcw className="w-3 h-3 mr-1" /> Replace Upload
              </button>
            </div>
            
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-gray-200 rounded object-cover flex-shrink-0 border border-gray-300 flex items-center justify-center text-gray-400 text-[8px] font-bold">DOC</div>
              <div className="bg-[#f0f2f5] border border-gray-200 rounded-lg p-2 font-mono text-[10px] text-gray-600 shadow-inner flex-1 truncate">
                Invoice #4821 - Fox jumps over lazy dog...
              </div>
            </div>

            <div className="flex justify-between items-center text-[10px] border-t border-gray-100 pt-2.5">
              <div className="font-bold uppercase text-gray-500">Accuracy: <span className="text-brand-blue text-xs ml-1 tracking-tight">97.4%</span></div>
              <div className="bg-brand-blue/10 text-brand-blue px-2 py-0.5 rounded font-bold shadow-sm">Latency: 142ms</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
