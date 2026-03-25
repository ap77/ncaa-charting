import type { MatchupResult } from "../types/api";

interface MatchupCardProps {
  matchup: MatchupResult;
  reliability: "high" | "medium" | "low";
  onClick: () => void;
}

export default function MatchupCard({ matchup, reliability, onClick }: MatchupCardProps) {
  const isLowReliability = reliability === "low" || reliability === "medium";
  const winnerName = matchup.predicted_winner.name;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg border transition hover:scale-[1.02] hover:shadow-lg cursor-pointer p-2.5 ${
        isLowReliability
          ? "bg-slate-800/60 border-amber-500/20 hover:border-amber-500/40"
          : "bg-slate-800 border-slate-700 hover:border-slate-600"
      }`}
    >
      {/* Team A */}
      <div
        className={`flex items-center justify-between gap-2 py-1 px-1.5 rounded ${
          winnerName === matchup.team_a.name ? "bg-emerald-500/10" : ""
        }`}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-500 w-4 text-right flex-shrink-0">{matchup.team_a.seed}</span>
          <span
            className={`text-sm truncate ${
              winnerName === matchup.team_a.name ? "text-emerald-400 font-semibold" : "text-slate-400"
            }`}
          >
            {matchup.team_a.name}
          </span>
        </div>
        {winnerName === matchup.team_a.name && (
          <svg className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>

      {/* Team B */}
      <div
        className={`flex items-center justify-between gap-2 py-1 px-1.5 rounded ${
          winnerName === matchup.team_b.name ? "bg-emerald-500/10" : ""
        }`}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-slate-500 w-4 text-right flex-shrink-0">{matchup.team_b.seed}</span>
          <span
            className={`text-sm truncate ${
              winnerName === matchup.team_b.name ? "text-emerald-400 font-semibold" : "text-slate-400"
            }`}
          >
            {matchup.team_b.name}
          </span>
        </div>
        {winnerName === matchup.team_b.name && (
          <svg className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>

      {/* Confidence */}
      <div className="mt-1.5 flex items-center justify-between px-1.5">
        <span
          className={`text-xs ${
            isLowReliability ? "text-amber-400/70" : "text-slate-500"
          }`}
        >
          {(matchup.confidence * 100).toFixed(0)}% conf.
        </span>
        {isLowReliability && (
          <svg className="w-3.5 h-3.5 text-amber-400/60" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>
    </button>
  );
}
