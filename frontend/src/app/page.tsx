"use client";

import { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import SearchBar from "@/components/SearchBar";
import PreferenceIcons from "@/components/PreferenceIcons";
import RouteResults from "@/components/RouteResults";
import { useRoutes } from "@/hooks/useRoutes";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

function routeToGeoJSON(coordinates: [number, number][]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: [{
      type: "Feature",
      properties: {},
      geometry: { type: "LineString", coordinates },
    }],
  };
}

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);
  const [weights, setWeights] = useState<number[]>([0, 0, 0, 0, 0, 0]);
  const [selectedRoute, setSelectedRoute] = useState(2); // Default to Best Walk

  const { data, loading, error, search } = useRoutes();

  // Auto-search when both start and end are set
  useEffect(() => {
    if (start && end) {
      search(start, end, weights);
    }
  }, [start, end, weights, search]);

  // Convert routes to GeoJSON for the Map component
  const routeGeoJSONs = useMemo(() => {
    if (!data) return undefined;
    return data.routes.map((r) => routeToGeoJSON(r.coordinates));
  }, [data]);

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
          routes={routeGeoJSONs}
          selectedRouteIndex={selectedRoute}
        />
        {/* Search overlay */}
        <div className="absolute top-4 left-4 right-4 flex flex-col gap-2 z-10">
          <SearchBar label="Start point..." onSelect={setStart} />
          <SearchBar label="Where do you want to go?" onSelect={setEnd} />
        </div>
        {/* Loading indicator */}
        {loading && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 bg-white/90 backdrop-blur-sm px-4 py-2 rounded-full shadow-md text-sm text-slate-600 flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            Finding routes...
          </div>
        )}
        {/* Error indicator */}
        {error && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 bg-red-50 border border-red-200 px-4 py-2 rounded-full shadow-md text-sm text-red-600">
            {error}
          </div>
        )}
      </div>
      {data && (
        <RouteResults
          data={data}
          selectedIndex={selectedRoute}
          onSelect={setSelectedRoute}
        />
      )}
      <PreferenceIcons onChange={setWeights} />
    </main>
  );
}
