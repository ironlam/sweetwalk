import { RoutesResponse } from "@/lib/types";
import RouteCard from "./RouteCard";

interface RouteResultsProps {
  data: RoutesResponse;
  selectedIndex: number;
  onSelect: (index: number) => void;
}

const ROUTE_COLORS = ["#94a3b8", "#3b82f6", "#10b981"];

export default function RouteResults({ data, selectedIndex, onSelect }: RouteResultsProps) {
  return (
    <div className="flex flex-col gap-2 p-4 bg-white/95 backdrop-blur-sm border-t border-slate-200 max-h-[40vh] overflow-y-auto">
      {data.routes.map((route, i) => (
        <RouteCard
          key={route.route_type}
          route={route}
          isSelected={selectedIndex === i}
          color={ROUTE_COLORS[i]}
          onSelect={() => onSelect(i)}
        />
      ))}
    </div>
  );
}
