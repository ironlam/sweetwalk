"use client";

import { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface MapProps {
  onStartSet: (lngLat: [number, number]) => void;
  onEndSet: (lngLat: [number, number]) => void;
  routes?: GeoJSON.FeatureCollection[];
  selectedRouteIndex?: number;
}

const ROUTE_COLORS = ["#94a3b8", "#3b82f6", "#10b981"]; // gray, blue, green

export default function Map({ onStartSet, onEndSet, routes, selectedRouteIndex }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const startMarker = useRef<mapboxgl.Marker | null>(null);
  const endMarker = useRef<mapboxgl.Marker | null>(null);
  const [clickMode, setClickMode] = useState<"start" | "end">("start");
  const clickModeRef = useRef(clickMode);
  clickModeRef.current = clickMode;

  const onStartSetRef = useRef(onStartSet);
  onStartSetRef.current = onStartSet;
  const onEndSetRef = useRef(onEndSet);
  onEndSetRef.current = onEndSet;

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [2.3522, 48.8566], // Paris default
      zoom: 13,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
    map.current.addControl(
      new mapboxgl.GeolocateControl({ trackUserLocation: true }),
      "top-right"
    );

    map.current.on("click", (e) => {
      const lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat];

      if (clickModeRef.current === "start") {
        if (startMarker.current) startMarker.current.remove();
        startMarker.current = new mapboxgl.Marker({ color: "#10b981" })
          .setLngLat(lngLat)
          .addTo(map.current!);
        onStartSetRef.current(lngLat);
        setClickMode("end");
      } else {
        if (endMarker.current) endMarker.current.remove();
        endMarker.current = new mapboxgl.Marker({ color: "#ef4444" })
          .setLngLat(lngLat)
          .addTo(map.current!);
        onEndSetRef.current(lngLat);
        setClickMode("start");
      }
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Draw routes on map
  useEffect(() => {
    if (!map.current || !routes) return;

    const m = map.current;

    const draw = () => {
      // Remove existing route layers
      for (let i = 0; i < 3; i++) {
        if (m.getLayer(`route-${i}`)) m.removeLayer(`route-${i}`);
        if (m.getSource(`route-${i}`)) m.removeSource(`route-${i}`);
      }

      // Add route layers
      routes.forEach((geojson, i) => {
        m.addSource(`route-${i}`, { type: "geojson", data: geojson });
        m.addLayer({
          id: `route-${i}`,
          type: "line",
          source: `route-${i}`,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": ROUTE_COLORS[i],
            "line-width": selectedRouteIndex === i ? 6 : 3,
            "line-opacity": selectedRouteIndex === i ? 1 : 0.5,
          },
        });
      });
    };

    if (m.isStyleLoaded()) draw();
    else m.on("load", draw);
  }, [routes, selectedRouteIndex]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
