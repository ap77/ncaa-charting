import { useState } from "react";
import TeamSelector from "../components/TeamSelector";
import ModeSelector from "../components/ModeSelector";
import ConfidenceBar from "../components/ConfidenceBar";
import StatBreakdownTable from "../components/StatBreakdownTable";
import { fetchPrediction } from "../hooks/useApi";
import type { PredictionResponse } from "../types/api";

const CURRENT_SEASON = 2025;

interface HeadToHeadProps {
  mode: "safe" | "spicy";
  onModeChange: (mode: "safe" | "spicy") => void;
}

export default function HeadToHead({ mode, onModeChange }: HeadToHeadProps) {
  const [teamA, setTeamA] = useState("");
  const [teamB, setTeamB] = useState("");
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handlePredict() {
    if (!teamA || !teamB) {
      setError("Pick both teams first \u2014 Jen needs two to tango.");
      return;
    }
    if (teamA === teamB) {
      setError("Nice try \u2014 Jen needs two different teams to make a call.");
      return;
    }

    setError("");
    setLoading(true);
    setResult(null);

    try {
      const data = await fetchPrediction(teamA, teamB, CURRENT_SEASON, mode);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Jen ran into an issue. Try again!");
    } finally {
      setLoading(false);
    }
  }

  const isSpicy = mode === "spicy";

  return (
    <div className="max-w-3xl mx-auto">
      {/* Tournament context */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-extrabold text-white mb-2">
          Give Jen two teams. She'll pick the winner.
        </h2>
        <p className="text-base text-slate-400">
          She's crunched 17 years of March Madness data and has opinions about all of them.
        </p>
      </div>

      {/* Mode selector */}
      <div className="mb-8">
        <ModeSelector mode={mode} onChange={onModeChange} />
      </div>

      {/* Input section */}
      <div className={`rounded-2xl p-7 mb-8 transition-all duration-500 ${
        isSpicy
          ? "bg-orange-950/30 border border-orange-500/20"
          : "bg-slate-800/40 border border-slate-700/60"
      }`}>
        <div className="flex flex-col sm:flex-row gap-4 items-end mb-6">
          <TeamSelector label="Team 1" season={CURRENT_SEASON} value={teamA} onChange={setTeamA} />
          <div className="flex items-center justify-center sm:pb-1">
            <span className={`font-black text-3xl transition-colors duration-500 ${
              isSpicy ? "text-orange-500/60" : "text-slate-600"
            }`}>
              VS
            </span>
          </div>
          <TeamSelector label="Team 2" season={CURRENT_SEASON} value={teamB} onChange={setTeamB} />
        </div>

        <button
          onClick={handlePredict}
          disabled={loading || !teamA || !teamB}
          className={`w-full px-8 py-4 text-lg font-bold rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:bg-slate-700 disabled:text-slate-500 disabled:shadow-none ${
            isSpicy
              ? "bg-orange-500 hover:bg-orange-400 hover:shadow-[0_0_30px_rgba(234,88,12,0.3)] text-white focus:ring-orange-500"
              : "bg-emerald-500 hover:bg-emerald-400 hover:shadow-[0_0_30px_rgba(16,185,129,0.3)] text-white focus:ring-emerald-500"
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {isSpicy ? "Spicy Jen's cooking..." : "Jen's thinking..."}
            </span>
          ) : isSpicy ? (
            "Let Spicy Jen Pick \uD83C\uDF36\uFE0F"
          ) : (
            "Let Jen Pick \uD83C\uDFC6"
          )}
        </button>

        {error && (
          <div className="mt-4 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
            {error}
          </div>
        )}
      </div>

      {/* Result card */}
      {result && (
        <div className={`rounded-2xl overflow-hidden transition-all duration-500 ${
          isSpicy
            ? "bg-orange-950/20 border border-orange-500/30 shadow-[0_0_40px_rgba(234,88,12,0.1)]"
            : "bg-slate-800/40 border border-emerald-500/20 shadow-[0_0_40px_rgba(16,185,129,0.08)]"
        }`}>
          {/* Winner header */}
          <div className={`border-b p-8 text-center ${
            isSpicy
              ? "bg-orange-600/10 border-orange-500/20"
              : "bg-emerald-600/10 border-emerald-500/20"
          }`}>
            <p className="text-slate-400 text-sm uppercase tracking-widest mb-2">
              {isSpicy ? "Spicy Jen's Pick \uD83C\uDF36\uFE0F" : "\uD83C\uDFC6 Jen's Pick"}
            </p>
            <h2 className={`text-4xl font-black mb-2 ${isSpicy ? "text-orange-400" : "text-emerald-400"}`}>
              {result.winner}
            </h2>
            <p className="text-xl text-white font-semibold">
              {(result.confidence * 100).toFixed(1)}% confident
            </p>
            <p className="text-sm text-slate-500 mt-2">
              {isSpicy
                ? result.confidence >= 0.65
                  ? "The numbers don't lie. Pure hoops says this team is better."
                  : "Coin flip territory \u2014 but Spicy Jen doesn't back down."
                : result.confidence >= 0.85
                  ? "Jen's feeling really good about this one."
                  : result.confidence >= 0.65
                    ? "Jen likes this pick, but anything can happen in March."
                    : "This one's a toss-up \u2014 Jen's going with her gut."}
            </p>
          </div>

          <div className="p-7 space-y-7">
            <ConfidenceBar
              probA={result.win_probability_a}
              probB={result.win_probability_b}
              teamA={result.team_a}
              teamB={result.team_b}
              winner={result.winner}
            />

            {result.stat_breakdown && result.stat_breakdown.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                    {isSpicy ? "The tape don't lie" : "Why Jen picked this"}
                  </h4>
                  <span className="text-xs text-slate-600">Based on 2024\u201325 season stats</span>
                </div>
                <StatBreakdownTable
                  stats={result.stat_breakdown}
                  teamA={result.team_a}
                  teamB={result.team_b}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="text-center py-20 text-slate-600">
          <div className="text-6xl mb-5">{isSpicy ? "\uD83C\uDF36\uFE0F" : "\uD83C\uDFC0"}</div>
          <p className="text-xl font-medium">{isSpicy ? "Spicy Jen's ready to cause chaos" : "Jen's ready when you are"}</p>
          <p className="text-sm mt-2 text-slate-600">Pick two teams and let her do the rest</p>
        </div>
      )}
    </div>
  );
}
