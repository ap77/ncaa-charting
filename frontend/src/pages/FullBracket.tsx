import { useState } from "react";
import { fetchBracket } from "../hooks/useApi";
import type { BracketResponse, MatchupResult } from "../types/api";
import ModeSelector from "../components/ModeSelector";
import ReliabilityBanner from "../components/ReliabilityBanner";
import ReliabilityBadge from "../components/ReliabilityBadge";
import MatchupCard from "../components/MatchupCard";
import MatchupModal from "../components/MatchupModal";

const ROUND_DISPLAY: Record<string, string> = {
  R64: "Round of 64",
  R32: "Round of 32",
  S16: "Sweet 16",
  E8: "Elite 8",
  F4: "Final Four",
  Championship: "Championship",
};

const REGION_ROUNDS = ["R64", "R32", "S16", "E8"] as const;

const CURRENT_SEASON = 2025;

interface FullBracketProps {
  mode: "safe" | "spicy";
  onModeChange: (mode: "safe" | "spicy") => void;
}

export default function FullBracket({ mode, onModeChange }: FullBracketProps) {
  const season = CURRENT_SEASON;
  const [bracket, setBracket] = useState<BracketResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedMatchup, setSelectedMatchup] = useState<{
    matchup: MatchupResult;
    reliability: "high" | "medium" | "low";
  } | null>(null);

  const isSpicy = mode === "spicy";

  async function handleSimulate() {
    setError("");
    setLoading(true);
    setBracket(null);

    try {
      const data = await fetchBracket(season, mode);
      setBracket(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to simulate bracket");
    } finally {
      setLoading(false);
    }
  }

  function getReliability(roundKey: string): "high" | "medium" | "low" {
    if (!bracket?.model_reliability) return "high";
    const acc = bracket.model_reliability[roundKey]?.historical_accuracy;
    if (acc == null) return "high";
    if (acc >= 0.80) return "high";
    if (acc >= 0.70) return "medium";
    return "low";
  }

  function getAccuracy(roundKey: string): number | null {
    return bracket?.model_reliability?.[roundKey]?.historical_accuracy ?? null;
  }

  return (
    <div>
      {/* Mode selector */}
      <div className="mb-5">
        <ModeSelector mode={mode} onChange={onModeChange} />
      </div>

      {/* Header + simulate button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {isSpicy ? "Spicy Jen's Full 2025–26 Bracket \uD83C\uDF36\uFE0F" : "Jen's Full 2025–26 Bracket"}
          </h2>
          <p className="text-sm text-slate-400">
            {isSpicy
              ? "Seeds are just numbers. Let the on-court stats decide everything."
              : "Every game, every round — Jen fills out the whole thing so you can argue about it."}
          </p>
        </div>
        <button
          onClick={handleSimulate}
          disabled={loading}
          className={`px-8 py-3 font-semibold rounded-lg transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 ${
            isSpicy
              ? "bg-orange-600 hover:bg-orange-500 disabled:bg-slate-700 disabled:text-slate-500 text-white focus:ring-orange-500"
              : "bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white focus:ring-emerald-500"
          }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {isSpicy ? "Spicy Jen's causing chaos..." : "Jen's filling it out..."}
            </span>
          ) : isSpicy ? (
            "Let Spicy Jen Fill the Bracket \uD83C\uDF36\uFE0F"
          ) : (
            "Let Jen Fill the Bracket"
          )}
        </button>
      </div>

      {error && (
        <div className="mb-6 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
          {error}
        </div>
      )}

      {bracket && (
        <div>
          <ReliabilityBanner />

          {/* Reliability legend */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mb-6">
            <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Model Accuracy by Round
            </h4>
            <div className="flex flex-wrap gap-3">
              {Object.keys(ROUND_DISPLAY).map((key) => {
                const acc = getAccuracy(key);
                if (acc == null) return null;
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{ROUND_DISPLAY[key]}:</span>
                    <ReliabilityBadge
                      accuracy={acc}
                      reliability={getReliability(key)}
                      size="sm"
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Champion */}
          {bracket.champion && (
            <div className="bg-gradient-to-r from-emerald-600/20 via-emerald-500/10 to-emerald-600/20 border border-emerald-500/30 rounded-xl p-6 mb-6 text-center">
              <p className="text-emerald-400/70 text-sm uppercase tracking-widest mb-1">
                Jen's Champion
              </p>
              <h2 className="text-4xl font-bold text-emerald-400 mb-1">
                {bracket.champion.name}
              </h2>
              <p className="text-slate-400">#{bracket.champion.seed} seed</p>
            </div>
          )}

          {/* Regional brackets */}
          {Object.entries(bracket.regions).map(([regionName, region]) => (
            <div key={regionName} className="mb-8">
              <h3 className="text-lg font-bold text-white mb-4 border-b border-slate-700 pb-2">
                {regionName} Region
              </h3>
              <div className="overflow-x-auto pb-4">
                <div className="flex gap-4 min-w-max">
                  {REGION_ROUNDS.map((roundKey) => {
                    const games = region.rounds[roundKey] || [];
                    if (games.length === 0) return null;
                    const reliability = getReliability(roundKey);
                    const acc = getAccuracy(roundKey);
                    const isLow = reliability === "low" || reliability === "medium";

                    return (
                      <div key={roundKey} className="flex-shrink-0 w-52">
                        {/* Round header */}
                        <div
                          className={`rounded-t-lg p-3 border-b-2 mb-3 ${
                            isLow
                              ? "bg-amber-500/10 border-amber-500/40"
                              : "bg-slate-800/80 border-emerald-500/30"
                          }`}
                        >
                          <h4
                            className={`text-sm font-bold mb-1 ${
                              isLow ? "text-amber-300" : "text-white"
                            }`}
                          >
                            {ROUND_DISPLAY[roundKey]}
                          </h4>
                          {acc != null && (
                            <ReliabilityBadge accuracy={acc} reliability={reliability} size="sm" />
                          )}
                          {isLow && (
                            <div className="mt-1.5 flex items-center gap-1">
                              <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                  fillRule="evenodd"
                                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              <span className="text-xs text-amber-400/80">Low reliability</span>
                            </div>
                          )}
                        </div>

                        {/* Matchups */}
                        <div className="space-y-2">
                          {games.map((game) => (
                            <MatchupCard
                              key={game.game_number}
                              matchup={game}
                              reliability={reliability}
                              onClick={() => setSelectedMatchup({ matchup: game, reliability })}
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}

          {/* Final Four + Championship */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-white mb-4 border-b border-slate-700 pb-2">
              Final Four & Championship
            </h3>
            <div className="overflow-x-auto pb-4">
              <div className="flex gap-6 min-w-max justify-center">
                {/* Final Four */}
                {bracket.final_four && bracket.final_four.games.length > 0 && (
                  <div className="flex-shrink-0 w-56">
                    <div className="rounded-t-lg p-3 border-b-2 mb-3 bg-amber-500/10 border-amber-500/40">
                      <h4 className="text-sm font-bold mb-1 text-amber-300">Final Four</h4>
                      {getAccuracy("F4") != null && (
                        <ReliabilityBadge accuracy={getAccuracy("F4")!} reliability={getReliability("F4")} size="sm" />
                      )}
                      <div className="mt-1.5 flex items-center gap-1">
                        <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-xs text-amber-400/80">Low reliability</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {bracket.final_four.games.map((game) => (
                        <MatchupCard
                          key={game.game_number}
                          matchup={game}
                          reliability={getReliability("F4")}
                          onClick={() => setSelectedMatchup({ matchup: game, reliability: getReliability("F4") })}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Championship */}
                {bracket.championship && (
                  <div className="flex-shrink-0 w-56">
                    <div className="rounded-t-lg p-3 border-b-2 mb-3 bg-amber-500/10 border-amber-500/40">
                      <h4 className="text-sm font-bold mb-1 text-amber-300">Championship</h4>
                      {getAccuracy("Championship") != null && (
                        <ReliabilityBadge
                          accuracy={getAccuracy("Championship")!}
                          reliability={getReliability("Championship")}
                          size="sm"
                        />
                      )}
                      <div className="mt-1.5 flex items-center gap-1">
                        <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-xs text-amber-400/80">Coin flip territory</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <MatchupCard
                        matchup={bracket.championship.game}
                        reliability={getReliability("Championship")}
                        onClick={() =>
                          setSelectedMatchup({
                            matchup: bracket.championship.game,
                            reliability: getReliability("Championship"),
                          })
                        }
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!bracket && !loading && !error && (
        <div className="text-center py-16 text-slate-600">
          <svg className="w-16 h-16 mx-auto mb-4 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
            />
          </svg>
          <p className="text-lg">Jen's got a bracket with your name on it</p>
          <p className="text-sm mt-1">Hit the button and let her fill in all 63 games</p>
        </div>
      )}

      {/* Matchup detail modal */}
      {selectedMatchup && (
        <MatchupModal
          matchup={selectedMatchup.matchup}
          reliability={selectedMatchup.reliability}
          onClose={() => setSelectedMatchup(null)}
        />
      )}
    </div>
  );
}
