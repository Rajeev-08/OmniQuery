import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Upload, MessageSquare, Bot, User, Cpu, CheckCircle, AlertTriangle, FileText, Loader2, Trash2, Plus, CornerDownLeft, Link2, LogOut, Lock } from "lucide-react";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("omni_token") || "");
  const [username, setUsername] = useState(localStorage.getItem("omni_username") || "");
  const [authMode, setAuthMode] = useState("login"); // login | register
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authConfirmPassword, setAuthConfirmPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentTrace, setCurrentTrace] = useState([]);
  const fileInputRef = useRef(null);

  const headers = { "Authorization": `Bearer ${token}` };

  useEffect(() => {
    if (token) {
      fetchDocuments();
      fetchConversations();
    }
  }, [token]);

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthSuccess("");

    // Registration password equality assertion check
    if (authMode === "register" && authPassword !== authConfirmPassword) {
      setAuthError("Passwords do not match. Please verify your entries.");
      return;
    }

    const endpoint = authMode === "login" ? "login" : "register";
    try {
      const res = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: authEmail, password: authPassword })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Authentication Failed");

      if (authMode === "login") {
        localStorage.setItem("omni_token", data.access_token);
        localStorage.setItem("omni_username", data.username);
        setToken(data.access_token);
        setUsername(data.username);
        setAuthEmail("");
        setAuthPassword("");
      } else {
        setAuthMode("login");
        setAuthPassword("");
        setAuthConfirmPassword("");
        setAuthSuccess("Account created successfully! You can now sign in.");
      }
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken("");
    setUsername("");
    setMessages([]);
    setDocuments([]);
    setConversations([]);
    setActiveChatId(null);
    setCurrentTrace([]);
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/documents", { headers });
      if (res.status === 401) return handleLogout();
      const data = await res.json();
      setDocuments(data);
    } catch (err) { console.error(err); }
  };

  const fetchConversations = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/conversations", { headers });
      if (res.status === 401) return handleLogout();
      const data = await res.json();
      setConversations(data);
      if (data.length > 0 && !activeChatId) loadConversation(data[0].id);
    } catch (err) { console.error(err); }
  };

  const loadConversation = async (id) => {
    setActiveChatId(id);
    try {
      const res = await fetch(`http://127.0.0.1:8000/conversations/${id}/messages`, { headers });
      const data = await res.json();
      setMessages(data);
      const lastAssistantMessage = [...data].reverse().find(m => m.role === "OmniQuery Agent");
      setCurrentTrace(lastAssistantMessage ? lastAssistantMessage.trace_timeline : []);
    } catch (err) { console.error(err); }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await fetch("http://127.0.0.1:8000/upload", { method: "POST", headers, body: formData });
      fetchDocuments();
    } catch (err) { console.error(err); }
    finally { setUploading(false); }
  };

  const handleDeleteDocument = async (id) => {
    try {
      await fetch(`http://127.0.0.1:8000/documents/${id}`, { method: "DELETE", headers });
      fetchDocuments();
    } catch (err) { console.error(err); }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput("");
    setMessages(prev => [...prev, { role: username, content: userMessage }]);
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, conversation_id: activeChatId })
      });
      const data = await res.json();
      
      if (!activeChatId) {
        setActiveChatId(data.conversation_id);
        fetchConversations();
      }
      
      setMessages(prev => [...prev, { role: "OmniQuery Agent", content: data.answer, sources: data.sources }]);
      setCurrentTrace(data.trace_timeline || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  // --- RENDERING ROUTE: CLEAN SIGN IN / SIGN UP AUTH INTERFACE ---
  if (!token) {
    return (
      <div className="flex h-screen w-screen bg-[#060913] items-center justify-center font-sans px-4">
        <div className="w-full max-w-md bg-[#090e1a] border border-slate-900 rounded-2xl p-8 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="w-12 h-12 bg-blue-600/10 border border-blue-500/30 rounded-xl flex items-center justify-center mx-auto mb-2">
              <Lock className="w-5 h-5 text-blue-400" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-slate-200">
              {authMode === "login" ? "Sign In to OmniQuery" : "Create Your Account"}
            </h2>
            <p className="text-xs text-slate-500">
              {authMode === "login" ? "Welcome back! Enter your details below." : "Get started by creating a new profile."}
            </p>
          </div>

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            <div>
              <label className="text-[10px] font-bold tracking-wider uppercase text-slate-400 block mb-1.5">Email Address</label>
              <input 
                type="email" required value={authEmail} onChange={(e) => setAuthEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full bg-[#0c1324] border border-slate-800 text-xs px-4 py-3 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500 placeholder-slate-600 shadow-inner"
              />
            </div>
            <div>
              <label className="text-[10px] font-bold tracking-wider uppercase text-slate-400 block mb-1.5">Password</label>
              <input 
                type="password" required value={authPassword} onChange={(e) => setAuthPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-[#0c1324] border border-slate-800 text-xs px-4 py-3 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500 placeholder-slate-600 shadow-inner"
              />
            </div>
            
            {/* Conditional Input Layer: Renders ONLY if Register Mode is actively chosen */}
            {authMode === "register" && (
              <div className="animate-fade-in">
                <label className="text-[10px] font-bold tracking-wider uppercase text-slate-400 block mb-1.5">Confirm Password</label>
                <input 
                  type="password" required value={authConfirmPassword} onChange={(e) => setAuthConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[#0c1324] border border-slate-800 text-xs px-4 py-3 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500 placeholder-slate-600 shadow-inner"
                />
              </div>
            )}

            {authError && (
              <div className="text-[11px] font-mono p-3 bg-rose-950/20 border border-rose-900/40 rounded-xl text-rose-400">
                {authError}
              </div>
            )}

            {authSuccess && (
              <div className="text-[11px] font-mono p-3 bg-emerald-950/20 border border-emerald-900/40 rounded-xl text-emerald-400">
                {authSuccess}
              </div>
            )}

            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium p-3 rounded-xl text-xs transition-all shadow-lg shadow-blue-600/10 active:scale-98">
              {authMode === "login" ? "Sign In" : "Sign Up"}
            </button>
          </form>

          <div className="text-center pt-2">
            <button 
              onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setAuthError(""); setAuthSuccess(""); }}
              className="text-xs text-slate-400 hover:text-blue-400 transition-colors"
            >
              {authMode === "login" ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDERING ROUTE: APPLICATION MAIN DASHSPACE ---
  return (
    <div className="flex h-screen w-screen bg-[#060913] text-slate-100 overflow-hidden font-sans">
      
      {/* COLUMN 1: History Logging & Actions */}
      <div className="w-64 border-r border-slate-900 bg-[#090e1a] flex flex-col justify-between flex-shrink-0">
        <div className="p-4 flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-2 mb-6">
            <Cpu className="w-5 h-5 text-blue-500" />
            <span className="font-bold tracking-wider text-xs uppercase text-slate-400">Conversations</span>
          </div>

          <button 
            onClick={() => { setActiveChatId(null); setMessages([]); setCurrentTrace([]); }}
            className="w-full bg-blue-600/10 border border-blue-500/20 hover:bg-blue-600/20 text-blue-400 p-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 mb-4 transition-all"
          >
            <Plus className="w-4 h-4" /> New Session Loop
          </button>

          <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
            {conversations.map(c => (
              <div 
                key={c.id} 
                onClick={() => loadConversation(c.id)}
                className={`p-3 rounded-xl cursor-pointer transition-all text-xs truncate ${c.id === activeChatId ? 'bg-[#121a2e] border border-slate-800 text-blue-400 font-medium' : 'text-slate-400 hover:bg-[#0d1527]'}`}
              >
                {c.title}
              </div>
            ))}
          </div>
          
          <div className="pt-4 border-t border-slate-900 flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden mr-2">
              <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-xs font-bold text-blue-400 flex-shrink-0">
                {username[0]?.toUpperCase()}
              </div>
              <span className="text-xs font-medium text-slate-300 truncate font-mono">{username}</span>
            </div>
            <button onClick={handleLogout} className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-950/10 transition-all flex-shrink-0">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* COLUMN 2: Document Index Management */}
      <div className="w-72 border-r border-slate-900 bg-[#070b16] p-4 flex flex-col justify-between flex-shrink-0">
        <div className="flex flex-col h-full overflow-hidden">
          <div className="mb-6">
            <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Knowledge Ingestion</h2>
            <div 
              onClick={() => !uploading && fileInputRef.current?.click()}
              className="border border-dashed border-slate-800 hover:border-blue-500/40 rounded-xl p-4 text-center cursor-pointer bg-[#0b1122]/50 transition-all group"
            >
              <Upload className="w-4 h-4 text-slate-500 group-hover:text-blue-400 mx-auto mb-1" />
              <span className="text-xs text-slate-400 font-medium group-hover:text-slate-200">Upload Text Source</span>
              <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".txt,.md,.json,.pdf" />
            </div>
            {uploading && <div className="text-[11px] text-blue-400 mt-2 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin"/> Processing embeddings...</div>}
          </div>

          <div className="flex-1 flex flex-col overflow-hidden">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Active Database Sources ({documents.length})</h3>
            <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-0.5">
              {documents.map(d => (
                <div key={d.id} className="flex items-center justify-between p-2.5 bg-[#0b1122] border border-slate-900 rounded-xl text-xs group hover:border-slate-800 transition-all">
                  <div className="flex items-center gap-2 truncate flex-1 pr-2">
                    <FileText className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                    <span className="truncate text-slate-300 font-mono text-[11px]">{d.file_name}</span>
                  </div>
                  <button onClick={() => handleDeleteDocument(d.id)} className="text-slate-600 hover:text-rose-400 p-1 opacity-0 group-hover:opacity-100 transition-all">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-900 mt-4">
            <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-1.5"><Cpu className="w-3 h-3 text-indigo-400"/> Operational Node Trace</h4>
            <div className="space-y-1.5 max-h-40 overflow-y-auto custom-scrollbar">
              {currentTrace.map((step, i) => (
                <div key={i} className="text-[10px] font-mono p-2 bg-[#0a1020] border border-slate-900 rounded-lg text-slate-400 flex items-start gap-1.5">
                  <CheckCircle className="w-3 h-3 text-emerald-500 mt-0.5 flex-shrink-0" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* COLUMN 3: Conversational Workspace Board */}
      <div className="flex-1 flex flex-col justify-between bg-[#05070f] relative overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar">
          {messages.map((m, idx) => {
            const isMe = m.role !== "OmniQuery Agent";
            return (
              <div key={idx} className={`flex gap-3 p-5 rounded-2xl max-w-3xl border transition-all ${isMe ? 'bg-[#0f172a] border-blue-500/10 ml-auto' : 'bg-[#0a0f1d] border-slate-900 mr-auto'}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isMe ? 'bg-blue-600' : 'bg-indigo-600'}`}>
                  {isMe ? <User className="w-4 h-4"/> : <Bot className="w-4 h-4"/>}
                </div>
                <div className="space-y-2 flex-1 overflow-hidden">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block font-mono">
                    {isMe ? m.role : m.role}
                  </span>
                  <div className="text-xs leading-relaxed text-slate-200 prose prose-invert max-w-none prose-xs">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                  
                  {!isMe && m.sources && m.sources.length > 0 && (
                    <div className="pt-2 flex flex-wrap gap-1.5 items-center">
                      <span className="text-[10px] font-semibold text-slate-500 uppercase flex items-center gap-1 mr-1"><Link2 className="w-3 h-3"/> Sources Cited:</span>
                      {m.sources.map((src, sIdx) => (
                        <span key={sIdx} className="text-[10px] font-mono bg-[#111827] border border-slate-800 text-blue-400 px-2 py-0.5 rounded-md flex items-center gap-1 max-w-xs truncate">
                          <FileText className="w-2.5 h-2.5 text-slate-500 flex-shrink-0" />
                          <span className="truncate">{src}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {loading && <div className="text-xs text-slate-500 italic flex items-center gap-2 bg-[#0a0f1d] p-4 border border-slate-900 rounded-xl max-w-xs"><Loader2 className="w-3 h-3 animate-spin" /> Traversing pipeline graph execution loops...</div>}
        </div>

        <div className="p-4 border-t border-slate-900/60 bg-[#070a14]">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex gap-2 relative">
            <input 
              type="text" 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              placeholder="Query structural database session context..." 
              className="flex-1 bg-[#0a0f1e] border border-slate-800 focus:border-blue-500/50 focus:outline-none rounded-xl pl-4 pr-12 py-3 text-xs text-slate-200 shadow-inner"
            />
            <button type="submit" disabled={loading || !input.trim()} className="absolute right-2 top-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white p-1.5 rounded-lg transition-all">
              <CornerDownLeft className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

    </div>
  );
}