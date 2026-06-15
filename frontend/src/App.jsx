import React, { useState, useRef } from "react";
import { Upload, MessageSquare, Bot, User, Cpu, CheckCircle, AlertTriangle, FileText, Loader2, Sparkles, Terminal } from "lucide-react";

export default function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentTrace, setCurrentTrace] = useState([]);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setUploading(true);
    setUploadStatus("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setUploadStatus(`Successfully embedded ${data.chunks_ingested} semantic vectors.`);
      } else {
        setUploadStatus(`Ingestion Failed: ${data.detail || "Malformed layout"}`);
      }
    } catch (err) {
      setUploadStatus("Network Timeout: Connection to engine refused.");
    } finally {
      setUploading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setLoading(true);
    setCurrentTrace([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });
      const data = await response.json();

      if (response.ok) {
        setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
        setCurrentTrace(data.trace_timeline || []);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", text: `Runtime Error: ${data.detail || "Failed pipeline execution."}` }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", text: "Orchestration Error: Connection to graph gateway failed." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#080b11] text-slate-100 overflow-hidden antialiased selection:bg-blue-500/30">
      
      {/* SIDEBAR: Controls & Graph Execution Logs */}
      <aside className="w-85 border-r border-slate-800/60 bg-[#0c101b] flex flex-col justify-between shadow-2xl z-10 flex-shrink-0">
        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-8">
          
          {/* Brand Header */}
          <div className="flex items-center gap-3 pb-2">
            <div className="p-2 bg-gradient-to-br from-blue-600/20 to-indigo-600/20 rounded-xl border border-blue-500/30 shadow-lg shadow-blue-500/5">
              <Cpu className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-md font-bold tracking-wider uppercase text-slate-200">OmniQuery</h1>
              <p className="text-[10px] text-blue-400 font-mono tracking-widest uppercase">Self-Corrective RAG</p>
            </div>
          </div>

          {/* Section: File Ingestion */}
          <div className="space-y-3">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-widest block">Document Context</label>
            <div 
              onClick={() => !uploading && fileInputRef.current?.click()}
              className={`border border-dashed border-slate-700 hover:border-blue-500/80 rounded-xl p-5 text-center cursor-pointer transition-all bg-[#0e1424]/40 hover:bg-[#11192e]/40 group relative overflow-hidden ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
            >
              <Upload className="w-5 h-5 text-slate-400 group-hover:text-blue-400 mx-auto mb-2 transition-colors" />
              <p className="text-xs text-slate-300 font-medium group-hover:text-slate-200 transition-colors">Ingest Local Document</p>
              <p className="text-[10px] text-slate-500 mt-1">Supports TXT, MD, JSON</p>
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
                className="hidden" 
                accept=".txt,.md,.json,.csv"
              />
            </div>

            {file && (
              <div className="flex items-center gap-2.5 text-xs bg-[#12192c]/80 p-3 rounded-xl border border-slate-800 shadow-inner animate-fade-in">
                <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <span className="truncate font-mono text-slate-300 flex-1">{file.name}</span>
              </div>
            )}

            {uploading && (
              <div className="flex items-center gap-2.5 text-xs text-blue-400 bg-blue-950/20 border border-blue-900/30 p-3 rounded-xl">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span className="font-medium">Vectorizing chunk payloads...</span>
              </div>
            )}

            {uploadStatus && (
              <div className={`text-xs font-mono p-3 rounded-xl border ${
                uploadStatus.startsWith("Successfully") 
                  ? "text-emerald-400 bg-emerald-950/20 border-emerald-900/40" 
                  : "text-rose-400 bg-rose-950/20 border-rose-900/40"
              }`}>
                {uploadStatus}
              </div>
            )}
          </div>
        </div>

        {/* Section: Agent Timeline Execution Trace */}
        <div className="p-6 border-t border-slate-800/60 bg-[#090d16]">
          <div className="flex items-center gap-2 mb-4">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Graph Trace Monitor</h3>
          </div>
          <div className="space-y-2.5 max-h-56 overflow-y-auto custom-scrollbar pr-1">
            {currentTrace.length === 0 ? (
              <div className="text-[11px] text-slate-500 italic p-3 bg-[#0e1322]/40 rounded-xl border border-slate-800 text-center">
                Awaiting query instantiation to trace workflow nodes...
              </div>
            ) : (
              currentTrace.map((step, idx) => {
                const isFallback = step.toLowerCase().includes("fallback") || step.toLowerCase().includes("refactored");
                return (
                  <div key={idx} className={`flex items-start gap-2.5 text-xs p-3 rounded-xl border transition-all ${
                    isFallback 
                      ? "bg-amber-950/10 border-amber-900/30 text-amber-300" 
                      : "bg-[#0f1526] border-slate-800/80 text-slate-300"
                  }`}>
                    {isFallback ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    )}
                    <span className="font-mono text-[11px] leading-relaxed">{step}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </aside>

      {/* CORE FRAMEWORK: Conversational Dashboard Space */}
      <main className="flex-1 flex flex-col justify-between bg-[#080b11] relative">
        
        {/* Background Decorative Mesh Glows */}
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none"></div>

        {/* Empty State vs Chat Messages */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar z-10">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto animate-fade-in mt-20">
              <div className="p-4 bg-[#0e1424] border border-slate-800 rounded-2xl mb-5 shadow-xl">
                <Sparkles className="w-8 h-8 text-blue-500" />
              </div>
              <h3 className="text-lg font-semibold text-slate-200 mb-2">Agentic Knowledge Workspace</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Submit conversational queries mapped against your embedded documents. 
                If the internal vector search scoring fails confidence thresholds, the system will self-correct using external web search fallbacks.
              </p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`flex gap-4 p-6 rounded-2xl max-w-4xl border transition-all ${
                msg.role === "user" 
                  ? "bg-[#131c33] border-blue-500/20 ml-auto shadow-lg shadow-blue-950/10" 
                  : "bg-[#0d1220] border-slate-800/80 mr-auto shadow-md"
              }`}>
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 border shadow-md ${
                  msg.role === "user" 
                    ? "bg-gradient-to-br from-blue-600 to-indigo-600 border-blue-400/30" 
                    : "bg-[#141b2d] border-slate-700"
                }`}>
                  {msg.role === "user" ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-blue-400" />}
                </div>
                <div className="space-y-1 w-full overflow-hidden">
                  <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    {msg.role === "user" ? "Client Identity" : "OmniQuery Synthesizer"}
                  </span>
                  <div className="text-sm leading-relaxed text-slate-200 font-normal">
                    {msg.text}
                  </div>
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-4 p-6 bg-[#0d1220] border border-slate-800/80 rounded-2xl max-w-md mr-auto shadow-md animate-pulse">
              <div className="w-9 h-9 rounded-xl bg-[#141b2d] border border-slate-700 flex items-center justify-center flex-shrink-0">
                <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
              </div>
              <div className="space-y-2 flex-1">
                <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase block">Traversing Graph State...</span>
                <div className="flex space-x-1.5 items-center pt-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Bar Section */}
        <div className="p-6 border-t border-slate-800/50 bg-[#0a0e17]/80 backdrop-blur-lg z-10">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything... (e.g., 'What is OmniQuery?' or 'Who won the 2025 NBA finals?')"
              className="flex-1 bg-[#0e1322] border border-slate-800 focus:border-blue-500/60 focus:outline-none focus:ring-1 focus:ring-blue-500/30 rounded-xl px-5 py-4 text-sm transition-all text-slate-100 placeholder-slate-500 shadow-inner"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800/50 disabled:text-slate-600 text-white px-6 py-4 rounded-xl font-medium text-sm transition-all flex items-center gap-2 active:scale-98 shadow-lg shadow-blue-600/10 flex-shrink-0 font-sans"
            >
              <MessageSquare className="w-4 h-4" /> Execute
            </button>
          </form>
        </div>

      </main>
    </div>
  );
}