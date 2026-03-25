interface ModeSelectorProps {
  mode: "safe" | "spicy";
  onChange: (mode: "safe" | "spicy") => void;
}

const MODES = {
  safe: {
    label: "Safe Jen",
    description:
      "Trusts the committee. Picks chalk. Has never once taken a risk in her life. Probably has Duke in the Final Four. (84.8% accurate)",
  },
  spicy: {
    label: "Spicy Jen \uD83C\uDF36\uFE0F",
    description:
      "Jen woke up and chose violence. Chaos is a feature, not a bug. \uD83C\uDF36\uFE0F (61.6% accurate)",
  },
};

export default function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  return (
    <div className="flex gap-2">
      {(["safe", "spicy"] as const).map((m) => {
        const info = MODES[m];
        const isActive = mode === m;
        return (
          <button
            key={m}
            onClick={() => onChange(m)}
            className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all duration-300 text-left ${
              isActive
                ? m === "safe"
                  ? "border-emerald-500 bg-emerald-500/10"
                  : "border-orange-500 bg-orange-500/10"
                : "border-slate-700 bg-slate-800/50 hover:border-slate-600"
            }`}
          >
            <span
              className={`font-bold text-sm block mb-1 ${
                isActive
                  ? m === "safe"
                    ? "text-emerald-400"
                    : "text-orange-400"
                  : "text-slate-400"
              }`}
            >
              {info.label}
            </span>
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
  );
}
