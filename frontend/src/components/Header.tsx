"use client";
import { useEffect, useState } from "react";
import { Settings, X, Orbit } from "lucide-react";
import { getConfig, type AppConfig } from "@/lib/api";

export default function Header() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [offline, setOffline] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  useEffect(() => { getConfig().then(setConfig).catch(() => setOffline(true)); }, []);
  const status = offline ? "Backend offline" : !config ? "Connecting..." : config.configured ? "Connected" : "Provider setup needed";
  return <header className="workspace-header">
    <div className="header-breadcrumb"><Orbit size={17} className="text-emerald-200/60" /><span>Workspace</span><span>/</span><strong>Personal AI</strong></div>
    <div className="flex items-center gap-3"><span className="connection-pill"><span className={`h-1.5 w-1.5 rounded-full ${config?.configured ? "bg-emerald-300" : "bg-amber-400"}`} />{config?.configured ? `${config.llm_provider} connected` : status}</span><button aria-label="Connection settings" onClick={() => setShowSettings(true)} className="settings-trigger"><Settings size={15} /></button></div>
    {showSettings && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6" onClick={() => setShowSettings(false)}>
      <section role="dialog" aria-modal="true" aria-label="Connection settings" className="w-full max-w-md rounded-2xl border border-white/15 bg-neutral-950 p-6" onClick={(event) => event.stopPropagation()}>
        <div className="flex justify-between"><h2 className="font-semibold">Connection settings</h2><button autoFocus aria-label="Close settings" onClick={() => setShowSettings(false)}><X size={18} /></button></div>
        <p className="mt-4 text-sm text-white/70">Status: {status}</p>
        <p className="mt-2 text-sm text-white/70">Provider: {config?.llm_provider || "Unavailable"}</p>
        {config && <p className="mt-2 text-sm text-white/70">Upload limit: {config.max_upload_bytes / 1024 / 1024} MB · PDF / TXT</p>}
        <p className="mt-4 text-sm text-white/50">Provider configuration is managed in the backend .env file. Restart the backend after changing it. API keys stay on the server.</p>
        <p className="mt-3 text-sm text-white/50">Chat history and extracted documents are stored locally. When using OpenAI or Groq, your question, recent history and relevant document excerpts are sent to that provider.</p>
      </section>
    </div>}
  </header>;
}
