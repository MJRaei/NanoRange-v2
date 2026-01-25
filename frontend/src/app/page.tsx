"use client";

import { useEffect, useState, useRef, useCallback, KeyboardEvent } from "react";
import {
  Sidebar,
  GalleryView,
  ChatMessage,
  LoadingIndicator,
  ImageUpload,
  AttachedImagePreview,
  NanoIcon,
  Message,
  MessageImage,
  analyzeImage,
  checkHealth,
  PipelineEditor,
} from "./components";

// UUID generator that works in all browsers
function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

type GalleryType = "images" | "plots" | "data";

interface Particle {
  id: number;
  size: number;
  x: number;
  y: number;
  delay: number;
  type: "orange" | "white";
}

function generateParticles(count: number): Particle[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    size: Math.random() * 8 + 4,
    x: Math.random() * 100,
    y: Math.random() * 100,
    delay: Math.random() * 5,
    type: Math.random() > 0.6 ? "orange" : "white",
  }));
}

function ChatView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [galleryView, setGalleryView] = useState<GalleryType | null>(null);
  const [attachedImagePath, setAttachedImagePath] = useState<string | null>(null);
  const [attachedImagePreview, setAttachedImagePreview] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showPipeline, setShowPipeline] = useState(true);
  const [splitPosition, setSplitPosition] = useState(50); // percentage
  const [isResizing, setIsResizing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle resize drag
  const handleMouseDown = useCallback(() => {
    setIsResizing(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();
      const newPosition = ((e.clientX - containerRect.left) / containerRect.width) * 100;

      // Clamp between 20% and 80%
      setSplitPosition(Math.min(80, Math.max(20, newPosition)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  // Check API health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const handleImageUploaded = (path: string, previewUrl: string) => {
    setAttachedImagePath(path);
    setAttachedImagePreview(previewUrl);
  };

  const handleRemoveImage = (revokeUrl: boolean = true) => {
    setAttachedImagePath(null);
    if (revokeUrl && attachedImagePreview) {
      URL.revokeObjectURL(attachedImagePreview);
    }
    setAttachedImagePreview(null);
  };

  const handleSubmit = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
      attachedImage: attachedImagePreview || undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    const currentImagePath = attachedImagePath;
    setInputValue("");
    // Don't revoke the URL since it's now used in the message
    handleRemoveImage(false);
    setIsLoading(true);

    try {
      // Call the backend API with session_id for conversation continuity
      const result = await analyzeImage(currentInput, currentImagePath, sessionId);

      // Store session_id for subsequent messages
      if (result.session_id && !sessionId) {
        setSessionId(result.session_id);
      }

      // Prepare images for display in chat
      const messageImages: MessageImage[] = [];

      if (result.images.thresholded_with_shapes) {
        messageImages.push({
          key: "thresholded_with_shapes",
          url: result.images.thresholded_with_shapes,
          title: "Detected Particles",
        });
      }

      if (result.images.size_distribution) {
        messageImages.push({
          key: "size_distribution",
          url: result.images.size_distribution,
          title: "Size Distribution",
        });
      }

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: result.message,
        timestamp: new Date(),
        images: result.success ? messageImages : undefined,
        csvPath: result.csv_path || undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error during analysis:", error);
      const errorMessage: Message = {
        id: generateId(),
        role: "assistant",
        content:
          "Sorry, I couldn't connect to the analysis server. Please make sure the backend is running.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const hasMessages = messages.length > 0;

  const handleNavigateToGallery = (type: GalleryType) => {
    setSidebarOpen(false);
    setGalleryView(type);
  };

  // Show gallery view if selected
  if (galleryView) {
    return (
      <GalleryView
        type={galleryView}
        onBack={() => setGalleryView(null)}
        sessionId={sessionId}
      />
    );
  }

  return (
    <div ref={containerRef} className="flex h-screen" style={{ backgroundColor: "#0a0908" }}>
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onNavigate={handleNavigateToGallery}
      />

      {/* Left side - Chat */}
      <div
        className="flex flex-col h-full"
        style={{
          width: showPipeline ? `${splitPosition}%` : "100%",
          transition: isResizing ? "none" : "width 0.3s ease",
        }}
      >
        {/* Header */}
        <header
          className="flex items-center justify-between pl-6 pr-0 py-4 border-b shrink-0"
          style={{ borderColor: "rgba(255, 107, 53, 0.1)" }}
        >
          <div className="flex items-center gap-3">
            <NanoIcon size="small" />
            <h1 className="text-xl font-semibold">
              <span style={{ color: "#c4b8a8" }}>Nan</span>
              <span style={{ color: "#ff6b35" }}>Orange</span>
            </h1>
          </div>
          <button
            onClick={() => setShowPipeline(!showPipeline)}
            className="group flex items-center gap-2 pl-2 pr-4 py-1.5 rounded-l-lg text-xs font-medium transition-colors hover:bg-white/5"
            style={{ color: showPipeline ? "#ff6b35" : "#6a655d" }}
          >
            <span className="opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              {showPipeline ? "Hide Pipeline" : "Show Pipeline"}
            </span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
              />
            </svg>
          </button>
        </header>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto chat-scroll">
          {!hasMessages ? (
            /* Empty state - centered content */
            <div className="flex flex-col items-center justify-center h-full px-6">
              <div className="mb-8 opacity-60">
                <NanoIcon size="small" />
              </div>
              <h2
                className="text-2xl font-semibold mb-4 text-center"
                style={{ color: "#c4b8a8" }}
              >
                How can I help you analyze?
              </h2>
              <p
                className="text-center max-w-md mb-8 text-sm"
                style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
              >
                Upload microscopy images, ask questions, or build a pipeline visually.
              </p>

              {/* Instructions for getting started */}
              <div
                className="p-4 rounded-xl max-w-sm"
                style={{
                  backgroundColor: "rgba(255, 107, 53, 0.05)",
                  border: "1px solid rgba(255, 107, 53, 0.1)",
                }}
              >
                <h3 className="text-xs font-medium mb-2" style={{ color: "#ff6b35" }}>
                  Getting Started
                </h3>
                <ol
                  className="text-xs space-y-1.5"
                  style={{ color: "#8a857d", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  <li className="flex items-start gap-2">
                    <span style={{ color: "#ff6b35" }}>1.</span>
                    Upload an image and describe your analysis
                  </li>
                  <li className="flex items-start gap-2">
                    <span style={{ color: "#ff6b35" }}>2.</span>
                    Or build a pipeline visually on the right
                  </li>
                  <li className="flex items-start gap-2">
                    <span style={{ color: "#ff6b35" }}>3.</span>
                    Run and iterate on your analysis
                  </li>
                </ol>
              </div>
            </div>
          ) : (
            /* Messages */
            <div className="px-6 py-8">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}

              {/* Loading indicator */}
              {isLoading && <LoadingIndicator />}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="px-6 py-4 shrink-0">
          <div>
            {/* Attached image preview */}
            {attachedImagePreview && (
              <div className="mb-3">
                <AttachedImagePreview
                  previewUrl={attachedImagePreview}
                  onRemove={handleRemoveImage}
                />
              </div>
            )}

            <div
              className="flex items-end gap-3 rounded-2xl px-4 py-3 transition-all chat-input-container"
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 107, 53, 0.15)",
              }}
            >
              {/* Attachment button */}
              <ImageUpload onImageUploaded={handleImageUploaded} disabled={isLoading} />

              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your analysis request..."
                rows={1}
                className="flex-1 bg-transparent border-none outline-none resize-none text-base leading-relaxed"
                style={{
                  color: "#f5f0e8",
                  fontFamily: "'JetBrains Mono', monospace",
                  maxHeight: "200px",
                }}
              />

              {/* Send button */}
              <button
                onClick={handleSubmit}
                disabled={!inputValue.trim() || isLoading}
                className="shrink-0 p-2 rounded-lg transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: inputValue.trim() ? "rgba(255, 107, 53, 0.8)" : "transparent",
                  color: inputValue.trim() ? "#0a0908" : "#6a655d",
                }}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>

            <p
              className="text-xs text-center mt-3"
              style={{ color: "#4a4540", fontFamily: "'JetBrains Mono', monospace" }}
            >
              NanOrange may produce inaccurate results. Verify important measurements.
            </p>
          </div>
        </div>
      </div>

      {/* Resize Handle */}
      {showPipeline && (
        <div
          className="w-1 h-full cursor-col-resize group flex items-center justify-center hover:bg-orange-500/20 transition-colors"
          style={{
            backgroundColor: isResizing ? "rgba(255, 107, 53, 0.3)" : "rgba(255, 107, 53, 0.1)",
          }}
          onMouseDown={handleMouseDown}
        >
          <div
            className="w-1 h-8 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ backgroundColor: "#ff6b35" }}
          />
        </div>
      )}

      {/* Right side - Pipeline Editor */}
      {showPipeline && (
        <div className="h-full" style={{ width: `${100 - splitPosition}%` }}>
          <PipelineEditor />
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const [particles, setParticles] = useState<Particle[]>([]);
  const [mounted, setMounted] = useState(false);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    setParticles(generateParticles(20));
    setMounted(true);
  }, []);

  if (showChat) {
    return <ChatView />;
  }

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "#0a0908" }}>
      {/* Grid overlay */}
      <div className="absolute inset-0 grid-overlay" />

      {/* Floating particles */}
      {mounted &&
        particles.map((particle) => (
          <div
            key={particle.id}
            className={`particle ${
              particle.type === "orange" ? "particle-orange" : "particle-white"
            }`}
            style={{
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              animationDelay: `${particle.delay}s`,
            }}
          />
        ))}

      {/* Radial gradient background accent */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full opacity-30 pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(255, 107, 53, 0.2) 0%, transparent 70%)",
        }}
      />

      {/* Main content */}
      <main className="relative z-10 flex flex-col items-center pt-10 md:pt-16 min-h-screen px-6">
        {/* Icon container */}
        <div className="icon-container mb-10">
          <NanoIcon size="large" />
        </div>

        {/* App name */}
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4">
          <span style={{ color: "#c4b8a8" }}>Nan</span>
          <span style={{ color: "#ff6b35" }}>Orange</span>
        </h1>

        {/* Tagline */}
        <p
          className="text-lg md:text-xl tracking-wide mb-12 text-center max-w-md"
          style={{
            color: "#8a857d",
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          AI-Powered Nanoparticle Analysis
        </p>

        {/* CTA Button */}
        <button
          onClick={() => setShowChat(true)}
          className="px-10 py-4 rounded-full font-semibold text-lg tracking-wide flex items-center gap-3 group cursor-pointer transition-all duration-300 hover:scale-105"
          style={{
            background: "linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%)",
            color: "#0a0908",
            boxShadow: "0 4px 20px rgba(255, 107, 53, 0.3)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background =
              "linear-gradient(135deg, #ff8c5a 0%, #ff6b35 100%)";
            e.currentTarget.style.boxShadow = "0 8px 30px rgba(255, 107, 53, 0.5)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background =
              "linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%)";
            e.currentTarget.style.boxShadow = "0 4px 20px rgba(255, 107, 53, 0.3)";
          }}
        >
          <span>Launch Analysis</span>
          <svg
            className="w-5 h-5 transition-transform group-hover:translate-x-1"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 7l5 5m0 0l-5 5m5-5H6"
            />
          </svg>
        </button>

        {/* Version badge */}
        <div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2 text-sm"
          style={{
            color: "#8a857d",
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          <div
            className="w-2 h-2 rounded-full animate-pulse"
            style={{ backgroundColor: "#ff6b35" }}
          />
          <span>v0.1.0</span>
        </div>
      </main>
    </div>
  );
}
