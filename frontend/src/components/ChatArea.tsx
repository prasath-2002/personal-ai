"use client";

import { useEffect, useRef, useState } from "react";
import { Download, FileText, Trash2, X } from "lucide-react";
import ChatInput from "@/components/ChatInput";
import ChatWindow from "@/components/ChatWindow";
import WelcomePanel from "@/components/WelcomePanel";
import { clearHistory, deleteDocument, getDocuments, getHistory, streamChat, uploadFile,
  type DocumentItem, type Message } from "@/lib/api";

type ChatAreaProps = { sessionId: string; onSessionCreated: () => Promise<void> };

export default function ChatArea({ sessionId, onSessionCreated }: ChatAreaProps) {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState("");
  const [lastUserMessage, setLastUserMessage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<DocumentItem[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);
  const controllerRef = useRef<AbortController | null>(null);
  const busyRef = useRef(false);

  useEffect(() => {
    let active = true;
    Promise.all([getHistory(sessionId), getDocuments(sessionId)])
      .then(([history, documents]) => {
        if (active) { setMessages(history); setUploadedFiles(documents); }
      })
      .catch((cause) => { if (active) setError(`Unable to load chat: ${cause.message}`); })
      .finally(() => { if (active) setInitializing(false); });
    return () => { active = false; controllerRef.current?.abort(); };
  }, [sessionId]);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container && messages.length > 0 && shouldAutoScrollRef.current) container.scrollTop = container.scrollHeight;
  }, [messages]);

  async function handleFileSelect(file: File) {
    if (busyRef.current) return;
    busyRef.current = true;
    setUploading(true); setError("");
    try {
      await uploadFile(sessionId, file);
      setUploadedFiles(await getDocuments(sessionId));
      await onSessionCreated();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Upload failed."); }
    finally { setUploading(false); busyRef.current = false; }
  }

  async function handleRemoveFile(documentId: number) {
    if (busyRef.current) return;
    busyRef.current = true;
    setUploading(true);
    try {
      await deleteDocument(documentId);
      setUploadedFiles((files) => files.filter((file) => file.document_id !== documentId));
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to remove document."); }
    finally { setUploading(false); busyRef.current = false; }
  }

  async function sendMessage(message: string) {
    if (busyRef.current || initializing) return;
    busyRef.current = true;
    setLoading(true); setError(""); setLastUserMessage(message);
    shouldAutoScrollRef.current = true;
    const controller = new AbortController();
    controllerRef.current = controller;
    try {
      // Reconcile with persisted history before retries, including ambiguous network failures.
      const history = await getHistory(sessionId);
      if (controller.signal.aborted) return;
      setMessages([...history, { role: "user", content: message }, { role: "assistant", content: "" }]);
      const response = await streamChat(sessionId, message, controller.signal);
      if (!response.body) throw new Error("Streaming response unavailable.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let completed = false;
      try {
        while (true) {
          const { done, value } = await reader.read();
          buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
          let boundary: number;
          while ((boundary = buffer.indexOf("\n\n")) >= 0) {
            const frame = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            if (!frame.startsWith("data: ")) continue;
            const event = JSON.parse(frame.slice(6));
            if (event.type === "error") throw new Error(event.message);
            if (event.type === "done") completed = true;
            if (event.type === "delta") {
              setMessages((previous) => previous.map((item, index) => index === previous.length - 1
                ? { ...item, content: item.content + event.content } : item));
            }
          }
          if (done) break;
        }
        if (!completed) throw new Error("Connection interrupted before the response finished.");
      } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
      setLastUserMessage("");
      await onSessionCreated();
    } catch (cause) {
      if (!controller.signal.aborted) {
        setError(cause instanceof Error ? cause.message : "Response failed. Please retry.");
        // Failed provider turns are not stored. Show the canonical conversation again.
        try { setMessages(await getHistory(sessionId)); } catch { /* Preserve visible content if offline. */ }
      }
    } finally { setLoading(false); busyRef.current = false; }
  }

  async function handleClear() {
    if (busyRef.current || !window.confirm("Clear this chat's messages? Attachments will remain.")) return;
    busyRef.current = true; setLoading(true);
    try { await clearHistory(sessionId); setMessages([]); setLastUserMessage(""); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to clear chat."); }
    finally { setLoading(false); busyRef.current = false; }
  }

  function exportChat() {
    const text = messages.map((item) => `## ${item.role === "user" ? "You" : "Personal AI"}\n\n${item.content}`).join("\n\n---\n\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = `${sessionId}.md`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
    <div className="chat-toolbar"><span className="chat-toolbar-label">✦ &nbsp; YOUR PERSONAL SPACE</span><div className="flex gap-3">
      <button onClick={exportChat} disabled={!messages.length || loading} className="flex items-center gap-1 disabled:opacity-30"><Download size={14} /> Export chat</button>
      <button onClick={handleClear} disabled={!messages.length || loading || uploading} className="flex items-center gap-1 disabled:opacity-30"><Trash2 size={14} /> Clear messages</button>
    </div></div>
    <div ref={scrollContainerRef} onScroll={() => {
      const element = scrollContainerRef.current;
      if (element) shouldAutoScrollRef.current = element.scrollHeight - element.scrollTop - element.clientHeight < 120;
    }} className={`min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-6 md:px-8 ${messages.length === 0 ? "welcome-scroll" : ""}`}>
      <div className="mx-auto w-full max-w-4xl">
        {initializing ? <p className="text-white/50">Loading chat...</p> : messages.length === 0 && !loading
          ? <WelcomePanel onSuggest={setDraft} /> : <ChatWindow messages={messages} loading={loading} />}
        {error && <div role="alert" className="mt-6 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
          <p>{error}</p>
          {lastUserMessage && <button onClick={() => sendMessage(lastUserMessage)} disabled={loading || uploading}
            className="mt-3 rounded-xl bg-white/10 px-4 py-2 disabled:opacity-40">Retry last message</button>}
        </div>}
      </div>
    </div>
    <div className="composer-dock">
      <div className="mx-auto w-full max-w-4xl">
        {uploadedFiles.length > 0 && <div className="mb-3 flex max-h-28 flex-wrap gap-2 overflow-y-auto">
          {uploadedFiles.map((file) => <div key={file.document_id} className="flex max-w-64 items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm">
            <FileText size={16} className="shrink-0 text-violet-300" /><span className="truncate">{file.filename}</span>
            <button aria-label={`Remove ${file.filename}`} disabled={loading || uploading} onClick={() => handleRemoveFile(file.document_id)} className="disabled:opacity-30"><X size={15} /></button>
          </div>)}
        </div>}
        <ChatInput message={draft} onMessageChange={setDraft} onSend={sendMessage} onFileSelect={handleFileSelect} disabled={loading || initializing || uploading} uploading={uploading} />
      </div>
    </div>
  </div>;
}
