// Teams API
export interface TeamListItem {
  id: number;
  name: string;
}

// Prediction API
export interface StatBreakdown {
  stat: string;
  stat_key: string;
  impact: number;
  direction: number;
  team_a_value: number | null;
  team_b_value: number | null;
  delta: number;
  favors: string;
}

export interface PredictionResponse {
  winner: string;
  loser: string;
  confidence: number;
  team_a: string;
  team_b: string;
  win_probability_a: number;
  win_probability_b: number;
  mode: string;
  stat_breakdown: StatBreakdown[];
}

// Bracket API
export interface BracketTeam {
  name: string;
  seed: number;
}

export interface GameTeamDetail {
  name: string;
  seed: number;
  win_probability: number;
}

export interface MatchupResult {
  game_number: number;
  round: string;
  team_a: GameTeamDetail;
  team_b: GameTeamDetail;
  predicted_winner: BracketTeam;
  confidence: number;
  stat_breakdown: StatBreakdown[];
}

export interface RegionResult {
  region: string;
  teams: BracketTeam[];
  rounds: Record<string, MatchupResult[]>;
}

export interface RoundReliability {
  historical_accuracy: number | null;
  sample_size: number | null;
  note: string;
}

export interface BracketResponse {
  season: number;
  regions: Record<string, RegionResult>;
  final_four: {
    teams: BracketTeam[];
    games: MatchupResult[];
  };
  championship: {
    game: MatchupResult;
  };
  champion: BracketTeam;
  total_games: number;
  model_reliability: Record<string, RoundReliability>;
}
