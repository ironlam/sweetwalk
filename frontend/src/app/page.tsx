"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import SearchBar from "@/components/SearchBar";
import PreferenceIcons from "@/components/PreferenceIcons";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);
  const [weights, setWeights] = useState<number[]>([0, 0, 0, 0, 0, 0]);

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
        />
        {/* Search overlay */}
        <div className="absolute top-4 left-4 right-4 flex flex-col gap-2 z-10">
          <SearchBar label="Start point..." onSelect={setStart} />
          <SearchBar label="Where do you want to go?" onSelect={setEnd} />
        </div>
      </div>
      <PreferenceIcons onChange={setWeights} />
    </main>
  );
}
