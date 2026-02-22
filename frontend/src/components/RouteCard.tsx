import { RouteResult, DIMENSIONS } from "@/lib/types";

interface RouteCardProps {
  route: RouteResult;
  isSelected: boolean;
  color: string;
  onSelect: () => void;
}

const ROUTE_LABELS = {
  quick: "Quick",
  balanced: "Balanced",
  best_walk: "Best Walk",
} as const;

function formatDuration(seconds: number): string {
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h${m > 0 ? ` ${m}m` : ""}`;
}

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
}

export default function RouteCard({ route, isSelected, color, onSelect }: RouteCardProps) {
  return (
    <button
      onClick={onSelect}
      className={`
        w-full text-left p-3 rounded-xl transition-all
        ${isSelected ? "bg-white shadow-md ring-2" : "bg-slate-50 hover:bg-white hover:shadow-sm"}
      `}
      style={isSelected ? { borderColor: color } : {}}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
          <span className="font-semibold text-sm text-slate-800">
            {ROUTE_LABELS[route.route_type]}
          </span>
        </div>
        <div className="text-xs text-slate-500">
          {formatDistance(route.distance)} · {formatDuration(route.duration)}
        </div>
      </div>
      <div className="flex gap-2">
        {route.dimension_scores.map((score, i) => (
          <div key={DIMENSIONS[i].key} className="flex items-center gap-0.5" title={DIMENSIONS[i].label}>
            <span className="text-xs">{DIMENSIONS[i].icon}</span>
            <div className="w-8 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${Math.round(score * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </button>
  );
}
