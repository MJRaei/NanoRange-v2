"use client";

import { useState, useEffect } from "react";
import { FileInfo, SidebarFiles } from "./types";
import { listFiles, getStaticUrl, getHtmlUrl, getCsvUrl } from "./api";

type GalleryType = "images" | "plots" | "data";

interface GalleryViewProps {
  type: GalleryType;
  onBack: () => void;
  sessionId?: string | null;
}

export function GalleryView({ type, onBack, sessionId }: GalleryViewProps) {
  const [files, setFiles] = useState<SidebarFiles>({ images: [], plots: [], csv_files: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<FileInfo | null>(null);

  useEffect(() => {
    const fetchFiles = async () => {
      setIsLoading(true);
      try {
        const data = await listFiles(sessionId || undefined);
        setFiles(data);
      } catch (error) {
        console.error("Failed to fetch files:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchFiles();
  }, [sessionId]);

  // Get the appropriate files based on type
  const getCurrentFiles = (): FileInfo[] => {
    switch (type) {
      case "images":
        return files.images;
      case "plots":
        return files.plots;
      case "data":
        return files.csv_files;
      default:
        return [];
    }
  };

  const currentFiles = getCurrentFiles();

  const getTitle = (): string => {
    switch (type) {
      case "images":
        return "Images";
      case "plots":
        return "Plots";
      case "data":
        return "Data";
      default:
        return "";
    }
  };

  const handleImageClick = (file: FileInfo) => {
    // For images and plots, open the modal
    if (type === "images" || type === "plots") {
      setSelectedImage(file);
    }
  };

  const handleCsvDownload = (file: FileInfo) => {
    // Trigger download for CSV files
    const link = document.createElement("a");
    link.href = getCsvUrl(file.path);
    link.download = file.name + ".csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenInteractive = (file: FileInfo) => {
    if (file.interactive_html) {
      window.open(getHtmlUrl(file.interactive_html), "_blank");
    }
  };

  const getEmptyStateIcon = () => {
    switch (type) {
      case "images":
        return (
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="#ff6b35">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        );
      case "plots":
        return (
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="#d4a574">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        );
      case "data":
        return (
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="#22c55e">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        );
    }
  };

  return (
    <div className="flex flex-col h-screen" style={{ backgroundColor: "#0a0908" }}>
      {/* Header */}
      <header
        className="flex items-center px-6 py-4 border-b"
        style={{ borderColor: "rgba(255, 107, 53, 0.1)" }}
      >
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/5"
          style={{ color: "#c4b8a8" }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          <span>Back to Chat</span>
        </button>
        <h1
          className="ml-6 text-xl font-semibold"
          style={{ color: "#ff6b35" }}
        >
          {getTitle()}
        </h1>
      </header>

      {/* Gallery Content */}
      <div className="flex-1 overflow-y-auto p-6 chat-scroll">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="loading-spinner" />
          </div>
        ) : currentFiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
              style={{ backgroundColor: "rgba(255, 107, 53, 0.1)" }}
            >
              {getEmptyStateIcon()}
            </div>
            <p className="text-center text-lg mb-2" style={{ color: "#c4b8a8" }}>
              No {type} available yet
            </p>
            <p
              className="text-center text-sm"
              style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
            >
              Run an analysis to generate results.
            </p>
          </div>
        ) : (
          <div className="max-w-6xl mx-auto">
            {/* Grid of items */}
            {type === "data" ? (
              /* Data/CSV Files Grid */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentFiles.map((file) => (
                  <button
                    key={file.path}
                    onClick={() => handleCsvDownload(file)}
                    className="flex items-center gap-4 p-4 rounded-xl transition-all hover:scale-[1.02]"
                    style={{
                      backgroundColor: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid rgba(34, 197, 94, 0.2)",
                    }}
                  >
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                      style={{ backgroundColor: "rgba(34, 197, 94, 0.1)" }}
                    >
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#22c55e">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <span className="text-sm truncate block" style={{ color: "#c4b8a8" }}>
                        {file.name}
                      </span>
                      <span
                        className="text-xs"
                        style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        Click to download CSV
                      </span>
                    </div>
                    <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="#6a655d">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                  </button>
                ))}
              </div>
            ) : (
              /* Images and Plots Grid */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {currentFiles.map((file) => (
                  <div
                    key={file.path}
                    onClick={() => handleImageClick(file)}
                    className="group cursor-pointer rounded-xl overflow-hidden transition-all hover:scale-[1.02]"
                    style={{
                      backgroundColor: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid rgba(255, 107, 53, 0.15)",
                    }}
                  >
                    <div className="aspect-square overflow-hidden relative">
                      <img
                        src={getStaticUrl(file.path)}
                        alt={file.name}
                        className="w-full h-full object-cover transition-transform group-hover:scale-105"
                      />
                      {/* Interactive indicator */}
                      {file.interactive_html && (
                        <div
                          className="absolute top-2 right-2 px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1"
                          style={{
                            backgroundColor: "rgba(212, 165, 116, 0.9)",
                            color: "#0a0908",
                          }}
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
                            />
                          </svg>
                          Interactive
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      <h3
                        className="text-sm font-medium truncate"
                        style={{ color: "#c4b8a8" }}
                      >
                        {file.name}
                      </h3>
                      <p
                        className="text-xs mt-1"
                        style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
                      >
                        {file.interactive_html ? "Click to view • Interactive available" : "Click to view full size"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Image Preview Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0, 0, 0, 0.95)" }}
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-5xl max-h-[90vh] w-full" onClick={(e) => e.stopPropagation()}>
            {/* Close button */}
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-12 right-0 p-2 rounded-lg transition-colors hover:bg-white/10"
              style={{ color: "#c4b8a8" }}
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {/* Image */}
            <img
              src={getStaticUrl(selectedImage.path)}
              alt={selectedImage.name}
              className="w-full h-auto rounded-lg"
              style={{ maxHeight: "75vh", objectFit: "contain" }}
            />
            
            {/* Footer with title and interactive button */}
            <div className="flex items-center justify-between mt-4">
              <p className="text-lg" style={{ color: "#c4b8a8" }}>
                {selectedImage.name}
              </p>
              
              {selectedImage.interactive_html && (
                <button
                  onClick={() => handleOpenInteractive(selectedImage)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:scale-105"
                  style={{
                    backgroundColor: "rgba(212, 165, 116, 0.2)",
                    border: "1px solid rgba(212, 165, 116, 0.4)",
                    color: "#d4a574",
                  }}
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
                    />
                  </svg>
                  <span className="font-medium">Open Interactive Plot</span>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
