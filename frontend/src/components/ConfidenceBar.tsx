interface ConfidenceBarProps {
  probA: number;
  probB: number;
  teamA: string;
  teamB: string;
  winner: string;
}

export default function ConfidenceBar({ probA, probB, teamA, teamB, winner }: ConfidenceBarProps) {
  const pctA = probA * 100;
  const pctB = probB * 100;

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm text-slate-400 mb-1.5">
        <span className={winner === teamA ? "text-emerald-400 font-semibold" : ""}>
          {teamA} {pctA.toFixed(1)}%
        </span>
        <span className={winner === teamB ? "text-emerald-400 font-semibold" : ""}>
          {pctB.toFixed(1)}% {teamB}
        </span>
      </div>
      <div className="flex h-3 rounded-full overflow-hidden bg-slate-700">
        <div
          className={`transition-all duration-500 ${
            winner === teamA ? "bg-emerald-500" : "bg-slate-500"
          }`}
          style={{ width: `${pctA}%` }}
        />
        <div
          className={`transition-all duration-500 ${
            winner === teamB ? "bg-emerald-500" : "bg-slate-500"
          }`}
          style={{ width: `${pctB}%` }}
        />
      </div>
    </div>
  );
}
