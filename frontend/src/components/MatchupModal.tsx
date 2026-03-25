import type { MatchupResult } from "../types/api";
import ConfidenceBar from "./ConfidenceBar";
import StatBreakdownTable from "./StatBreakdownTable";

interface MatchupModalProps {
  matchup: MatchupResult;
  reliability: "high" | "medium" | "low";
  onClose: () => void;
}

export default function MatchupModal({ matchup, reliability, onClose }: MatchupModalProps) {
  const isLowReliability = reliability === "low" || reliability === "medium";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Matchup Details</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Reliability warning */}
          {isLowReliability && (
            <div className="bg-amber-500/10 border border-amber-500/25 rounded-lg px-3 py-2 flex items-center gap-2">
              <svg className="w-4 h-4 text-amber-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-amber-300 text-sm">
                This is a late-round prediction with lower model accuracy. Treat as an informed guess.
              </span>
            </div>
          )}

          {/* Teams & winner */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-4 mb-3">
              <div className="text-right flex-1">
                <span className="text-xs text-slate-500">({matchup.team_a.seed})</span>{" "}
                <span
                  className={`text-lg ${
                    matchup.predicted_winner.name === matchup.team_a.name
                      ? "text-emerald-400 font-bold"
                      : "text-slate-400"
                  }`}
                >
                  {matchup.team_a.name}
                </span>
              </div>
              <span className="text-slate-600 text-sm font-medium">vs</span>
              <div className="text-left flex-1">
                <span
                  className={`text-lg ${
                    matchup.predicted_winner.name === matchup.team_b.name
                      ? "text-emerald-400 font-bold"
                      : "text-slate-400"
                  }`}
                >
                  {matchup.team_b.name}
                </span>{" "}
                <span className="text-xs text-slate-500">({matchup.team_b.seed})</span>
              </div>
            </div>

            <ConfidenceBar
              probA={matchup.team_a.win_probability}
              probB={matchup.team_b.win_probability}
              teamA={matchup.team_a.name}
              teamB={matchup.team_b.name}
              winner={matchup.predicted_winner.name}
            />
          </div>

          {/* Stat breakdown */}
          {matchup.stat_breakdown && matchup.stat_breakdown.length > 0 && (
            <StatBreakdownTable
              stats={matchup.stat_breakdown}
              teamA={matchup.team_a.name}
              teamB={matchup.team_b.name}
            />
          )}
        </div>
      </div>
    </div>
  );
}
