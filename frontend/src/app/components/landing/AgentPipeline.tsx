"use client";

import { useState, useEffect, useRef } from "react";

const agents = [
  {
    id: "planner",
    name: "Planner",
    description: "Reviews image & builds pipeline",
    detail:
      "Selects appropriate tools, orders them, and verifies pipeline compatibility before proposing to the user.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
  },
  {
    id: "executor",
    name: "Executor",
    description: "Runs each tool in sequence",
    detail:
      "Executes the confirmed pipeline step by step, feeding outputs into the next stage.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    id: "critic",
    name: "Critic",
    description: "Evaluates output quality",
    detail:
      "Uses vision capabilities to assess whether the processed image meets quality standards.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
  {
    id: "optimizer",
    name: "Optimizer",
    description: "Tunes parameters automatically",
    detail:
      "Adjusts tool parameters based on critic feedback and re-runs the pipeline for better results.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
      </svg>
    ),
  },
];

function Connector({ delay = 0 }: { delay?: number }) {
  return (
    <div className="pipeline-connector hidden md:flex">
      <div className="connector-line">
        <div className="flow-dot" style={{ animationDelay: `${delay}s` }} />
      </div>
    </div>
  );
}

export function AgentPipeline() {
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="px-6 py-16 md:py-24">
      <div className="max-w-5xl mx-auto">
        {/* Section title */}
        <h2
          className={`text-2xl md:text-3xl font-semibold text-center mb-4 reveal ${isVisible ? "visible" : ""}`}
          style={{ color: "#c4b8a8" }}
        >
          Multi-Agent Architecture
        </h2>
        <p
          className={`text-center text-sm mb-14 reveal stagger-1 ${isVisible ? "visible" : ""}`}
          style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
        >
          Powered by Google ADK &amp; Gemini 3.0
        </p>

        {/* Agent pipeline - desktop horizontal */}
        <div className="hidden md:flex items-stretch justify-center">
          {agents.map((agent, i) => (
            <div key={agent.id} className="flex items-center">
              <div
                className={`agent-card reveal p-5 rounded-xl w-[180px] ${isVisible ? "visible" : ""} ${activeAgent === agent.id ? "active" : ""}`}
                style={{
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 107, 53, 0.12)",
                  transitionDelay: `${i * 0.12}s`,
                }}
                onClick={() =>
                  setActiveAgent(activeAgent === agent.id ? null : agent.id)
                }
              >
                <div className="mb-3" style={{ color: "#ff6b35" }}>
                  {agent.icon}
                </div>
                <h3 className="text-base font-semibold mb-1" style={{ color: "#f5f0e8" }}>
                  {agent.name}
                </h3>
                <p
                  className="text-xs leading-relaxed"
                  style={{ color: "#8a857d", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  {agent.description}
                </p>
                {/* Expanded detail */}
                <div
                  className="overflow-hidden transition-all duration-300"
                  style={{
                    maxHeight: activeAgent === agent.id ? "80px" : "0px",
                    opacity: activeAgent === agent.id ? 1 : 0,
                  }}
                >
                  <p
                    className="text-xs mt-3 pt-3 leading-relaxed"
                    style={{
                      color: "#c4b8a8",
                      fontFamily: "'JetBrains Mono', monospace",
                      borderTop: "1px solid rgba(255, 107, 53, 0.15)",
                    }}
                  >
                    {agent.detail}
                  </p>
                </div>
              </div>
              {i < agents.length - 1 && <Connector delay={i * 0.5} />}
            </div>
          ))}
        </div>

        {/* Agent pipeline - mobile vertical */}
        <div className="md:hidden flex flex-col items-center gap-3">
          {agents.map((agent, i) => (
            <div key={agent.id} className="w-full max-w-sm">
              <div
                className={`agent-card reveal p-5 rounded-xl ${isVisible ? "visible" : ""} ${activeAgent === agent.id ? "active" : ""}`}
                style={{
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 107, 53, 0.12)",
                  transitionDelay: `${i * 0.1}s`,
                }}
                onClick={() =>
                  setActiveAgent(activeAgent === agent.id ? null : agent.id)
                }
              >
                <div className="flex items-center gap-3 mb-2">
                  <div style={{ color: "#ff6b35" }}>{agent.icon}</div>
                  <h3 className="text-base font-semibold" style={{ color: "#f5f0e8" }}>
                    {agent.name}
                  </h3>
                </div>
                <p
                  className="text-xs leading-relaxed"
                  style={{ color: "#8a857d", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  {agent.description}
                </p>
                <div
                  className="overflow-hidden transition-all duration-300"
                  style={{
                    maxHeight: activeAgent === agent.id ? "80px" : "0px",
                    opacity: activeAgent === agent.id ? 1 : 0,
                  }}
                >
                  <p
                    className="text-xs mt-3 pt-3 leading-relaxed"
                    style={{
                      color: "#c4b8a8",
                      fontFamily: "'JetBrains Mono', monospace",
                      borderTop: "1px solid rgba(255, 107, 53, 0.15)",
                    }}
                  >
                    {agent.detail}
                  </p>
                </div>
              </div>
              {/* Vertical connector */}
              {i < agents.length - 1 && (
                <div className="flex justify-center py-1">
                  <svg width="2" height="20" className="opacity-40">
                    <line x1="1" y1="0" x2="1" y2="20" stroke="#ff6b35" strokeWidth="2" strokeDasharray="4 4" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Iterative loop indicator */}
        <div
          className={`loop-indicator mt-8 mx-auto max-w-md rounded-lg px-5 py-3 flex items-center justify-center gap-3 reveal stagger-5 ${isVisible ? "visible" : ""}`}
          style={{
            backgroundColor: "rgba(255, 107, 53, 0.05)",
            border: "1px solid rgba(255, 107, 53, 0.12)",
          }}
        >
          <span className="loop-icon text-lg" style={{ color: "#ff6b35" }}>
            ↻
          </span>
          <span
            className="text-xs"
            style={{ color: "#8a857d", fontFamily: "'JetBrains Mono', monospace" }}
          >
            Iterative loop — Executor → Critic → Optimizer — up to 3 rounds
          </span>
        </div>
      </div>
    </section>
  );
}
