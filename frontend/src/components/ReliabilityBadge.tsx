interface ReliabilityBadgeProps {
  accuracy: number;
  reliability: "high" | "medium" | "low";
  label?: string;
  size?: "sm" | "md";
}

export default function ReliabilityBadge({ accuracy, reliability, label, size = "md" }: ReliabilityBadgeProps) {
  const pct = (accuracy * 100).toFixed(0);

  const colorMap = {
    high: {
      bg: "bg-emerald-500/15",
      border: "border-emerald-500/30",
      text: "text-emerald-400",
      dot: "bg-emerald-400",
    },
    medium: {
      bg: "bg-amber-500/15",
      border: "border-amber-500/30",
      text: "text-amber-400",
      dot: "bg-amber-400",
    },
    low: {
      bg: "bg-amber-500/15",
      border: "border-amber-500/30",
      text: "text-amber-400",
      dot: "bg-amber-400",
    },
  };

  const colors = colorMap[reliability];
  const isSmall = size === "sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 border rounded-full ${colors.bg} ${colors.border} ${colors.text} ${
        isSmall ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
      } font-medium`}
    >
      <span className={`inline-block rounded-full ${colors.dot} ${isSmall ? "w-1.5 h-1.5" : "w-2 h-2"}`} />
      {pct}% accuracy
      {label && !isSmall && <span className="text-slate-500 ml-1">- {label}</span>}
    </span>
  );
}
