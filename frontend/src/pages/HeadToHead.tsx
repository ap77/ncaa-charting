import { useState } from "react";
import TeamSelector from "../components/TeamSelector";
import ConfidenceBar from "../components/ConfidenceBar";
import StatBreakdownTable from "../components/StatBreakdownTable";
import { fetchPrediction } from "../hooks/useApi";
import type { PredictionResponse } from "../types/api";

const CURRENT_SEASON = 2025;

export default function HeadToHead() {
  const [teamA, setTeamA] = useState("");
  const [teamB, setTeamB] = useState("");
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handlePredict() {
    if (!teamA || !teamB) {
      setError("Pick both teams first — Jen needs two to tango.");
      return;
    }
    if (teamA === teamB) {
      setError("Nice try — Jen needs two different teams to make a call.");
      return;
    }

    setError("");
    setLoading(true);
    setResult(null);

    try {
      const data = await fetchPrediction(teamA, teamB, CURRENT_SEASON);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Jen ran into an issue. Try again!");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Tournament context */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-1">
          Give Jen two teams. She'll pick the winner.
        </h2>
        <p className="text-sm text-slate-400">
          She's crunched 17 years of March Madness data and has opinions about all of them.
        </p>
      </div>

      {/* Input section */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
        <div className="flex flex-col sm:flex-row gap-4 mb-5">
          <TeamSelector label="Team 1" season={CURRENT_SEASON} value={teamA} onChange={setTeamA} />
          <div className="flex items-end justify-center pb-1">
            <span className="text-slate-500 font-bold text-xl">vs</span>
          </div>
          <TeamSelector label="Team 2" season={CURRENT_SEASON} value={teamB} onChange={setTeamB} />
        </div>

        <button
          onClick={handlePredict}
          disabled={loading || !teamA || !teamB}
          className="w-full px-8 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold rounded-lg transition focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Jen's thinking...
            </span>
          ) : (
            "Let Jen Pick"
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
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
          {/* Winner header */}
          <div className="bg-emerald-600/10 border-b border-emerald-500/20 p-6 text-center">
            <p className="text-slate-400 text-sm uppercase tracking-wider mb-1">Jen's Pick</p>
            <h2 className="text-3xl font-bold text-emerald-400 mb-2">{result.winner}</h2>
            <p className="text-xl text-white font-semibold">
              {(result.confidence * 100).toFixed(1)}% confident
            </p>
            <p className="text-sm text-slate-500 mt-1">
              {result.confidence >= 0.85
                ? "Jen's feeling really good about this one."
                : result.confidence >= 0.65
                  ? "Jen likes this pick, but anything can happen in March."
                  : "This one's a toss-up — Jen's going with her gut."}
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* Probability bar */}
            <ConfidenceBar
              probA={result.win_probability_a}
              probB={result.win_probability_b}
              teamA={result.team_a}
              teamB={result.team_b}
              winner={result.winner}
            />

            {/* Stat breakdown */}
            {result.stat_breakdown && result.stat_breakdown.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                    Why Jen picked this
                  </h4>
                  <span className="text-xs text-slate-600">Based on 2024–25 season stats</span>
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
        <div className="text-center py-16 text-slate-600">
          <div className="text-5xl mb-4">&#127936;</div>
          <p className="text-lg">Jen's ready when you are</p>
          <p className="text-sm mt-1">Pick two teams and let her do the rest</p>
        </div>
      )}
    </div>
  );
}
