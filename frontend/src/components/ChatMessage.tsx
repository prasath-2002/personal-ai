"use client";

import {
  isValidElement,
  type ReactNode,
  useState,
} from "react";

import {
  Check,
  Copy,
  Sparkles,
} from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

type ChatMessageProps = {
  role: "user" | "assistant";
  content: string;
};

type CodeBlockProps = {
  code: string;
  language?: string;
};

type AvatarProps = {
  isUser: boolean;
};

function CodeBlock({
  code,
  language = "text",
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch (error) {
      console.error("Failed to copy code:", error);
    }
  }

  return (
    <div className="my-4 overflow-hidden rounded-2xl border border-white/10 bg-[#0d0d0d]">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
        <span className="font-mono text-xs text-white/40">
          {language}
        </span>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-2 rounded-lg px-2 py-1 text-xs text-white/50 transition hover:bg-white/10 hover:text-white"
        >
          {copied ? (
            <>
              <Check size={14} />
              Copied
            </>
          ) : (
            <>
              <Copy size={14} />
              Copy
            </>
          )}
        </button>
      </div>

      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: "1rem",
          background: "transparent",
          fontSize: "0.875rem",
          lineHeight: "1.6",
        }}
        wrapLongLines={false}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

function Avatar({
  isUser,
}: AvatarProps) {
  return (
    <div
      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
        isUser
          ? "bg-white text-black"
          : "border border-white/10 bg-white/10 text-white"
      }`}
    >
      {isUser ? (
        <span className="text-xs font-semibold">
          You
        </span>
      ) : (
        <Sparkles size={16} />
      )}
    </div>
  );
}

export default function ChatMessage({
  role,
  content,
}: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex gap-3 ${
        isUser
          ? "justify-end"
          : "justify-start"
      }`}
    >
      {!isUser && (
        <Avatar isUser={isUser} />
      )}

      <div
        className={`message-bubble ${
          isUser
            ? "message-user"
            : "message-assistant"
        }`}
      >
        <div className="message-author">
          {isUser ? "You" : "Personal AI"}
        </div>

        {isUser ? (
          <p className="whitespace-pre-wrap">
            {content}
          </p>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => (
                <h1 className="mb-3 mt-4 text-2xl font-semibold text-white">
                  {children}
                </h1>
              ),

              h2: ({ children }) => (
                <h2 className="mb-3 mt-4 text-xl font-semibold text-white">
                  {children}
                </h2>
              ),

              h3: ({ children }) => (
                <h3 className="mb-2 mt-3 text-lg font-semibold text-white">
                  {children}
                </h3>
              ),

              p: ({ children }) => (
                <p className="mb-3 last:mb-0">
                  {children}
                </p>
              ),

              ul: ({ children }) => (
                <ul className="mb-3 list-disc space-y-1 pl-6">
                  {children}
                </ul>
              ),

              ol: ({ children }) => (
                <ol className="mb-3 list-decimal space-y-1 pl-6">
                  {children}
                </ol>
              ),

              li: ({ children }) => (
                <li>
                  {children}
                </li>
              ),

              strong: ({ children }) => (
                <strong className="font-semibold text-white">
                  {children}
                </strong>
              ),

              blockquote: ({ children }) => (
                <blockquote className="my-4 border-l-2 border-white/20 pl-4 italic text-white/60">
                  {children}
                </blockquote>
              ),

              a: ({
                href,
                children,
              }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-400 underline underline-offset-4 transition hover:text-blue-300"
                >
                  {children}
                </a>
              ),

              code: ({
                children,
                ...props
              }) => (
                <code
                  className="rounded-md bg-white/10 px-1.5 py-0.5 font-mono text-[13px] text-white"
                  {...props}
                >
                  {children}
                </code>
              ),

              pre: ({ children }) => {
                const child = Array.isArray(children)
                  ? children[0]
                  : children;

                if (
                  isValidElement<{
                    className?: string;
                    children?: ReactNode;
                  }>(child)
                ) {
                  const className =
                    child.props.className || "";

                  const match =
                    /language-([\w-]+)/.exec(
                      className
                    );

                  const language =
                    match?.[1] || "text";

                  const code = String(
                    child.props.children || ""
                  ).replace(/\n$/, "");

                  return (
                    <CodeBlock
                      code={code}
                      language={language}
                    />
                  );
                }

                return (
                  <pre className="overflow-x-auto">
                    {children}
                  </pre>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </div>

      {isUser && (
        <Avatar isUser={isUser} />
      )}
    </div>
  );
}