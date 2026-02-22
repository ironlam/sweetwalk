export interface RouteResult {
  route_type: "quick" | "balanced" | "best_walk";
  nodes: string[];
  coordinates: [number, number][];
  distance: number;
  duration: number;
  quality_score: number;
  dimension_scores: number[];
}

export interface RoutesResponse {
  routes: RouteResult[];
  city: string;
}

export interface RouteRequest {
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
  weights: number[];
}

export const DIMENSIONS = [
  { key: "greenery", icon: "🌳", label: "Greenery" },
  { key: "heritage", icon: "🏛️", label: "Heritage" },
  { key: "tranquility", icon: "🤫", label: "Tranquility" },
  { key: "water", icon: "💧", label: "Water" },
  { key: "culture", icon: "🎨", label: "Culture" },
  { key: "charm", icon: "✨", label: "Charm" },
] as const;
