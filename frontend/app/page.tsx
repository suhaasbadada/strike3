import { Header } from "../components/Header";
import { Sidebar } from "../components/Sidebar";
import { OCRStage } from "../components/stages/OCRStage";
import { CompressionStage } from "../components/stages/CompressionStage";
import { VerificationStage } from "../components/stages/VerificationStage";

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-brand-blue/20">
      <Header />
      
      <main className="flex-1 w-full max-w-[1440px] mx-auto px-8 py-8 flex space-x-6">
        <Sidebar />
        
        {/* Main Stage Grid Container */}
        <div className="flex-1 flex flex-col space-y-6">
          
          {/* Core Pipeline UI */}
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6">
            <OCRStage />
            <CompressionStage />
            <VerificationStage />
          </div>

          {/* Metric Cards Bottom Bar */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {/* Card 1 */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">OCR Accuracy (G)</h3>
              <div className="text-2xl font-bold text-brand-blue mb-1 tracking-tight">97.4<span className="text-[13px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[10px] font-medium text-gray-400 mb-4">Gaussian - &ge;95% req.</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-blue h-full rounded-full" style={{ width: '97.4%' }}></div>
              </div>
            </div>

            {/* Card 2 */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">OCR Accuracy (S&P)</h3>
              <div className="text-2xl font-bold text-brand-purple mb-1 tracking-tight">95.1<span className="text-[13px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[10px] font-medium text-gray-400 mb-4">Salt & pepper - &ge;95% req.</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-purple h-full rounded-full" style={{ width: '95.1%' }}></div>
              </div>
            </div>

            {/* Card 3 */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">Compression Ratio</h3>
              <div className="text-2xl font-bold text-brand-purple mb-1 tracking-tight">3.21<span className="text-[13px] font-semibold text-gray-400 ml-0.5">x</span></div>
              <div className="text-[10px] font-medium text-gray-400 mb-4">vs raw text size</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-purple h-full rounded-full" style={{ width: '60%' }}></div>
              </div>
            </div>

            {/* Card 4 */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">Entropy</h3>
              <div className="text-2xl font-bold text-orange-500 mb-1 tracking-tight">4.87</div>
              <div className="text-[10px] font-medium text-gray-400 mb-4">bits / symbol</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-orange-500 h-full rounded-full" style={{ width: '70%' }}></div>
              </div>
            </div>

            {/* Card 5 */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">Encoding Efficiency</h3>
              <div className="text-2xl font-bold text-brand-green mb-1 tracking-tight">96.2<span className="text-[13px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[10px] font-medium text-gray-400 mb-4">Huffman quality</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-green h-full rounded-full" style={{ width: '96.2%' }}></div>
              </div>
            </div>

            {/* Card 6 */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">E2E Latency</h3>
              <div className="text-2xl font-bold text-gray-900 mb-1 tracking-tight">230<span className="text-[13px] font-semibold text-gray-400 ml-1">ms</span></div>
              <div className="text-[10px] font-medium text-gray-400 mb-4">benchmarked</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-gray-400 h-full rounded-full" style={{ width: '40%' }}></div>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}