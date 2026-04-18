import { Upload } from "lucide-react";

export function OCRStage() {
  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
        <div className="bg-brand-blue/10 text-brand-blue text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wider">Stage 1</div>
        <div className="bg-gray-100 text-gray-500 text-[10px] font-mono px-2.5 py-1 rounded uppercase tracking-wider">POST /ocr</div>
      </div>
      
      <div className="p-6 flex flex-col flex-1">
        <h2 className="text-lg font-bold text-gray-900 mb-6 tracking-tight">OCR microservice — CNN</h2>
        
        {/* Upload Zone */}
        <div className="border-2 border-dashed border-gray-200 rounded-xl bg-gray-50 flex flex-col items-center justify-center py-10 px-6 mb-6 hover:border-brand-blue/50 hover:bg-brand-blue/5 transition-all duration-200 cursor-pointer group">
          <Upload className="w-7 h-7 text-gray-400 group-hover:text-brand-blue mb-3 transition-colors" />
          <p className="text-sm font-semibold text-gray-700">Drop scanned image or browse</p>
          <p className="text-[10px] text-gray-400 mt-1.5 uppercase font-bold tracking-widest">PNG · JPG · TIFF · MAX 10 MB</p>
        </div>

        {/* Noise profile buttons */}
        <div className="grid grid-cols-3 gap-2 mb-8">
          <button className="bg-brand-blue text-white text-xs font-semibold py-2.5 rounded-lg shadow-sm hover:bg-blue-600 transition-colors">Gaussian</button>
          <button className="bg-brand-purple text-white text-xs font-semibold py-2.5 rounded-lg shadow-sm hover:bg-purple-600 transition-colors">Salt & pepper</button>
          <button className="bg-gray-100 text-gray-600 hover:bg-gray-200 text-xs font-semibold py-2.5 rounded-lg transition-colors">None</button>
        </div>

        {/* Character Accuracy */}
        <div className="mb-8">
          <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-4">Character Accuracy By Profile</h3>
          
          <div className="mb-4">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-semibold text-gray-700 tracking-wide">Gaussian</span>
              <span className="text-xs font-bold text-brand-blue">97.4%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden relative">
              <div className="bg-brand-blue h-1.5 rounded-full absolute left-0 top-0 transition-all duration-1000 ease-out" style={{ width: '97.4%' }}></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-semibold text-gray-700 tracking-wide">Salt & pepper</span>
              <span className="text-xs font-bold text-brand-purple">95.1%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden relative">
              <div className="bg-brand-purple h-1.5 rounded-full absolute left-0 top-0 transition-all duration-1000 ease-out" style={{ width: '95.1%' }}></div>
            </div>
          </div>
        </div>

        {/* Extracted Text */}
        <div className="mt-auto">
          <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-3">Extracted Text</h3>
          <div className="bg-[#f0f2f5] border border-gray-200 rounded-xl p-4 font-mono text-xs text-gray-800 mb-4 shadow-inner overflow-x-auto">
            Invoice #4821 - Fox jumps over lazy dog - Total: $482.00
          </div>
          <div className="flex justify-between items-center text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
            <span>Characters extracted <strong className="text-gray-700 ml-1 font-bold">312</strong></span>
            <span>Model <strong className="text-gray-700 ml-1 font-bold">CNN (custom)</strong></span>
          </div>
          <div className="text-[11px] font-medium text-gray-400 mt-4 flex items-center bg-gray-50 px-2 py-1 rounded w-max border border-gray-100">
            <div className="w-1.5 h-1.5 bg-gray-300 rounded-full mr-2"></div>
            OCR latency: 142 ms
          </div>
        </div>
      </div>
    </div>
  );
}
