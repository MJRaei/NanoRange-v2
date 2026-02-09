"use client";

import Link from "next/link";
import { NanoIcon } from "../NanoIcon";
import { useEffect, useState } from "react";

const techBadges = [
  "Gemini 3.0",
  "Multi-Agent",
  "Google ADK",
  "10+ Tools",
];

export function Hero() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className="flex flex-col items-center pt-10 md:pt-16 px-6 pb-16 md:pb-24">
      {/* Icon container */}
      <div className="icon-container mb-10">
        <NanoIcon size="large" />
      </div>

      {/* App name */}
      <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4">
        <span style={{ color: "#c4b8a8" }}>Nano</span>
        <span style={{ color: "#ff6b35" }}>Range</span>
      </h1>

      {/* Tagline */}
      <p
        className="text-lg md:text-xl tracking-wide mb-3 text-center max-w-lg"
        style={{
          color: "#8a857d",
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        An Agentic Framework for Microscopy Image Analysis
      </p>

      {/* Vision statement */}
      <p
        className="text-sm tracking-wide mb-8 text-center max-w-md"
        style={{
          color: "#6a655d",
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        So researchers can focus on discovery, not configuration.
      </p>

      {/* Tech badges */}
      <div className="flex flex-wrap justify-center gap-2 mb-10">
        {techBadges.map((badge, i) => (
          <span
            key={badge}
            className="tech-badge text-xs px-3 py-1.5 rounded-full transition-all duration-300"
            style={{
              backgroundColor: "rgba(255, 107, 53, 0.08)",
              border: "1px solid rgba(255, 107, 53, 0.2)",
              color: "#ff8c5a",
              fontFamily: "'JetBrains Mono', monospace",
              opacity: mounted ? 1 : 0,
              transform: mounted ? "translateY(0)" : "translateY(10px)",
              transition: `opacity 0.5s ease ${0.3 + i * 0.1}s, transform 0.5s ease ${0.3 + i * 0.1}s`,
            }}
          >
            {badge}
          </span>
        ))}
      </div>

      {/* CTA Button */}
      <Link
        href="/chat"
        className="cta-button px-10 py-4 rounded-full font-semibold text-lg tracking-wide flex items-center gap-3 group transition-all duration-300 hover:scale-105"
        style={{
          background: "linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%)",
          color: "#0a0908",
          boxShadow: "0 4px 20px rgba(255, 107, 53, 0.3)",
        }}
      >
        <span>Start Analyzing</span>
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
      </Link>
    </section>
  );
}
