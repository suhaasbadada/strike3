import { Header } from "../components/Header";
import { Sidebar } from "../components/Sidebar";

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

            <div className="bg-white/40 border border-dashed border-gray-300 rounded-2xl flex items-center justify-center p-8 text-gray-400 text-sm shadow-sm transition-all hover:bg-white/60">
              <span className="font-medium tracking-wide">Stage 1 OCR goes here</span>
            </div>

            <div className="bg-white/40 border border-dashed border-gray-300 rounded-2xl flex items-center justify-center p-8 text-gray-400 text-sm shadow-sm transition-all hover:bg-white/60">
              <span className="font-medium tracking-wide">Stage 2 Compression goes here</span>
            </div>

            <div className="bg-white/40 border border-dashed border-gray-300 rounded-2xl flex items-center justify-center p-8 text-gray-400 text-sm shadow-sm transition-all hover:bg-white/60">
              <span className="font-medium tracking-wide">Stage 3 Verification goes here</span>
            </div>

          </div>

          {/* Metric Cards Bottom Bar */}
          <div className="h-28 grid grid-cols-4 gap-6">
            <div className="bg-white/40 border border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 text-xs shadow-sm hover:bg-white/60" />
            <div className="bg-white/40 border border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 text-xs shadow-sm hover:bg-white/60" />
            <div className="bg-white/40 border border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 text-xs shadow-sm hover:bg-white/60" />
            <div className="bg-white/40 border border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-400 text-xs shadow-sm hover:bg-white/60" />
          </div>

        </div>
      </main>
    </div>
  );
}