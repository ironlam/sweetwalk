"use client";

import { useState, useCallback } from "react";
import { fetchRoutes } from "@/lib/api";
import { RoutesResponse } from "@/lib/types";

export function useRoutes() {
  const [data, setData] = useState<RoutesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (start: [number, number], end: [number, number], weights: number[]) => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchRoutes({
          start_lat: start[1],
          start_lon: start[0],
          end_lat: end[1],
          end_lon: end[0],
          weights,
        });
        setData(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, search, clear };
}
