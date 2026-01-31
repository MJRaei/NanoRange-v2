"use client";

import { useEffect, useState } from "react";

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

interface ParticleBackgroundProps {
  particleCount?: number;
  showGrid?: boolean;
  showRadialGlow?: boolean;
}

export function ParticleBackground({
  particleCount = 20,
  showGrid = true,
  showRadialGlow = true,
}: ParticleBackgroundProps) {
  const [particles, setParticles] = useState<Particle[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setParticles(generateParticles(particleCount));
    setMounted(true);
  }, [particleCount]);

  return (
    <>
      {/* Grid overlay */}
      {showGrid && <div className="absolute inset-0 grid-overlay" />}

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
      {showRadialGlow && (
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full opacity-30 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, rgba(255, 107, 53, 0.2) 0%, transparent 70%)",
          }}
        />
      )}
    </>
  );
}
