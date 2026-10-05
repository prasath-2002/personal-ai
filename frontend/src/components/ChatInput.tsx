"use client";
import { useRef } from "react";
import { ArrowUp, LoaderCircle, Paperclip, Sparkles } from "lucide-react";

type Props = {
  onSend: (message: string) => Promise<void>;
  onFileSelect: (file: File) => Promise<void>;
  disabled?: boolean; uploading?: boolean;
  message: string; onMessageChange: (message: string) => void;
};
export default function ChatInput({ onSend, onFileSelect, disabled = false, uploading = false, message, onMessageChange }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  async function send() {
    if (!message.trim() || disabled || uploading) return;
    const text = message.trim(); onMessageChange(""); await onSend(text);
  }
  return <div className="composer-wrap">
    <div className="composer">
      <textarea aria-label="Message" maxLength={20000} value={message} onChange={(e) => onMessageChange(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }}
        disabled={disabled} placeholder="Where should we start?" rows={2} />
      <input ref={fileInputRef} type="file" accept=".pdf,.txt" className="hidden" onChange={async (e) => {
        const input = e.currentTarget; const file = input.files?.[0]; if (file) await onFileSelect(file); input.value = "";
      }} />
      <div className="composer-controls">
        <div className="flex items-center gap-3"><button type="button" onClick={() => fileInputRef.current?.click()} disabled={disabled || uploading} className="attach-button" title="Attach PDF or TXT" aria-label="Attach PDF or TXT"><Paperclip size={17} /><span>Attach</span></button><span className="composer-divider" /><span className="composer-mode"><Sparkles size={13} /> Personal AI</span></div>
        <button type="button" onClick={send} disabled={disabled || !message.trim()} className="send-button" aria-label={disabled ? "Waiting for response" : "Send message"}>{disabled ? <LoaderCircle size={18} className="animate-spin" /> : <ArrowUp size={20} />}</button>
      </div>
    </div>
    <div className="composer-footer"><span>{uploading ? "Processing your document…" : "A little intelligence. A lot of possibility."}</span><span className="keyboard-hint"><kbd>↵</kbd> send <span>·</span> <kbd>shift ↵</kbd> new line</span></div>
  </div>;
}
