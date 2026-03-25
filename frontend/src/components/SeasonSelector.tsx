interface SeasonSelectorProps {
  value: number;
  onChange: (season: number) => void;
}

export default function SeasonSelector({ value, onChange }: SeasonSelectorProps) {
  const seasons = Array.from({ length: 2025 - 2008 + 1 }, (_, i) => 2025 - i);

  return (
    <div>
      <label className="block text-sm font-medium text-slate-400 mb-1.5">Season</label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition appearance-none cursor-pointer"
      >
        {seasons.map((s) => (
          <option key={s} value={s}>
            {s - 1}-{String(s).slice(2)}
          </option>
        ))}
      </select>
    </div>
  );
}
