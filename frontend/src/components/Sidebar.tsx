"use client";
import { useState } from "react";
import { ArrowUpRight, MessageSquare, MoreHorizontal, Pencil, Plus, Search, Sparkles, Trash2, Orbit } from "lucide-react";
import type { Session } from "@/lib/api";
type Props = { sessions: Session[]; selectedSessionId: string; onSelectSession: (id: string) => void; onNewChat: () => void; onRenameSession: (id: string, title: string) => Promise<void>; onDeleteSession: (id: string) => Promise<void> };
export default function Sidebar({ sessions, selectedSessionId, onSelectSession, onNewChat, onRenameSession, onDeleteSession }: Props) {
  const [query, setQuery] = useState("");
  const [menu, setMenu] = useState<string | null>(null);
  const filtered = sessions.filter((session) => session.title.toLowerCase().includes(query.toLowerCase()));
  return <aside className="app-sidebar">
    <div className="brand"><span className="brand-symbol"><Orbit size={26} strokeWidth={1.4} /></span><div>personal<span className="brand-ai">ai</span><p>YOUR THOUGHTS. AMPLIFIED.</p></div></div>
    <button onClick={onNewChat} className="new-chat-button"><Plus size={17} /> New conversation <ArrowUpRight size={16} /></button>
    <label className="chat-search"><Search size={15} /><input aria-label="Search conversations" placeholder="Search conversations" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
    <div className="sidebar-section-label">YOUR CONVERSATIONS <span>{sessions.length.toString().padStart(2, "0")}</span></div>
    <nav aria-label="Conversations" className="session-list">{filtered.length === 0 && <p className="empty-chats">{query ? "No matching conversations." : "Good ideas start with a conversation."}</p>}{filtered.map((session) => <div key={session.session_id} className={`session-row ${selectedSessionId === session.session_id ? "selected" : ""}`}>
      <button className="session-select" onClick={() => onSelectSession(session.session_id)}><MessageSquare size={15} /><span>{session.title}</span></button>
      <button className="session-more" aria-label={`Options for ${session.title}`} aria-expanded={menu === session.session_id} onClick={() => setMenu(menu === session.session_id ? null : session.session_id)}><MoreHorizontal size={16} /></button>
      {menu === session.session_id && <div className="session-menu"><button onClick={async () => { const title = window.prompt("Rename conversation", session.title); if (title?.trim()) await onRenameSession(session.session_id, title.trim()); setMenu(null); }}><Pencil size={13} />Rename</button><button onClick={async () => { if (window.confirm(`Delete "${session.title}"?`)) await onDeleteSession(session.session_id); setMenu(null); }}><Trash2 size={13} />Delete</button></div>}
    </div>)}</nav>
    <div className="sidebar-bottom"><div className="workspace-note"><Sparkles size={18} /><strong>A mind of your own.</strong><p>Space to think bigger.<br />Tools to go further.</p><span>PERSONAL WORKSPACE <span className="tiny-star">✦</span></span></div>
    <div className="profile-row"><div className="profile-avatar">P</div><div><strong>My workspace</strong><p>Make yourself at home</p></div><span className="profile-dot" /></div></div>
  </aside>;
}
