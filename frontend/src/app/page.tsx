"use client";

import { useCallback, useEffect, useState } from "react";
import ChatArea from "@/components/ChatArea";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import { deleteSession, getSessions, renameSession, type Session } from "@/lib/api";

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [error, setError] = useState("");
  const loadSessions = useCallback(async () => {
    try { setSessions(await getSessions()); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load chats."); }
  }, []);

  useEffect(() => {
    let active = true;
    void getSessions().then((items) => {
      if (active) setSessions(items);
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "Unable to load chats.");
    }).finally(() => {
      if (!active) return;
      const saved = localStorage.getItem("personal-ai-session");
      const id = saved && /^[A-Za-z0-9_-]{1,100}$/.test(saved) ? saved : `chat-${crypto.randomUUID()}`;
      setSelectedSessionId(id);
      localStorage.setItem("personal-ai-session", id);
    });
    return () => { active = false; };
  }, []);

  function selectSession(id: string) { setSelectedSessionId(id); localStorage.setItem("personal-ai-session", id); }
  function newChat() { selectSession(`chat-${crypto.randomUUID()}`); }

  async function handleRenameSession(id: string, title: string) {
    try { await renameSession(id, title); await loadSessions(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to rename chat."); }
  }
  async function handleDeleteSession(id: string) {
    try { await deleteSession(id); if (selectedSessionId === id) newChat(); await loadSessions(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to delete chat."); }
  }

  return <main className="app-shell relative h-dvh overflow-hidden text-white">
    <div className="app-frame relative z-10 flex h-full overflow-hidden">
      <Sidebar sessions={sessions} selectedSessionId={selectedSessionId} onSelectSession={selectSession}
        onNewChat={newChat} onRenameSession={handleRenameSession} onDeleteSession={handleDeleteSession} />
      <section className="main-workspace flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <Header />
        <div className="mobile-navigation flex gap-2 border-b border-white/10 px-4 py-2 md:hidden">
          <select aria-label="Select chat" value={selectedSessionId} onChange={(event) => selectSession(event.target.value)}
            className="min-w-0 flex-1 rounded-lg bg-neutral-900 p-2 text-sm">
            {!sessions.some((item) => item.session_id === selectedSessionId) && <option value={selectedSessionId}>New chat</option>}
            {sessions.map((item) => <option key={item.session_id} value={item.session_id}>{item.title}</option>)}
          </select>
          <button onClick={newChat} className="rounded-lg bg-white/10 px-3 text-sm">New chat</button>
        </div>
        {error && <div role="alert" className="flex items-center justify-between bg-red-500/10 px-4 py-2 text-sm text-red-200">
          {error}<button onClick={loadSessions} className="ml-3 underline">Retry</button>
        </div>}
        {selectedSessionId && <ChatArea key={selectedSessionId} sessionId={selectedSessionId} onSessionCreated={loadSessions} />}
      </section>
    </div>
  </main>;
}
