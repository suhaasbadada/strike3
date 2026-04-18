import { PipelineStatus } from "../lib/types";

export function Sidebar({ status }: { status: PipelineStatus }) {
  const isRunningOCR = status !== 'idle';
  const isRunningCompress = status === 'compress' || status === 'verify' || status === 'complete';
  const isRunningVerify = status === 'verify' || status === 'complete';
  const isComplete = status === 'complete';

  const flowSteps = [
    { name: 'Image input', active: isRunningOCR },
    { name: 'Denoising', active: isRunningOCR },
    { name: 'CNN inference', active: isRunningOCR },
    { name: 'Huffman encode', active: isRunningCompress },
    { name: 'Decompress', active: isRunningVerify },
    { name: 'Verify match', active: isComplete }
  ];

  return (
    <aside className="w-[180px] flex-shrink-0 flex flex-col space-y-6 pr-4 border-r border-gray-100 overflow-y-auto pb-4">
      {/* Live Flow */}
      <div>
        <h3 className="text-[11px] font-bold tracking-widest text-gray-400 uppercase mb-4">Live Flow</h3>
        <ul className="space-y-3">
          {flowSteps.map((step, i) => (
            <li key={i} className="flex items-center text-sm font-medium text-gray-700 transition-opacity duration-300">
              <div className={`w-2 h-2 rounded-full mr-3 transition-colors duration-500 ${step.active ? 'bg-brand-green' : 'bg-gray-300'}`}></div>
              <span className={step.active ? 'opacity-100' : 'opacity-40'}>{step.name}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Last Run */}
      <div className={`bg-white rounded-xl border border-gray-100 p-4 shadow-sm relative overflow-hidden group transition-all duration-700 ${isComplete ? 'border-brand-blue/30 bg-brand-blue/5' : ''}`}>
        <div className="absolute top-0 right-0 p-3 opacity-5">
          <div className="text-4xl text-gray-900">⏱</div>
        </div>
        <h3 className="text-[11px] font-bold tracking-widest text-gray-400 uppercase mb-2">Last Run</h3>
        <div className="text-3xl font-bold text-gray-900 tracking-tight flex items-baseline">
          {isComplete ? '230' : '---'} <span className="text-sm text-gray-400 ml-1 font-semibold">ms</span>
        </div>
        <div className={`text-[10px] uppercase font-bold mt-3 leading-tight tracking-wide transition-opacity duration-500 ${isComplete ? 'text-gray-500 opacity-100' : 'text-gray-300 opacity-0'}`}>
          OCR 142<br />Huff 76<br />Verify 12
        </div>
      </div>

      {/* Service Health */}
      <div className={`transition-opacity duration-300 ${status !== 'idle' ? 'opacity-100' : 'opacity-50'}`}>
        <h3 className="text-[11px] font-bold tracking-widest text-gray-400 uppercase mb-4">Service Health</h3>
        <ul className="space-y-3">
          <li className="flex justify-between items-center text-xs bg-white py-1.5 px-2 rounded border border-gray-100 shadow-sm">
            <span className="text-gray-500 font-mono tracking-tighter">POST /ocr</span>
            <span className={isRunningOCR ? 'text-brand-green font-bold' : 'text-gray-400'}>{isRunningOCR ? '200' : '...'}</span>
          </li>
          <li className="flex justify-between items-center text-xs bg-white py-1.5 px-2 rounded border border-gray-100 shadow-sm">
            <span className="text-gray-500 font-mono tracking-tighter">POST /compress</span>
            <span className={isRunningCompress ? 'text-brand-green font-bold' : 'text-gray-400'}>{isRunningCompress ? '200' : '...'}</span>
          </li>
          <li className="flex justify-between items-center text-xs bg-white py-1.5 px-2 rounded border border-gray-100 shadow-sm">
            <span className="text-gray-500 font-mono tracking-tighter">POST /decompress</span>
            <span className={isRunningVerify ? 'text-brand-green font-bold' : 'text-gray-400'}>{isRunningVerify ? '200' : '...'}</span>
          </li>
        </ul>
      </div>
    </aside>
  );
}
