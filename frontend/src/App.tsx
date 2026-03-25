import { useState } from "react";
import HeadToHead from "./pages/HeadToHead";
import FullBracket from "./pages/FullBracket";

type Tab = "h2h" | "bracket";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("h2h");

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                <span className="text-emerald-400">Jen-erate</span>{" "}
                <span className="text-white">the Winner</span>
              </h1>
              <p className="text-xs text-slate-500 -mt-0.5">Jen's 2025–26 NCAA Tournament Picks</p>
            </div>

            {/* Tab navigation */}
            <nav className="flex gap-1 bg-slate-800 rounded-lg p-1">
              <button
                onClick={() => setActiveTab("h2h")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                  activeTab === "h2h"
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-700"
                }`}
              >
                Head-to-Head
              </button>
              <button
                onClick={() => setActiveTab("bracket")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                  activeTab === "bracket"
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-700"
                }`}
              >
                Jen's Full Bracket
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "h2h" ? <HeadToHead /> : <FullBracket />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 mt-auto">
        <p className="text-center text-xs text-slate-600">
          Jen-erate the Winner — Jen's been studying 17 seasons of tournament data so you don't have to. Picks are for fun, not for Vegas.
        </p>
      </footer>
    </div>
  );
}
