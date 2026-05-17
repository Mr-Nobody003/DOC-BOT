"use client";

import { useCallback, useState, useRef, useEffect, ReactNode } from "react";

type Citation = { pmid?: string; title?: string; url?: string };

type TimelineEvent = {
  node: string;
  timestamp: number;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  timeline: TimelineEvent[];
  isStreaming: boolean;
};

type ChatProps = {
  apiBase: string;
};

// Component to render text with inline citations like [1]
const FormattedText = ({ text, citations, isDark }: { text: string; citations: Citation[]; isDark: boolean }) => {
  if (!text) return null;
  // Regex to match [1], [2], etc.
  const regex = /(\[\d+\])/g;
  const parts = text.split(regex);

  return (
    <div className={`prose max-w-none leading-relaxed ${isDark ? "prose-invert" : ""}`}>
      {parts.map((part, i) => {
        const match = part.match(/\[(\d+)\]/);
        if (match) {
          const idx = parseInt(match[1], 10) - 1;
          const cite = citations[idx];
          if (cite && cite.url) {
            return (
              <a
                key={i}
                href={cite.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center w-5 h-5 mx-0.5 text-xs font-bold rounded-full bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors no-underline align-super"
                title={cite.title || "Reference"}
              >
                {match[1]}
              </a>
            );
          } else {
            return <span key={i} className="text-gray-500 font-mono text-sm">{part}</span>;
          }
        }
        return <span key={i} className="whitespace-pre-wrap">{part}</span>;
      })}
    </div>
  );
};

// Component to render the vertical timeline
const VerticalTimeline = ({ events, isStreaming }: { events: TimelineEvent[]; isStreaming: boolean }) => {
  if (events.length === 0) return null;

  return (
    <div className="mb-6 pl-2">
      <div className="relative border-l-2 border-slate-200 dark:border-slate-700 ml-3 space-y-4 py-2">
        {events.map((ev, i) => {
          const isLast = i === events.length - 1;
          const isActive = isLast && isStreaming;
          
          return (
            <div key={i} className="relative flex items-start group">
              {/* Timeline dot */}
              <div className={`absolute -left-[9px] w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 ${isActive ? 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)] animate-pulse' : 'bg-emerald-500'}`}></div>
              
              <div className="pl-6">
                <div className={`font-semibold text-sm ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'}`}>
                  {ev.node.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-500">
                  {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
              </div>
            </div>
          );
        })}
        {/* Pending state dot if streaming but no event yet */}
        {isStreaming && events.length === 0 && (
           <div className="relative flex items-start group">
             <div className="absolute -left-[9px] w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 bg-slate-300 dark:bg-slate-600 animate-pulse"></div>
             <div className="pl-6 text-sm text-slate-500 italic">Starting...</div>
           </div>
        )}
      </div>
    </div>
  );
};

export function MedicalChat({ apiBase }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasWarmedBackendRef = useRef(false);

  const url = `${apiBase.replace(/\/$/, "")}/chat`;
  const warmupUrl = `${apiBase.replace(/\/$/, "")}/warmup`;
  const healthUrl = `${apiBase.replace(/\/$/, "")}/health`;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (hasWarmedBackendRef.current) return;
    hasWarmedBackendRef.current = true;

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);

    fetch(warmupUrl, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    }).catch(async () => {
      try {
        await fetch(healthUrl, {
          method: "GET",
          cache: "no-store",
          signal: controller.signal,
        });
      } catch {
        // Best-effort warm-up only; the first real chat request still handles errors.
      }
    }).finally(() => {
      window.clearTimeout(timeout);
    });

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [healthUrl, warmupUrl]);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || busy) return;

    const query = input.trim();
    setInput("");
    setBusy(true);

    const userMsg: Message = {
      id: Date.now().toString() + "_user",
      role: "user",
      content: query,
      citations: [],
      timeline: [],
      isStreaming: false
    };

    const astMsgId = Date.now().toString() + "_ast";
    const astMsg: Message = {
      id: astMsgId,
      role: "assistant",
      content: "",
      citations: [],
      timeline: [],
      isStreaming: true
    };

    setMessages((prev) => [...prev, userMsg, astMsg]);

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok || !res.body) {
        setMessages((prev) => prev.map(m => m.id === astMsgId ? { ...m, content: `HTTP Error ${res.status}`, isStreaming: false } : m));
        setBusy(false);
        return;
      }

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split(/\r?\n\r?\n/);
        buf = parts.pop() ?? "";
        
        for (const block of parts) {
          const line = block.split(/\r?\n/).find((l) => l.startsWith("data:"));
          if (!line) continue;
          const payload = line.replace(/^data:\s*/, "").trim();
          if (payload === "[DONE]" || payload === "{}") continue;
          
          try {
            const ev = JSON.parse(payload);
            if (ev.node) {
              setMessages((prev) => prev.map(m => {
                if (m.id !== astMsgId) return m;
                
                const newTimeline = [...m.timeline];
                if (!newTimeline.find(t => t.node === ev.node)) {
                  newTimeline.push({ node: ev.node, timestamp: Date.now() });
                }

                const patch = ev.patch ?? {};
                let newContent = m.content;
                if (typeof patch.final_response === "string") {
                  newContent = patch.final_response;
                }
                if (typeof patch.clarification_prompt === "string") {
                  newContent = patch.clarification_prompt;
                }

                return {
                  ...m,
                  timeline: newTimeline,
                  content: newContent,
                  citations: Array.isArray(patch.citations) ? patch.citations : m.citations
                };
              }));
            }
          } catch {
            // parsing error on partial payload
          }
        }
      }
      
      setMessages((prev) => prev.map(m => m.id === astMsgId ? { ...m, isStreaming: false } : m));
    } catch (e) {
      setMessages((prev) => prev.map(m => m.id === astMsgId ? { ...m, content: "Network error occurred.", isStreaming: false } : m));
    } finally {
      setBusy(false);
    }
  }, [input, busy, url]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isDark = theme === "dark";

  return (
    <div className={`flex flex-col h-screen ${isDark ? 'bg-slate-900 text-slate-100' : 'bg-slate-50 text-slate-900'} transition-colors duration-300 font-sans`}>
      {/* Header */}
      <header className={`flex-none flex items-center justify-between p-4 border-b ${isDark ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white/80'} backdrop-blur-md z-10 shadow-sm`}>
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold tracking-tight">DocBot</h1>
        </div>
        <button
          type="button"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-200 hover:bg-slate-300 text-slate-700'}`}
        >
          {isDark ? "☀️ Light" : "🌙 Dark"}
        </button>
      </header>

      {/* Chat Messages */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 w-full max-w-4xl mx-auto space-y-8 scroll-smooth">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full opacity-60">
            <div className="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-tr from-blue-500 to-cyan-400 p-0.5">
              <div className={`w-full h-full rounded-[14px] flex items-center justify-center ${isDark ? 'bg-slate-900' : 'bg-slate-50'}`}>
                <svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
            </div>
            <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
            <p className="text-center max-w-md text-sm">Ask any clinical question, and I will search the medical literature and Wikipedia for evidence.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-5 py-4 shadow-sm ${
                msg.role === "user" 
                  ? "bg-blue-600 text-white rounded-br-none" 
                  : isDark 
                    ? "bg-slate-800/80 text-slate-200 rounded-bl-none border border-slate-700/50" 
                    : "bg-white text-slate-800 rounded-bl-none border border-slate-200"
              }`}>
                {msg.role === "assistant" && (
                  <VerticalTimeline events={msg.timeline} isStreaming={msg.isStreaming} />
                )}
                
                {msg.content ? (
                  <FormattedText text={msg.content} citations={msg.citations} isDark={isDark} />
                ) : msg.isStreaming ? (
                  <div className="flex space-x-1 items-center h-6">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                ) : null}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} className="h-4" />
      </main>

      {/* Input Area */}
      <div className={`flex-none p-4 ${isDark ? 'bg-slate-900' : 'bg-slate-50'}`}>
        <div className="max-w-4xl mx-auto relative">
          <form onSubmit={handleSubmit} className={`relative flex items-end overflow-hidden rounded-2xl border shadow-sm transition-all focus-within:ring-2 focus-within:ring-blue-500/50 ${
            isDark ? 'bg-slate-800 border-slate-700 focus-within:border-blue-500' : 'bg-white border-slate-300 focus-within:border-blue-400'
          }`}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message DocBot..."
              className={`w-full max-h-48 min-h-[56px] resize-none bg-transparent py-4 pl-5 pr-14 text-base focus:outline-none ${
                isDark ? 'placeholder-slate-500 text-slate-100' : 'placeholder-slate-400 text-slate-900'
              }`}
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || busy}
              className={`absolute right-2 bottom-2 p-2 rounded-xl flex items-center justify-center transition-all ${
                input.trim() && !busy 
                  ? 'bg-blue-600 text-white hover:bg-blue-500 shadow-md shadow-blue-500/20' 
                  : isDark 
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed' 
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              }`}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            </button>
          </form>
          <div className="text-center mt-3 text-xs text-slate-500">
            DocBot can make mistakes. Verify clinical evidence independently.
          </div>
        </div>
      </div>
    </div>
  );
}
