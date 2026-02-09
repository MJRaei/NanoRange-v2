"use client";

import { useEffect, useRef, useState } from "react";

const toolCategories = [
  {
    name: "Vision-Language Models",
    color: "#ff6b35",
    tools: [
      { name: "Gemini 3 Pro", desc: "Image enhancement, editing & reasoning" },
    ],
  },
  {
    name: "Preprocessing",
    color: "#ff8c5a",
    tools: [
      { name: "Denoising", desc: "Remove noise while preserving structure" },
      { name: "Contrast Enhancement", desc: "Improve visibility of features" },
      { name: "Filtering", desc: "Sharpen, smooth, or extract edges" },
    ],
  },
  {
    name: "Segmentation",
    color: "#ff6b35",
    tools: [
      { name: "Cellpose", desc: "Deep learning cell/particle segmentation" },
      { name: "Watershed", desc: "Region-based segmentation for touching objects" },
      { name: "Thresholding", desc: "Adaptive & global threshold methods" },
    ],
  },
  {
    name: "Analysis",
    color: "#ff8c5a",
    tools: [
      { name: "Morphological Ops", desc: "Erosion, dilation, opening, closing" },
      { name: "Measurements", desc: "Size, shape, area, perimeter" },
      { name: "Statistics", desc: "Distributions, histograms, CSV export" },
    ],
  },
];

export function Toolbox() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [hoveredTool, setHoveredTool] = useState<string | null>(null);

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

  let chipIndex = 0;

  return (
    <section ref={sectionRef} className="px-6 py-16 md:py-24">
      <div className="max-w-4xl mx-auto">
        {/* Section title */}
        <h2
          className={`text-2xl md:text-3xl font-semibold text-center mb-4 reveal ${isVisible ? "visible" : ""}`}
          style={{ color: "#c4b8a8" }}
        >
          Comprehensive Toolbox
        </h2>
        <p
          className={`text-center text-sm mb-14 reveal stagger-1 ${isVisible ? "visible" : ""}`}
          style={{ color: "#6a655d", fontFamily: "'JetBrains Mono', monospace" }}
        >
          Add a new tool by just writing a function — no core changes needed
        </p>

        {/* Tool categories grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {toolCategories.map((category, catIndex) => (
            <div
              key={category.name}
              className={`tool-category rounded-xl p-5 reveal ${isVisible ? "visible" : ""}`}
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 107, 53, 0.08)",
                transitionDelay: `${catIndex * 0.1}s`,
              }}
            >
              {/* Category header */}
              <h3
                className="text-sm font-semibold mb-4 uppercase tracking-wider"
                style={{ color: category.color, opacity: 0.8 }}
              >
                {category.name}
              </h3>

              {/* Tool chips */}
              <div className="flex flex-wrap gap-2">
                {category.tools.map((tool) => {
                  const idx = chipIndex++;
                  const isHovered = hoveredTool === `${category.name}-${tool.name}`;
                  return (
                    <div
                      key={tool.name}
                      className={`tool-chip rounded-lg px-3 py-2 reveal ${isVisible ? "visible" : ""}`}
                      style={{
                        backgroundColor: "rgba(255, 107, 53, 0.06)",
                        border: "1px solid rgba(255, 107, 53, 0.12)",
                        transitionDelay: `${(catIndex * 0.1) + (idx * 0.03)}s`,
                      }}
                      onMouseEnter={() => setHoveredTool(`${category.name}-${tool.name}`)}
                      onMouseLeave={() => setHoveredTool(null)}
                    >
                      <span
                        className="text-sm font-medium"
                        style={{ color: "#f5f0e8" }}
                      >
                        {tool.name}
                      </span>
                      {/* Tooltip on hover */}
                      <div
                        className="overflow-hidden transition-all duration-200"
                        style={{
                          maxHeight: isHovered ? "30px" : "0px",
                          opacity: isHovered ? 1 : 0,
                        }}
                      >
                        <p
                          className="text-xs mt-1"
                          style={{
                            color: "#8a857d",
                            fontFamily: "'JetBrains Mono', monospace",
                          }}
                        >
                          {tool.desc}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
