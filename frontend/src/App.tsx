import { useState } from "react";
import HeadToHead from "./pages/HeadToHead";

type Mode = "safe" | "spicy";

export default function App() {
  const [mode, setMode] = useState<Mode>("safe");

  const isSpicy = mode === "spicy";

  return (
    <div
      className="min-h-screen text-white transition-colors duration-700 ease-in-out"
      style={{
        backgroundColor: isSpicy ? "#1a0f00" : "#0f172a",
      }}
    >
      {/* Warm overlay for spicy mode */}
      <div
        className="fixed inset-0 pointer-events-none transition-opacity duration-700 ease-in-out"
        style={{
          background: "radial-gradient(ellipse at top, rgba(234,88,12,0.08) 0%, transparent 70%)",
          opacity: isSpicy ? 1 : 0,
        }}
      />

      {/* Header */}
      <header
        className={`border-b backdrop-blur-sm sticky top-0 z-40 transition-colors duration-700 ${
          isSpicy
            ? "border-orange-900/50 bg-[#1a0f00]/95"
            : "border-slate-800 bg-slate-900/95"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                <span className={`transition-colors duration-700 ${isSpicy ? "text-orange-400" : "text-emerald-400"}`}>
                  Jen-erate
                </span>{" "}
                <span className="text-white">the Winner</span>
              </h1>
              <p className={`text-xs -mt-0.5 transition-colors duration-700 ${isSpicy ? "text-orange-400/50" : "text-slate-500"}`}>
                {isSpicy ? "Spicy Jen\u2019s 2025\u201326 NCAA Tournament Picks \uD83C\uDF36\uFE0F" : "Jen\u2019s 2025\u201326 NCAA Tournament Picks"}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <HeadToHead mode={mode} onModeChange={setMode} />
      </main>

      {/* Footer */}
      <footer className={`relative z-10 border-t py-4 mt-auto transition-colors duration-700 ${isSpicy ? "border-orange-900/30" : "border-slate-800"}`}>
        <p className="text-center text-xs text-slate-600">
          Jen-erate the Winner — Jen's been studying 17 seasons of tournament data so you don't have to. Picks are for fun, not for Vegas.
        </p>
      </footer>
    </div>
  );
}
