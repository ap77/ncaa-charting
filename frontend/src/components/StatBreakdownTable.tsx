import { useState } from "react";
import type { StatBreakdown } from "../types/api";

interface StatBreakdownTableProps {
  stats: StatBreakdown[];
  teamA: string;
  teamB: string;
}

export default function StatBreakdownTable({ stats, teamA, teamB }: StatBreakdownTableProps) {
  const [showAll, setShowAll] = useState(false);
  const sorted = [...stats].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));
  const displayed = showAll ? sorted : sorted.slice(0, 5);

  const maxImpact = Math.max(...sorted.map((s) => Math.abs(s.impact)), 0.01);

  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Stat Breakdown
      </h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-500 border-b border-slate-700">
              <th className="text-left py-2 px-2 font-medium">Stat</th>
              <th className="text-right py-2 px-2 font-medium">{teamA}</th>
              <th className="text-right py-2 px-2 font-medium">{teamB}</th>
              <th className="py-2 px-2 font-medium text-center w-40">Impact</th>
              <th className="text-center py-2 px-2 font-medium">Favors</th>
            </tr>
          </thead>
          <tbody>
            {displayed.map((s, i) => {
              const pct = (Math.abs(s.impact) / maxImpact) * 100;
              const favorsA = s.favors === teamA;
              return (
                <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50 transition">
                  <td className="py-2.5 px-2 text-slate-300 font-medium">{s.stat}</td>
                  <td className="py-2.5 px-2 text-right text-white tabular-nums">
                    {s.team_a_value != null ? Number(s.team_a_value).toFixed(2) : "—"}
                  </td>
                  <td className="py-2.5 px-2 text-right text-white tabular-nums">
                    {s.team_b_value != null ? Number(s.team_b_value).toFixed(2) : "—"}
                  </td>
                  <td className="py-2.5 px-2">
                    <div className="flex items-center justify-center">
                      <div className="w-full bg-slate-700 rounded-full h-2 relative">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            favorsA ? "bg-emerald-500" : "bg-blue-500"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                        favorsA
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {s.favors}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {sorted.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-3 text-sm text-emerald-400 hover:text-emerald-300 transition font-medium"
        >
          {showAll ? "Show top 5" : `Show all ${sorted.length} stats`}
        </button>
      )}
    </div>
  );
}
