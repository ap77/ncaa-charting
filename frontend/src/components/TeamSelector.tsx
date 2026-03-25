import { useState, useEffect, useRef } from "react";
import { fetchTeams } from "../hooks/useApi";
import type { TeamListItem } from "../types/api";

interface TeamSelectorProps {
  label: string;
  season: number;
  value: string;
  onChange: (team: string) => void;
}

export default function TeamSelector({ label, season, value, onChange }: TeamSelectorProps) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<TeamListItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleInputChange(val: string) {
    setQuery(val);
    onChange("");

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (val.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await fetchTeams(season, val);
        setSuggestions(results);
        setIsOpen(results.length > 0);
      } catch {
        setSuggestions([]);
        setIsOpen(false);
      } finally {
        setLoading(false);
      }
    }, 250);
  }

  function selectTeam(name: string) {
    setQuery(name);
    onChange(name);
    setIsOpen(false);
    setSuggestions([]);
  }

  return (
    <div ref={wrapperRef} className="relative flex-1">
      <label className="block text-sm font-medium text-slate-400 mb-1.5">{label}</label>
      <input
        type="text"
        value={query}
        onChange={(e) => handleInputChange(e.target.value)}
        onFocus={() => {
          if (suggestions.length > 0) setIsOpen(true);
        }}
        placeholder="Search team..."
        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
      />
      {loading && (
        <div className="absolute right-3 top-[38px]">
          <div className="w-5 h-5 border-2 border-slate-600 border-t-emerald-400 rounded-full animate-spin" />
        </div>
      )}
      {isOpen && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-h-60 overflow-auto">
          {suggestions.map((team) => (
            <li
              key={team.id}
              onClick={() => selectTeam(team.name)}
              className="px-4 py-2.5 cursor-pointer hover:bg-slate-700 text-white transition text-left"
            >
              {team.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
