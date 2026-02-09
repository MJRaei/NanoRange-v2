"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";

const demos = [
  {
    title: "Interactive Canvas",
    description: "Visualize, annotate, and process microscopy images in real time",
    src: "/demo_canvas.gif",
    alt: "Demo of the NanoRange canvas interface",
  },
  {
    title: "AI Chat",
    description: "Describe your analysis in natural language and let agents handle the rest",
    src: "/demo_chat.gif",
    alt: "Demo of the NanoRange chat interface",
  },
];

export function DemoShowcase() {
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
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="px-6 py-16 md:py-24">
      <div className="max-w-5xl mx-auto">
        <h2
          className={`text-2xl md:text-3xl font-semibold text-center mb-4 reveal ${isVisible ? "visible" : ""}`}
          style={{ color: "#c4b8a8" }}
        >
          See It in Action
        </h2>
        <p
          className={`text-center text-sm mb-14 reveal stagger-1 ${isVisible ? "visible" : ""}`}
          style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
        >
          From conversation to results — no configuration required
        </p>

        <div className="flex flex-col gap-12">
          {demos.map((demo, i) => (
            <div
              key={demo.title}
              className={`reveal ${isVisible ? "visible" : ""}`}
              style={{ transitionDelay: `${i * 0.2}s` }}
            >
              <h3
                className="text-base font-semibold mb-1"
                style={{ color: "#f5f0e8" }}
              >
                {demo.title}
              </h3>
              <p
                className="text-xs mb-4"
                style={{
                  color: "#8a857d",
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {demo.description}
              </p>
              <div
                className="rounded-xl overflow-hidden"
                style={{
                  border: "1px solid rgba(255, 107, 53, 0.35)",
                  boxShadow: "0 0 20px rgba(255, 107, 53, 0.08)",
                  backgroundColor: "#111",
                }}
              >
                <div className="relative w-full" style={{ aspectRatio: "16 / 10" }}>
                  <Image
                    src={demo.src}
                    alt={demo.alt}
                    fill
                    unoptimized
                    className="object-contain"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
