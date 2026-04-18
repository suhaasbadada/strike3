export function Sidebar() {
  const flowSteps = [
    { name: 'Image input', active: true },
    { name: 'Denoising', active: true },
    { name: 'CNN inference', active: true },
    { name: 'Huffman encode', active: false },
    { name: 'Decompress', active: false },
    { name: 'Verify match', active: false }
  ];

  return (
    <aside className="w-[200px] flex-shrink-0 flex flex-col space-y-10 pr-6 border-r border-gray-100">
      {/* Live Flow */}
      <div>
        <h3 className="text-[11px] font-bold tracking-widest text-gray-400 uppercase mb-4">Live Flow</h3>
        <ul className="space-y-3">
          {flowSteps.map((step, i) => (
            <li key={i} className="flex items-center text-sm font-medium text-gray-700">
              <div className={`w-2 h-2 rounded-full mr-3 ${step.active ? 'bg-brand-green' : 'bg-gray-300'}`}></div>
              <span className={step.active ? 'opacity-100' : 'opacity-50'}>{step.name}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Last Run */}
      <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm relative overflow-hidden group hover:border-gray-200 transition-colors">
        <div className="absolute top-0 right-0 p-3 opacity-5">
          {/* Subtle decoration */}
          <div className="text-4xl text-gray-900">⏱</div>
        </div>
        <h3 className="text-[11px] font-bold tracking-widest text-gray-400 uppercase mb-2">Last Run</h3>
        <div className="text-3xl font-bold text-gray-900 tracking-tight flex items-baseline">
          230 <span className="text-sm text-gray-400 ml-1 font-semibold">ms</span>
        </div>
        <div className="text-[10px] uppercase font-bold text-gray-400 mt-3 leading-tight tracking-wide">
          OCR 142<br />Huff 76<br />Verify 12
        </div>
      </div>

      {/* Service Health */}
      <div>
        <h3 className="text-[11px] font-bold tracking-widest text-gray-400 uppercase mb-4">Service Health</h3>
        <ul className="space-y-3">
          <li className="flex justify-between items-center text-xs bg-white py-1.5 px-2 rounded border border-gray-100 shadow-sm">
            <span className="text-gray-500 font-mono tracking-tighter">POST /ocr</span>
            <span className="text-brand-green font-bold">200</span>
          </li>
          <li className="flex justify-between items-center text-xs bg-white py-1.5 px-2 rounded border border-gray-100 shadow-sm">
            <span className="text-gray-500 font-mono tracking-tighter">POST /compress</span>
            <span className="text-brand-green font-bold">200</span>
          </li>
          <li className="flex justify-between items-center text-xs bg-white py-1.5 px-2 rounded border border-gray-100 shadow-sm">
            <span className="text-gray-500 font-mono tracking-tighter">POST /decompress</span>
            <span className="text-brand-green font-bold">200</span>
          </li>
        </ul>
      </div>
    </aside>
  );
}
