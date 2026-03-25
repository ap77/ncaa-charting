import type { TeamListItem, PredictionResponse, BracketResponse } from "../types/api";

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function fetchTeams(season: number, query: string): Promise<TeamListItem[]> {
  if (!query || query.length < 2) return [];
  const res = await fetch(`${API_BASE}/api/teams?season=${season}&q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Failed to fetch teams");
  return res.json();
}

export async function fetchPrediction(teamA: string, teamB: string, season: number, mode: string = "safe"): Promise<PredictionResponse> {
  const res = await fetch(`${API_BASE}/api/predictions/matchup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team_a: teamA, team_b: teamB, season, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Prediction failed" }));
    throw new Error(err.detail || "Prediction failed");
  }
  return res.json();
}

export async function fetchBracket(season: number, mode: string = "safe"): Promise<BracketResponse> {
  const res = await fetch(`${API_BASE}/api/bracket/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Bracket simulation failed" }));
    throw new Error(err.detail || "Bracket simulation failed");
  }
  return res.json();
}
