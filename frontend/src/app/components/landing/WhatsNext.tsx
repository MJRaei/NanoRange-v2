"use client";

import { useEffect, useRef, useState } from "react";

const roadmapItems = [
  {
    title: "Batch Processing",
    description: "Process hundreds of images in parallel — hours of work in minutes.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    title: "Dataset Generation",
    description: "Generate annotated datasets at scale for training specialized ML models.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
  },
  {
    title: "Community Tools",
    description: "Open-source toolbox for the microscopy community to contribute and share.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
];

export function WhatsNext() {
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
          What&apos;s Next
        </h2>
        <p
          className={`text-center text-sm mb-14 reveal stagger-1 ${isVisible ? "visible" : ""}`}
          style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
        >
          The microscopy analysis market is projected to reach $5.9B by 2031
        </p>

        {/* Roadmap cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {roadmapItems.map((item, i) => (
            <div
              key={item.title}
              className={`roadmap-card p-6 rounded-xl reveal ${isVisible ? "visible" : ""}`}
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 107, 53, 0.1)",
                transitionDelay: `${(i + 1) * 0.12}s`,
              }}
            >
              <div className="mb-4" style={{ color: "#ff6b35" }}>
                {item.icon}
              </div>
              <h3
                className="text-lg font-semibold mb-2"
                style={{ color: "#f5f0e8" }}
              >
                {item.title}
              </h3>
              <p
                className="text-sm leading-relaxed"
                style={{ color: "#8a857d", fontFamily: "'JetBrains Mono', monospace" }}
              >
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
