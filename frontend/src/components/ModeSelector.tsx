interface ModeSelectorProps {
  mode: "safe" | "spicy";
  onChange: (mode: "safe" | "spicy") => void;
}

const MODES = {
  safe: {
    label: "\uD83C\uDFC6 Safe Jen",
    description:
      "Trusts the committee. Picks chalk. Has never once taken a risk in her life. Probably has Duke in the Final Four. (84.8% accurate)",
  },
  spicy: {
    label: "\uD83C\uDF36\uFE0F Spicy Jen",
    description:
      "Jen woke up and chose violence. Chaos is a feature, not a bug. \uD83C\uDF36\uFE0F (61.6% accurate)",
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
            <span
              className={`font-extrabold text-base block mb-1.5 ${
                isActive
                  ? m === "safe"
                    ? "text-emerald-400"
                    : "text-orange-400"
                  : "text-slate-500"
              }`}
            >
              {info.label}
            </span>
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
