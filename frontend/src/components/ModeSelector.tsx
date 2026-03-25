interface ModeSelectorProps {
  mode: "safe" | "spicy";
  onChange: (mode: "safe" | "spicy") => void;
}

const MODES = {
  safe: {
    label: "Safe Jen \uD83C\uDFC6",
    accuracy: "84.8%",
    description:
      "Trusts the committee. Trusts the seeds. Picks chalk. Has never once taken a risk in her life. Probably has Duke in the Final Four.",
  },
  spicy: {
    label: "Spicy Jen \uD83C\uDF36\uFE0F",
    accuracy: "61.6%",
    description:
      "Doesn\u2019t care about your seed. Doesn\u2019t care about your r\u00e9sum\u00e9. Only cares about what happens on the court. Chaos is a feature, not a bug.",
  },
};

export default function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="flex gap-3">
      {(["safe", "spicy"] as const).map((m) => {
        const info = MODES[m];
        const isActive = mode === m;
        return (
          <button
            key={m}
            onClick={() => onChange(m)}
            className={`flex-1 px-5 py-4 rounded-xl border-2 transition-all duration-300 text-left ${
              isActive
                ? m === "safe"
                  ? "border-emerald-400 bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.15)]"
                  : "border-orange-400 bg-orange-500/15 shadow-[0_0_24px_rgba(234,88,12,0.2)]"
                : "border-slate-700/60 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/50"
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span
                className={`font-extrabold text-base ${
                  isActive
                    ? m === "safe"
                      ? "text-emerald-400"
                      : "text-orange-400"
                    : "text-slate-500"
                }`}
              >
                {info.label}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  isActive
                    ? m === "safe"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "bg-orange-500/20 text-orange-400"
                    : "bg-slate-700/50 text-slate-500"
                }`}
              >
                {info.accuracy} accurate
              </span>
            </div>
            <p
              className={`text-sm leading-relaxed ${
                isActive ? "text-slate-300" : "text-slate-600"
              }`}
            >
              {info.description}
            </p>
          </button>
        );
      })}
    </div>
  );
}
