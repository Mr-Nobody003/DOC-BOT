"use client";

import { useCallback, useMemo, useState, useEffect, useRef } from "react";

type ChatProps = {
  apiBase: string;
};

type Citation = { pmid?: string; title?: string; url?: string };

export function MedicalChat({ apiBase }: ChatProps) {
  const [query, setQuery] = useState("");
  const [log, setLog] = useState<{type: string, content: string}[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [busy, setBusy] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const logEndRef = useRef<HTMLDivElement>(null);

  const url = useMemo(() => `${apiBase.replace(/\/$/, "")}/chat`, [apiBase]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  const run = useCallback(async () => {
    setBusy(true);
    setLog([]);
    setCitations([]);
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!res.ok || !res.body) {
      setLog([{type: "error", content: `HTTP ${res.status}`}]);
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
            setLog((l) => [...l, {type: "system", content: `Executing Node: ${ev.node}`}]);
            const patch = ev.patch ?? {};
            if (Array.isArray(patch.citations)) {
              setCitations(patch.citations as Citation[]);
            }
            if (typeof patch.final_response === "string") {
              setLog((l) => [...l, {type: "response", content: patch.final_response}]);
            }
            if (typeof patch.clarification_prompt === "string") {
              setLog((l) => [...l, {type: "clarification", content: patch.clarification_prompt}]);
            }
            if (Array.isArray(patch) && patch.length > 0 && typeof patch[0] === "string" && patch[0].startsWith("Interrupt")) {
              setLog((l) => [...l, {type: "interrupt", content: "Graph Execution Interrupted for User Clarification"}]);
            }
          }
        } catch {
          // ignore parsing errors on partial payloads
        }
      }
    }
    setBusy(false);
  }, [query, url]);

  const isDark = theme === "dark";
  const bgClass = isDark 
    ? "bg-slate-950 text-slate-100 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950" 
    : "bg-slate-50 text-slate-900 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-100 via-slate-50 to-slate-100";

  const panelClass = isDark ? "glass-panel" : "glass-panel-light";

  return (
    <div className={`min-h-screen ${bgClass} transition-colors duration-500`}>
      <div className="mx-auto flex max-w-5xl flex-col gap-8 p-6 lg:p-10 animate-fade-in">
        
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold tracking-tight gradient-text">DocBot Evidence</h1>
          </div>
          <button
            type="button"
            className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-200 hover:bg-slate-300 text-slate-700'}`}
            onClick={() => setTheme(isDark ? "light" : "dark")}
          >
            {isDark ? "☀️ Light" : "🌙 Dark"}
          </button>
        </header>

        <div className={`${panelClass} rounded-2xl p-6 transition-all`}>
          <textarea
            className={`min-h-[120px] w-full resize-none rounded-xl border-none bg-transparent p-2 text-lg focus:outline-none focus:ring-0 ${isDark ? 'placeholder:text-slate-600' : 'placeholder:text-slate-400'}`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a clinical evidence question..."
          />
          <div className="flex justify-end mt-4">
            <button
              type="button"
              disabled={busy || !query.trim()}
              onClick={run}
              className="rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-6 py-2.5 font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 disabled:pointer-events-none disabled:opacity-50"
            >
              {busy ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Processing...
                </span>
              ) : "Search Evidence"}
            </button>
          </div>
        </div>

        <section className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
              <span className="h-px flex-1 bg-slate-800"></span>
              Execution Trace
              <span className="h-px flex-1 bg-slate-800"></span>
            </h2>
            <div className={`${panelClass} rounded-2xl p-6 min-h-[400px] max-h-[600px] overflow-auto flex flex-col gap-4 relative`}>
              {log.length === 0 && !busy && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 opacity-50">
                  <svg className="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <p>Awaiting Query...</p>
                </div>
              )}
              {log.map((entry, i) => (
                <div key={i} className={`animate-slide-up rounded-xl p-4 border ${
                  entry.type === 'system' ? 'bg-slate-800/30 border-slate-700/50 text-slate-400 text-sm font-mono' :
                  entry.type === 'clarification' ? 'bg-amber-500/10 border-amber-500/30 text-amber-200' :
                  entry.type === 'interrupt' ? 'bg-red-500/10 border-red-500/30 text-red-300 text-sm' :
                  'bg-emerald-500/10 border-emerald-500/30 text-emerald-50 font-medium'
                }`}>
                  {entry.type === 'clarification' && <div className="text-xs font-bold uppercase tracking-wider text-amber-500 mb-1">Action Required</div>}
                  {entry.content}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>

          <div>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
              Citations
              <span className="h-px flex-1 bg-slate-800"></span>
            </h2>
            <ul className="space-y-4">
              {citations.map((c, i) => (
                <li key={`${c.pmid}-${i}`} className={`${panelClass} animate-slide-up rounded-xl p-5 hover:scale-[1.02] transition-transform`}>
                  <div className={`font-semibold mb-2 leading-tight ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                    {c.title || "Untitled Document"}
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <span className="inline-flex items-center rounded-md bg-slate-800 px-2 py-1 text-xs font-medium text-slate-400 ring-1 ring-inset ring-slate-700">
                      PMID {c.pmid}
                    </span>
                    {c.url && (
                      <a className="text-sm font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1" href={c.url} target="_blank" rel="noreferrer">
                        View 
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                      </a>
                    )}
                  </div>
                </li>
              ))}
              {!citations.length && (
                <li className={`text-sm text-center py-8 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
                  No citations retrieved yet.
                </li>
              )}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
