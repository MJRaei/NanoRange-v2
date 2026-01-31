"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "./types";
import { getStaticUrl, getCsvUrl } from "./api";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex gap-4 mb-6 chat-message ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* Assistant Avatar */}
      {!isUser && (
        <div
          className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
          style={{ backgroundColor: "rgba(255, 107, 53, 0.2)" }}
        >
          <svg className="w-4 h-4" fill="#ff6b35" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" />
          </svg>
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        {/* Attached Image (for user messages) */}
        {isUser && message.attachedImage && (
          <div className="mb-2">
            <img
              src={message.attachedImage}
              alt="Attached"
              className="max-w-xs rounded-lg"
              style={{ border: "1px solid rgba(255, 107, 53, 0.3)" }}
            />
          </div>
        )}

        {/* Message Content */}
        <div
          className={`px-4 py-3 rounded-2xl ${isUser ? "rounded-br-md" : "rounded-bl-md"} ${!isUser ? "markdown-content" : ""} overflow-x-auto max-w-full`}
          style={{
            backgroundColor: isUser
              ? "rgba(255, 107, 53, 0.15)"
              : "rgba(196, 184, 168, 0.08)",
            color: isUser ? "#f5f0e8" : "#c4b8a8",
            overflowWrap: "anywhere",
            wordBreak: "break-word",
          }}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom renderers for better styling
                p: ({ children }) => (
                  <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-[#ff6b35]">{children}</strong>
                ),
                em: ({ children }) => (
                  <em className="italic text-[#e5dcd0]">{children}</em>
                ),
                code: ({ children, className }) => {
                  const isInline = !className;
                  return isInline ? (
                    <code className="px-1.5 py-0.5 rounded bg-[rgba(255,107,53,0.15)] text-[#ff9f7a] font-mono text-sm">
                      {children}
                    </code>
                  ) : (
                    <code className={className}>{children}</code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="my-3 p-3 rounded-lg bg-[rgba(0,0,0,0.3)] overflow-x-auto font-mono text-sm">
                    {children}
                  </pre>
                ),
                ul: ({ children }) => (
                  <ul className="my-3 ml-4 space-y-1.5 list-disc marker:text-[#ff6b35]">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="my-3 ml-4 space-y-1.5 list-decimal marker:text-[#ff6b35]">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="leading-relaxed pl-1">{children}</li>
                ),
                h1: ({ children }) => (
                  <h1 className="text-xl font-bold text-[#f5f0e8] mb-3 mt-4 first:mt-0 border-b border-[rgba(255,107,53,0.2)] pb-2">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-lg font-semibold text-[#f5f0e8] mb-2 mt-4 first:mt-0">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-base font-semibold text-[#e5dcd0] mb-2 mt-3 first:mt-0">
                    {children}
                  </h3>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="my-3 pl-4 border-l-3 border-[#ff6b35] italic text-[#a09888]">
                    {children}
                  </blockquote>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#ff6b35] underline underline-offset-2 hover:text-[#ff9f7a] transition-colors"
                  >
                    {children}
                  </a>
                ),
                table: ({ children }) => (
                  <div className="my-3 overflow-x-auto">
                    <table className="min-w-full border-collapse text-sm">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="px-3 py-2 text-left font-semibold bg-[rgba(255,107,53,0.1)] border border-[rgba(255,107,53,0.2)]">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-3 py-2 border border-[rgba(255,107,53,0.15)]">
                    {children}
                  </td>
                ),
                hr: () => (
                  <hr className="my-4 border-t border-[rgba(255,107,53,0.2)]" />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Analysis Results (Images) */}
        {message.images && message.images.length > 0 && (
          <div className="mt-3 space-y-3 w-full">
            {message.images.map((img) => (
              <div key={img.key} className="analysis-image-container">
                <p className="text-xs mb-2 uppercase tracking-wide" style={{ color: "#6a655d" }}>
                  {img.title}
                </p>
                <img
                  src={getStaticUrl(img.url)}
                  alt={img.title}
                  className="rounded-lg w-full max-w-lg analysis-image"
                  style={{ border: "1px solid rgba(255, 107, 53, 0.2)" }}
                />
              </div>
            ))}
          </div>
        )}

        {/* CSV Download Link */}
        {message.csvPath && (
          <a
            href={getCsvUrl(message.csvPath)}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors csv-link"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download Shape Data (CSV)
          </a>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div
          className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
          style={{ backgroundColor: "rgba(196, 184, 168, 0.2)" }}
        >
          <svg className="w-4 h-4" fill="#c4b8a8" viewBox="0 0 24 24">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        </div>
      )}
    </div>
  );
}

export function LoadingIndicator() {
  return (
    <div className="flex gap-4 mb-6">
      <div
        className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
        style={{ backgroundColor: "rgba(255, 107, 53, 0.2)" }}
      >
        <svg className="w-4 h-4" fill="#ff6b35" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" />
        </svg>
      </div>
      <div
        className="px-4 py-3 rounded-2xl rounded-bl-md"
        style={{ backgroundColor: "rgba(196, 184, 168, 0.08)" }}
      >
        <div className="flex gap-1.5 py-1">
          <span className="w-2 h-2 rounded-full loading-dot" style={{ backgroundColor: "#ff6b35" }} />
          <span className="w-2 h-2 rounded-full loading-dot" style={{ backgroundColor: "#ff6b35" }} />
          <span className="w-2 h-2 rounded-full loading-dot" style={{ backgroundColor: "#ff6b35" }} />
        </div>
      </div>
    </div>
  );
}

