"use client";

type GalleryType = "images" | "plots" | "data";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNavigate: (type: GalleryType) => void;
}

export function Sidebar({ isOpen, onToggle, onNavigate }: SidebarProps) {
  return (
    <>
      {/* Close Button - Only visible when sidebar is open */}
      {isOpen && (
        <button
          onClick={onToggle}
          className="group fixed left-4 top-4 z-50 p-2.5 rounded-lg transition-all hover:scale-105"
          style={{
            backgroundColor: "rgba(255, 107, 53, 0.15)",
            border: "1px solid rgba(255, 107, 53, 0.3)",
            color: "#ff6b35",
          }}
          title="Close Sidebar"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          {/* Tooltip on hover */}
          <span
            className="absolute left-full ml-2 px-2 py-1 rounded text-xs font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
            style={{
              backgroundColor: "#1a1816",
              border: "1px solid rgba(255, 107, 53, 0.3)",
              color: "#c4b8a8",
            }}
          >
            Close Sidebar
          </span>
        </button>
      )}

      {/* Sidebar Panel */}
      <div
        className={`fixed left-0 top-0 h-full z-40 transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{
          width: "220px",
          backgroundColor: "#0d0b0a",
          borderRight: "1px solid rgba(255, 107, 53, 0.15)",
        }}
      >
        {/* Header */}
        <div
          className="px-4 pt-16 pb-3 border-b"
          style={{ borderColor: "rgba(255, 107, 53, 0.15)" }}
        >
          <h2 className="text-base font-semibold" style={{ color: "#c4b8a8" }}>
            Results
          </h2>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-2">
          <button
            onClick={() => onNavigate("images")}
            className="w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all hover:bg-white/5"
            style={{ color: "#c4b8a8" }}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#ff6b35">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span className="text-sm font-medium">Images</span>
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="#6a655d">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button
            onClick={() => onNavigate("plots")}
            className="w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all hover:bg-white/5"
            style={{ color: "#c4b8a8" }}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#d4a574">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <span className="text-sm font-medium">Plots</span>
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="#6a655d">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button
            onClick={() => onNavigate("data")}
            className="w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all hover:bg-white/5"
            style={{ color: "#c4b8a8" }}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#22c55e">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <span className="text-sm font-medium">Data</span>
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="#6a655d">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </nav>
      </div>

      {/* Overlay to close sidebar when clicking outside */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50"
          onClick={onToggle}
        />
      )}
    </>
  );
}
