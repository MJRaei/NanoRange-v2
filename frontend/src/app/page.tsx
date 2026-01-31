"use client";

import {
  ParticleBackground,
  Hero,
  Features,
  HowItWorks,
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
        <Features />
        <HowItWorks />

        {/* Footer with version */}
        <footer className="py-12 text-center">
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
