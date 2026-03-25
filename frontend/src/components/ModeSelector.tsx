interface ModeSelectorProps {
  mode: "safe" | "spicy";
  onChange: (mode: "safe" | "spicy") => void;
}

const MODES = {
  safe: {
    label: "Safe Jen",
    accuracy: "84.8%",
    emoji: "",
    color: "emerald",
    description:
      "Trusts the committee. Uses seeds, win totals, and strength of schedule \u2014 because 30 analysts spent all season watching these teams so you don't have to. Picks chalk. Borderline psychic. Probably has Duke in the Final Four.",
  },
  spicy: {
    label: "Spicy Jen",
    accuracy: "61.6%",
    emoji: "\uD83C\uDF36\uFE0F",
    color: "orange",
    description:
      "Doesn\u2019t care about your seed. Doesn\u2019t care about how many wins you padded against cupcakes. Doesn\u2019t care what the committee thinks. Only looks at what happens on the court \u2014 efficiency, tempo, turnovers, free throws, rebounding. Pure basketball. Wrong 40% of the time but those picks hit different. Chaos is a feature, not a bug. \uD83C\uDF36\uFE0F",
  },
};

export default function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {(["safe", "spicy"] as const).map((m) => {
          const info = MODES[m];
          const isActive = mode === m;
          return (
            <button
              key={m}
              onClick={() => onChange(m)}
              className={`flex-1 px-4 py-3 rounded-lg border-2 transition text-left ${
                isActive
                  ? m === "safe"
                    ? "border-emerald-500 bg-emerald-500/10"
                    : "border-orange-500 bg-orange-500/10"
                  : "border-slate-700 bg-slate-800/50 hover:border-slate-600"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`font-bold text-sm ${
                    isActive
                      ? m === "safe"
                        ? "text-emerald-400"
                        : "text-orange-400"
                      : "text-slate-400"
                  }`}
                >
                  {info.emoji} {info.label}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    isActive
                      ? m === "safe"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-orange-500/20 text-orange-400"
                      : "bg-slate-700 text-slate-500"
                  }`}
                >
                  {info.accuracy} accurate
                </span>
              </div>
              <p
                className={`text-xs leading-relaxed ${
                  isActive ? "text-slate-300" : "text-slate-600"
                }`}
              >
                {info.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
