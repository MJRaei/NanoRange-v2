const steps = [
  {
    number: 1,
    title: "Upload",
    description: "Drop your TEM or SEM microscopy images",
  },
  {
    number: 2,
    title: "Describe",
    description: "Tell the AI what analysis you need",
  },
  {
    number: 3,
    title: "Results",
    description: "Get annotated images and CSV data",
  },
];

export function HowItWorks() {
  return (
    <section className="px-6 py-16 md:py-24">
      <div className="max-w-4xl mx-auto">
        {/* Section title */}
        <h2
          className="text-2xl md:text-3xl font-semibold text-center mb-16"
          style={{ color: "#c4b8a8" }}
        >
          How It Works
        </h2>

        {/* Timeline - horizontal on desktop, vertical on mobile */}
        <div className="relative">
          {/* Desktop horizontal timeline */}
          <div className="hidden md:block">
            {/* Connecting line */}
            <div
              className="absolute top-6 left-[15%] right-[15%] h-px"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg, #ff6b35 0, #ff6b35 8px, transparent 8px, transparent 16px)",
                opacity: 0.4,
              }}
            />

            <div className="flex justify-between">
              {steps.map((step) => (
                <div
                  key={step.number}
                  className="flex flex-col items-center text-center w-1/3"
                >
                  {/* Step number circle */}
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold mb-4 relative z-10"
                    style={{
                      backgroundColor: "#0a0908",
                      border: "2px solid #ff6b35",
                      color: "#ff6b35",
                    }}
                  >
                    {step.number}
                  </div>

                  {/* Step title */}
                  <h3
                    className="text-lg font-semibold mb-2"
                    style={{ color: "#f5f0e8" }}
                  >
                    {step.title}
                  </h3>

                  {/* Step description */}
                  <p
                    className="text-sm max-w-[200px]"
                    style={{
                      color: "#8a857d",
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Mobile vertical timeline */}
          <div className="md:hidden">
            <div className="relative pl-8">
              {/* Vertical connecting line */}
              <div
                className="absolute left-[11px] top-6 bottom-6 w-px"
                style={{
                  backgroundImage:
                    "repeating-linear-gradient(180deg, #ff6b35 0, #ff6b35 8px, transparent 8px, transparent 16px)",
                  opacity: 0.4,
                }}
              />

              {steps.map((step, index) => (
                <div
                  key={step.number}
                  className={`relative flex items-start gap-6 ${
                    index !== steps.length - 1 ? "pb-10" : ""
                  }`}
                >
                  {/* Step number circle */}
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 relative z-10"
                    style={{
                      backgroundColor: "#0a0908",
                      border: "2px solid #ff6b35",
                      color: "#ff6b35",
                      marginLeft: "-12px",
                    }}
                  >
                    {step.number}
                  </div>

                  <div>
                    {/* Step title */}
                    <h3
                      className="text-base font-semibold mb-1"
                      style={{ color: "#f5f0e8" }}
                    >
                      {step.title}
                    </h3>

                    {/* Step description */}
                    <p
                      className="text-sm"
                      style={{
                        color: "#8a857d",
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                    >
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
