"use client";

import {
  ParticleBackground,
  Hero,
  AgentPipeline,
  Toolbox,
  HowItWorks,
  WhatsNext,
} from "./components/landing";

export default function LandingPage() {
  return (
    <div
      className="relative min-h-screen overflow-hidden"
      style={{ backgroundColor: "#0a0908" }}
    >
      <ParticleBackground />

      <main className="relative z-10">
        <Hero />

        {/* Divider */}
        <div className="section-divider mx-auto max-w-3xl" />

        <AgentPipeline />

        <div className="section-divider mx-auto max-w-3xl" />

        <Toolbox />

        <div className="section-divider mx-auto max-w-3xl" />

        <HowItWorks />

        <div className="section-divider mx-auto max-w-3xl" />

        <WhatsNext />

        {/* Footer with version */}
        <footer className="py-12 text-center">
          <p
            className="text-xs mb-4 max-w-sm mx-auto"
            style={{
              color: "#6a655d",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            NanoRange — so researchers can focus on discovery, not configuration.
          </p>
          <div
            className="inline-flex items-center gap-2 text-sm"
            style={{
              color: "#6a655d",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            <div
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ backgroundColor: "#ff6b35" }}
            />
            <span>v0.1.0</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
