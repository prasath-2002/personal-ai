import ChatMessage from "@/components/ChatMessage";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ChatWindowProps = {
  messages: Message[];
  loading?: boolean;
};

export default function ChatWindow({
  messages,
  loading = false,
}: ChatWindowProps) {
  const lastMessage =
    messages[
      messages.length - 1
    ];

  const waitingForFirstChunk =
    loading &&
    lastMessage?.role ===
      "assistant" &&
    lastMessage.content === "";

  return (
    <div className="space-y-7">
      {messages.map(
        (
          message,
          index
        ) => (
          <ChatMessage
            key={index}
            role={
              message.role
            }
            content={
              message.content
            }
          />
        )
      )}

      {waitingForFirstChunk && (
        <div className="flex items-center gap-2 text-sm text-white/40">
          <div className="h-2 w-2 animate-pulse rounded-full bg-white/50" />

          Personal AI is thinking...
        </div>
      )}
    </div>
  );
}