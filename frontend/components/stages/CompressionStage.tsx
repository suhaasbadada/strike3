"use client";

import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Loader2, Maximize2, X, Play, Pause, ChevronDown, ChevronUp } from "lucide-react";
import { CompressionData, PipelineStatus, TreeEdge, TreeNode } from "../../lib/types";
import { useCompressionSim } from "../../lib/useCompressionSim";
import { calculateTreeLayout } from "../../lib/treeLayout";

export function CompressionStage({ status, liveData, ocrText }: { status: PipelineStatus, liveData: CompressionData | null, ocrText?: string }) {
  const isVisible = status === 'compress' || status === 'verify' || status === 'complete';
  const isActive = status === 'compress';

  const [isTreeExpanded, setIsTreeExpanded] = useState(false);
  const [mounted, setMounted] = useState(false);
  const layoutCache = useRef<{ [key: string]: { nodes: TreeNode[], edges: TreeEdge[] } }>({});

  const { treeData, processedRatio, metrics, allSteps } = useCompressionSim(isVisible, liveData);
  const treeLayout = calculateTreeLayout(treeData.nodes, treeData.edges);

  const [modalEvoIndex, setModalEvoIndex] = useState(0);
  const [isPlayingEvo, setIsPlayingEvo] = useState(false);
  const [isInputExpanded, setIsInputExpanded] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isTreeExpanded && allSteps) {
      setModalEvoIndex(allSteps.length > 0 ? allSteps.length - 1 : 0);
      setIsPlayingEvo(false);
    }
  }, [isTreeExpanded, allSteps]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlayingEvo && isTreeExpanded && allSteps && allSteps.length > 0) {
      timer = setInterval(() => {
        setModalEvoIndex(prev => {
          if (prev >= allSteps.length - 1) {
            setIsPlayingEvo(false);
            return prev;
          }
          return prev + 1;
        });
      }, 500);
    }
    return () => clearInterval(timer);
  }, [isPlayingEvo, isTreeExpanded, allSteps]);

  const modalTreeData = (isTreeExpanded && allSteps && allSteps[modalEvoIndex])
    ? allSteps[modalEvoIndex].tree
    : treeData;

  const modalTreeLayout = calculateTreeLayout(modalTreeData.nodes, modalTreeData.edges);

  const renderTreeSVG = (layout: ReturnType<typeof calculateTreeLayout>, expanded: boolean) => {
    if (layout.nodes.length === 0) return null;

    if (!expanded) {
      const root = layout.nodes.find(n => n.depth === 0) || layout.nodes[0];
      const rootEdges = layout.edges.filter(e => e.from.toString() === root.id.toString());
      const leftEdge = rootEdges.find(e => e.label === '0');
      const rightEdge = rootEdges.find(e => e.label === '1');
      const leftChild = leftEdge ? layout.nodes.find(n => n.id.toString() === leftEdge.to.toString()) : null;
      const rightChild = rightEdge ? layout.nodes.find(n => n.id.toString() === rightEdge.to.toString()) : null;

      return (
        <svg viewBox="0 0 200 90" className="w-full h-full max-h-[70px]">
          {leftChild && (
            <g>
              <path d="M 100 20 L 50 65" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <text x="70" y="40" textAnchor="middle" fontSize="9" fontStyle="italic" fill="#d8b4fe">0</text>
              <circle cx="50" cy="65" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
              <text x="50" y="68" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">{leftChild.weight}</text>
            </g>
          )}
          {rightChild && (
            <g>
              <path d="M 100 20 L 150 65" stroke="#e9d5ff" strokeWidth="2.5" fill="none" />
              <text x="130" y="40" textAnchor="middle" fontSize="9" fontStyle="italic" fill="#d8b4fe">1</text>
              <circle cx="150" cy="65" r="14" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
              <text x="150" y="68" textAnchor="middle" fontSize="10" fontWeight="bold" fill="#7e22ce">{rightChild.weight}</text>
            </g>
          )}
          <g>
            <circle cx="100" cy="20" r="16" fill="#f3e8ff" stroke="#d8b4fe" strokeWidth="1.5" />
            <text x="100" y="24" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#7e22ce">{root.weight}</text>
          </g>
        </svg>
      );
    }

    const scaleFactor = 1;
    const strokeWidthAttr = 1.5;

    return (
      <svg viewBox={`0 0 ${layout.width} ${layout.height}`} className="w-full max-h-[450px]" style={{ transform: `scale(${scaleFactor})`, transformOrigin: 'center top' }}>
        {layout.edges.map((e, index) => (
          <g key={`e-${index}`}>
            <path
              d={`M ${e.x1} ${e.y1} L ${e.x2} ${e.y2}`}
              stroke="#e9d5ff"
              strokeWidth="2.5"
              fill="none"
            />
            <text
              x={(e.x1 + e.x2) / 2}
              y={(e.y1 + e.y2) / 2 - 5}
              textAnchor="middle"
              fontSize="8"
              fill="#d8b4fe"
            >
              {e.label}
            </text>
          </g>
        ))}

        {layout.nodes.map(n => {
          const isLeaf = n.symbol !== null;
          const hasChildren = layout.edges.some(e => e.from.toString() === n.id.toString());
          const trueLeaf = isLeaf && !hasChildren;

          return (
            <g key={`n-${n.id}`}>
              <circle
                cx={n.x}
                cy={n.y}
                r={trueLeaf ? "12" : "14"}
                fill={trueLeaf ? "white" : "#f3e8ff"}
                stroke={trueLeaf ? "#e9d5ff" : "#d8b4fe"}
                strokeWidth={strokeWidthAttr}
              />
              <text
                x={n.x}
                y={n.y + 3}
                textAnchor="middle"
                fontSize={trueLeaf ? "10" : "9"}
                fontWeight="bold"
                fill={trueLeaf ? "#9333ea" : "#7e22ce"}
              >
                {trueLeaf ? (n.symbol === 'NYT' ? 'NYT' : String.fromCharCode(Number(n.symbol))) : n.weight}
              </text>
            </g>
          );
        })}
      </svg>
    );
  };

  const modal = (isTreeExpanded && mounted) ? createPortal(
    <div className="fixed inset-0 z-[100] bg-gray-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col" style={{ maxHeight: 'calc(100vh - 2rem)' }}>
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50 relative z-10 shadow-sm shrink-0">
          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 rounded-full bg-brand-purple"></div>
            <h2 className="text-sm font-bold text-gray-900 tracking-tight">Live Huffman Tree</h2>
          </div>
          <button onClick={() => setIsTreeExpanded(false)} className="text-gray-400 hover:text-gray-900 bg-white hover:bg-gray-100 p-1.5 rounded-lg border border-gray-200 transition-colors shadow-sm">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Timeline Evolution UI */}
        <div className="bg-white px-6 py-4 border-b border-gray-100 flex items-center space-x-5 shrink-0 z-10 shadow-sm">
          <button
            onClick={() => {
              if (modalEvoIndex >= (allSteps?.length || 1) - 1) setModalEvoIndex(0);
              setIsPlayingEvo(!isPlayingEvo);
            }}
            className="flex items-center justify-center w-9 h-9 rounded-full bg-brand-purple text-white shadow-md hover:bg-purple-700 hover:shadow-lg transition-all shrink-0 active:scale-95"
          >
            {isPlayingEvo ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>
          <div className="flex-1 flex flex-col relative w-full pt-1">
            <div className="flex justify-between w-full absolute -top-3 text-[9px] font-bold text-gray-400 uppercase tracking-widest pointer-events-none">
              <span>Start</span>
              <span className="translate-x-[-50%] ml-[25%]">25%</span>
              <span className="translate-x-[-50%] ml-[25%]">50%</span>
              <span className="translate-x-[-50%] ml-[25%]">75%</span>
              <span>Final</span>
            </div>
            <input
              type="range"
              min={0}
              max={(allSteps?.length || 1) - 1}
              value={modalEvoIndex}
              onChange={(e) => {
                setIsPlayingEvo(false);
                setModalEvoIndex(parseInt(e.target.value));
              }}
              className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer mt-1 relative z-10 
                      [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 
                      [&::-webkit-slider-thumb]:bg-brand-purple [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-md
                      focus:outline-none focus:ring-2 focus:ring-brand-purple/20"
              style={{ background: `linear-gradient(to right, #9333ea ${Math.round((modalEvoIndex / Math.max(1, (allSteps?.length || 1) - 1)) * 100)}%, #e5e7eb ${Math.round((modalEvoIndex / Math.max(1, (allSteps?.length || 1) - 1)) * 100)}%)` }}
            />
          </div>
          <div className="w-14 text-right bg-brand-purple/5 px-2 py-1 rounded text-xs font-bold text-brand-purple tabular-nums shrink-0 border border-brand-purple/10">
            {Math.round((modalEvoIndex / Math.max(1, (allSteps?.length || 1) - 1)) * 100)}%
          </div>
        </div>

        <div className="bg-[#f8f9fc] p-6 lg:p-8 flex-1 overflow-auto flex items-start justify-center min-h-[300px]">
          {renderTreeSVG(modalTreeLayout, true)}
        </div>
      </div>
    </div>,
    document.body
  ) : null;

  return (
    <>
      <div className={`flex flex-col bg-white rounded-2xl border transition-all duration-700 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)] overflow-hidden flex-1 ${isActive ? 'border-brand-purple ring-4 ring-brand-purple/10 scale-[1.02] z-10' : 'border-gray-100/50'} ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8 pointer-events-none'}`}>

        <div className={`px-4 py-3 border-b border-gray-100 flex justify-between items-center transition-colors ${isActive ? 'bg-brand-purple/5' : ''}`}>
          <div className="bg-brand-purple/10 text-brand-purple text-[9px] font-bold px-2 py-1 rounded uppercase tracking-wider">Stage 2</div>
          <div className="bg-gray-100 text-gray-500 text-[9px] font-mono px-2 py-1 rounded uppercase tracking-wider">POST /compress</div>
        </div>

        <div className="p-4 lg:p-5 flex flex-col flex-1 relative min-h-0">
          {isActive && (
            <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center animate-in fade-in duration-300 pointer-events-none">
              <Loader2 className="w-8 h-8 text-brand-purple animate-spin mb-3 shadow-sm rounded-full" />
              <div className="bg-brand-purple text-white text-[9px] font-bold px-3 py-1.5 rounded-full shadow-lg uppercase tracking-widest animate-pulse">
                Building Huffman Tree
              </div>
            </div>
          )}

          <h2 className="text-base font-bold text-gray-900 mb-3 tracking-tight">Huffman compression</h2>

          {/* Input area */}
          <div className="mb-3">
            <div className="flex justify-between items-center mb-1.5">
              <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase">Input (Piped from OCR)</h3>
              {ocrText && ocrText.length > 50 && (
                <button 
                  onClick={() => setIsInputExpanded(!isInputExpanded)}
                  className="flex items-center text-[10px] font-bold text-brand-purple hover:text-purple-700 bg-brand-purple/5 hover:bg-brand-purple/10 px-2 py-0.5 rounded transition-colors"
                >
                  {isInputExpanded ? (
                    <>Collapse <ChevronUp className="w-3 h-3 ml-1" /></>
                  ) : (
                    <>Expand <ChevronDown className="w-3 h-3 ml-1" /></>
                  )}
                </button>
              )}
            </div>
            <div className={`bg-[#f0f2f5] border border-gray-200 rounded-lg p-2.5 font-mono text-[10px] text-gray-800 shadow-inner overflow-x-auto transition-all duration-300 ${isInputExpanded ? 'whitespace-pre-wrap max-h-[250px] overflow-y-auto' : 'whitespace-nowrap'}`}>
              {ocrText || "Awaiting extracted text from OCR Pipeline..."}
            </div>
          </div>

          {/* Metrics Blocks */}
          <div className="grid grid-cols-3 gap-2 mb-3 lg:mb-3">
            <div className="bg-[#fcf8ff] border border-brand-purple/10 rounded-lg py-1.5 px-2 text-center shadow-sm">
              <div className="text-base font-bold text-brand-purple leading-none mb-0.5">{metrics.ratio}<span className="text-[10px] ml-0.5">x</span></div>
              <div className="text-[7px] font-bold text-brand-purple/50 tracking-widest uppercase">Ratio</div>
            </div>
            <div className="bg-[#fff7ed] border border-orange-500/10 rounded-lg py-1.5 px-2 text-center shadow-sm">
              <div className="text-base font-bold text-orange-500 leading-none mb-0.5">{metrics.entropy}</div>
              <div className="text-[7px] font-bold text-orange-500/50 tracking-widest uppercase">Entropy</div>
            </div>
            <div className="bg-[#f0fdf4] border border-brand-green/10 rounded-lg py-1.5 px-2 text-center shadow-sm">
              <div className="text-base font-bold text-brand-green leading-none mb-0.5">{metrics.efficiency}<span className="text-[10px] ml-0.5">%</span></div>
              <div className="text-[7px] font-bold text-brand-green/50 tracking-widest uppercase">Efficiency</div>
            </div>
          </div>

          {/* Compression Bar */}
          <div className="mb-4 lg:mb-5 relative">
            <div className="flex justify-between items-end text-[9px] text-gray-800 font-bold mb-1.5 uppercase tracking-widest px-0.5">
              <span>Original &middot; {metrics.originalSize} B</span>
              <span className="text-gray-800">Compressed &middot; {metrics.compressedSize} B</span>
            </div>
            
            {isVisible && processedRatio > 0 && (
              <div 
                className="absolute text-[8px] text-teal-600 tracking-wider font-bold whitespace-nowrap pointer-events-none transition-all duration-300 ease-linear"
                style={{ 
                  left: `calc(${(processedRatio / 100) * (metrics.compressedSize / metrics.originalSize) * 100}% - 4px)`, 
                  transform: 'translateX(-100%)',
                  bottom: '12px'
                }}
              >
                - {Math.round((1 - metrics.compressedSize / metrics.originalSize) * 100)}% REDUCTION
              </div>
            )}

            <div className="w-full bg-gray-200 rounded-sm h-[5px] overflow-visible flex relative z-10">
              <div 
                className="bg-[#1a1a1a] h-full flex items-center relative transition-all duration-300 ease-linear" 
                style={{ width: `${(processedRatio / 100) * (metrics.compressedSize / metrics.originalSize) * 100}%` }}
              >
                <div className="absolute right-[-1px] w-[2px] h-[10px] bg-teal-600 z-20"></div>
              </div>
            </div>
          </div>

          {/* Tree Preview */}
          <div className="mb-2 flex-1 flex flex-col min-h-[90px] relative">
            <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1.5">Live Huffman Tree Output</h3>
            <div className="border border-gray-200 rounded-xl bg-[#fcfcfd] flex-1 flex flex-col items-center justify-center p-2 relative shadow-inner min-h-[70px] overflow-hidden">
              {renderTreeSVG(treeLayout, false)}
              <button
                onClick={() => setIsTreeExpanded(true)}
                className="absolute bottom-1 right-1 flex items-center bg-white border border-gray-200 shadow-sm rounded-md px-1.5 py-0.5 text-[8px] font-bold text-brand-purple hover:bg-brand-purple/5 transition-colors cursor-pointer z-10"
              >
                <Maximize2 className="w-2.5 h-2.5 mr-1" /> Expand Tree
              </button>
            </div>
          </div>

          {/* Extracted Text */}
          <div className="mt-auto">
            <h3 className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-1 mt-1">Compressed Bitstream</h3>
            <div className="bg-[#f0f2f5] border border-gray-200 text-gray-600 rounded-lg p-2 font-mono text-[10px] break-all shadow-inner leading-relaxed overflow-y-auto max-h-[50px]">
              {metrics.compressedDataOutput}
            </div>

            <div className="flex justify-end items-center mt-1.5 pt-1 border-t border-transparent">
              <div className="bg-brand-purple/10 text-brand-purple px-2 py-0.5 rounded text-[10px] font-bold shadow-sm">
                Compress Latency: {metrics.latency}ms
              </div>
            </div>
          </div>
        </div>
      </div>
      {modal}
    </>
  );
}
