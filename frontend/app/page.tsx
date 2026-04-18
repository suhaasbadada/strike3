"use client";

import { useState } from "react";
import { Header } from "../components/Header";
import { Sidebar } from "../components/Sidebar";
import { OCRStage } from "../components/stages/OCRStage";
import { CompressionStage } from "../components/stages/CompressionStage";
import { VerificationStage } from "../components/stages/VerificationStage";
import { PipelineStatus } from "../lib/types";

export default function Home() {
  const [status, setStatus] = useState<PipelineStatus>('idle');

  const runPipeline = () => {
    // If complete or idle, start the pipeline
    if (status === 'complete' || status === 'idle') {
      setStatus('ocr');
      
      // Mock OCR Inference Latency
      setTimeout(() => {
        setStatus('compress');
        
        // Mock Huffman Compression Latency
        setTimeout(() => {
          setStatus('verify');
          
          // Mock Verification Latency
          setTimeout(() => {
            setStatus('complete');
          }, 1800);
        }, 1800);
      }, 2500);
    }
  };

  const resetPipeline = () => {
    setStatus('idle');
  };

  return (
    <div className="h-screen overflow-hidden bg-background flex flex-col selection:bg-brand-blue/20">
      <Header status={status} onAction={status === 'complete' ? resetPipeline : runPipeline} />
      
      <main className="flex-1 w-full max-w-[1440px] mx-auto px-6 py-4 flex space-x-6 min-h-0">
        <Sidebar status={status} />
        
        {/* Main Stage Grid Container */}
        <div className="flex-1 flex flex-col space-y-4 min-h-0">
          
          {/* Core Pipeline UI */}
          <div className={`flex-1 w-full grid gap-4 transition-all duration-300 min-h-0 ${status === 'idle' ? 'grid-cols-1 max-w-3xl mx-auto' : 'grid-cols-1 lg:grid-cols-3 items-stretch'}`}>
            <OCRStage status={status} onReset={resetPipeline} />
            
            {status !== 'idle' && (
              <>
                <CompressionStage status={status} />
                <VerificationStage status={status} />
              </>
            )}
          </div>

          {/* Metric Cards Bottom Bar */}
          <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4 transition-all duration-1000 ${status === 'complete' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}>
            {/* Card 1 */}
            <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">OCR Accuracy (G)</h3>
              <div className="text-xl font-bold text-brand-blue leading-none mb-1 tracking-tight">97.4<span className="text-[11px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">Gaussian - &ge;95% req.</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-blue h-full rounded-full" style={{ width: '97.4%' }}></div>
              </div>
            </div>

            {/* Card 2 */}
            <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">OCR Accuracy (S&P)</h3>
              <div className="text-xl font-bold text-brand-purple leading-none mb-1 tracking-tight">95.1<span className="text-[11px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">Salt & pepper - &ge;95% req.</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-purple h-full rounded-full" style={{ width: '95.1%' }}></div>
              </div>
            </div>

            {/* Card 3 */}
            <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">Compression Ratio</h3>
              <div className="text-xl font-bold text-brand-purple leading-none mb-1 tracking-tight">3.21<span className="text-[11px] font-semibold text-gray-400 ml-0.5">x</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">vs raw text size</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-purple h-full rounded-full" style={{ width: '60%' }}></div>
              </div>
            </div>

            {/* Card 4 */}
            <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">Entropy</h3>
              <div className="text-xl font-bold text-orange-500 leading-none mb-1 tracking-tight">4.87</div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">bits / symbol</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-orange-500 h-full rounded-full" style={{ width: '70%' }}></div>
              </div>
            </div>

            {/* Card 5 */}
            <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">Encoding Efficiency</h3>
              <div className="text-xl font-bold text-brand-green leading-none mb-1 tracking-tight">96.2<span className="text-[11px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">Huffman quality</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-green h-full rounded-full" style={{ width: '96.2%' }}></div>
              </div>
            </div>

            {/* Card 6 */}
            <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">E2E Latency</h3>
              <div className="text-xl font-bold text-gray-900 leading-none mb-1 tracking-tight">230<span className="text-[11px] font-semibold text-gray-400 ml-1">ms</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">benchmarked</div>
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