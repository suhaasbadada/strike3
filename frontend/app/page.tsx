"use client";

import { useState } from "react";
import { Header } from "../components/Header";

import { OCRStage } from "../components/stages/OCRStage";
import { CompressionStage } from "../components/stages/CompressionStage";
import { VerificationStage } from "../components/stages/VerificationStage";
import { PipelineStatus, ProcessImageResponse } from "../lib/types";

export default function Home() {
  const [status, setStatus] = useState<PipelineStatus>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [apiData, setApiData] = useState<ProcessImageResponse | null>(null);

  const runPipeline = async () => {
    // If complete or idle, start the pipeline
    if ((status === 'complete' || status === 'idle') && selectedFile) {
      setStatus('ocr');
      
      try {
        const formData = new FormData();
        formData.append("file", selectedFile);
        
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "https://localhost:8000"}/process-image`, {
          method: "POST",
          body: formData
        });
        
        if (!res.ok) throw new Error("Pipeline backend failed");
        
        const data: ProcessImageResponse = await res.json();
        setApiData(data);

        setTimeout(() => {
          setStatus('compress');
          
          setTimeout(() => {
            setStatus('verify');
            
            setTimeout(() => {
              setStatus('complete');
            }, 1800);
          }, 1800);
        }, 1200); // 1.2s delay for OCR completion animation
        
      } catch (err) {
        console.error("API call failed:", err);
        setStatus('idle');
      }
    }
  };

  const resetPipeline = () => {
    setStatus('idle');
    setApiData(null);
    setSelectedFile(null);
  };

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-b from-[#ffffff] to-[#f4f5f7] flex flex-col selection:bg-brand-blue/20">
      <Header status={status} onAction={status === 'complete' ? resetPipeline : runPipeline} />
      
      <main className="flex-1 w-full max-w-[1440px] mx-auto px-6 py-4 flex space-x-6 min-h-0 relative">
        {/* Faint separation top line */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-200/50 to-transparent"></div>

        
        {/* Main Stage Grid Container */}
        <div className="flex-1 flex flex-col space-y-4 min-h-0">
          
          {/* Core Pipeline UI */}
          <div className={`flex-1 w-full grid gap-4 transition-all duration-300 min-h-0 ${status === 'idle' ? 'grid-cols-1 max-w-3xl mx-auto' : 'grid-cols-1 lg:grid-cols-3 items-stretch'}`}>
            <OCRStage 
              status={status} 
              onReset={resetPipeline} 
              selectedFile={selectedFile} 
              onFileSelect={setSelectedFile} 
              ocrText={apiData?.ocr_text} 
            />
            
            {status !== 'idle' && (
              <>
                <CompressionStage status={status} liveData={apiData?.compression || null} ocrText={apiData?.ocr_text} />
                <VerificationStage status={status} liveData={apiData || null} />
              </>
            )}
          </div>

          {/* Metric Cards Bottom Bar */}
          <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4 transition-all duration-1000 ${status === 'complete' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}>
            {/* Card 1 */}
            <div className="bg-white border border-gray-100/50 rounded-xl p-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.06)] transition-all duration-300 transform hover:-translate-y-0.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">OCR Accuracy (G)</h3>
              <div className="text-xl font-bold text-brand-blue leading-none mb-1 tracking-tight">97.4<span className="text-[11px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">Gaussian - &ge;95% req.</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-blue h-full rounded-full" style={{ width: '97.4%' }}></div>
              </div>
            </div>

            {/* Card 2 */}
            <div className="bg-white border border-gray-100/50 rounded-xl p-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.06)] transition-all duration-300 transform hover:-translate-y-0.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">OCR Accuracy (S&P)</h3>
              <div className="text-xl font-bold text-brand-purple leading-none mb-1 tracking-tight">95.1<span className="text-[11px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">Salt & pepper - &ge;95% req.</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-purple h-full rounded-full" style={{ width: '95.1%' }}></div>
              </div>
            </div>

            {/* Card 3 */}
            <div className="bg-white border border-gray-100/50 rounded-xl p-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.06)] transition-all duration-300 transform hover:-translate-y-0.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">Compression Ratio</h3>
              <div className="text-xl font-bold text-brand-purple leading-none mb-1 tracking-tight">{apiData?.compression?.compression_ratio || '0.00'}<span className="text-[11px] font-semibold text-gray-400 ml-0.5">x</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">vs raw text size</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-purple h-full rounded-full" style={{ width: `${Math.min(100, (apiData?.compression?.compression_ratio || 0) * 20)}%` }}></div>
              </div>
            </div>

            {/* Card 4 */}
            <div className="bg-white border border-gray-100/50 rounded-xl p-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.06)] transition-all duration-300 transform hover:-translate-y-0.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">Entropy</h3>
              <div className="text-xl font-bold text-orange-500 leading-none mb-1 tracking-tight">{apiData?.compression?.entropy || '0.00'}</div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">bits / symbol</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-orange-500 h-full rounded-full" style={{ width: '70%' }}></div>
              </div>
            </div>

            {/* Card 5 */}
            <div className="bg-white border border-gray-100/50 rounded-xl p-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.06)] transition-all duration-300 transform hover:-translate-y-0.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">Encoding Efficiency</h3>
              <div className="text-xl font-bold text-brand-green leading-none mb-1 tracking-tight">{apiData?.compression?.encoding_efficiency || '0.0'}<span className="text-[11px] font-semibold text-gray-400 ml-0.5">%</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">Huffman quality</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-brand-green h-full rounded-full" style={{ width: `${apiData?.compression?.encoding_efficiency || 0}%` }}></div>
              </div>
            </div>

            {/* Card 6 */}
            <div className="bg-white border border-gray-100/50 rounded-xl p-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_-4px_rgba(0,0,0,0.06)] transition-all duration-300 transform hover:-translate-y-0.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1">E2E Latency</h3>
              <div className="text-xl font-bold text-gray-900 leading-none mb-1 tracking-tight">{apiData?.total_latency || '0'}<span className="text-[11px] font-semibold text-gray-400 ml-1">ms</span></div>
              <div className="text-[9px] font-medium text-gray-400 mb-2.5">benchmarked</div>
              <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                <div className="bg-gray-400 h-full rounded-full" style={{ width: '100%' }}></div>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}