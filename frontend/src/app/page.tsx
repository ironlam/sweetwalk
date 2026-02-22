"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const Map = dynamic(() => import("@/components/Map"), { ssr: false });

export default function Home() {
  const [start, setStart] = useState<[number, number] | null>(null);
  const [end, setEnd] = useState<[number, number] | null>(null);

  return (
    <main className="h-screen w-screen relative flex flex-col">
      <div className="flex-1 relative">
        <Map
          onStartSet={setStart}
          onEndSet={setEnd}
        />
      </div>
    </main>
  );
}
