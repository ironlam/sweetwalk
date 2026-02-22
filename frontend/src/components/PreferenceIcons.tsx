"use client";

import { useState } from "react";
import { DIMENSIONS } from "@/lib/types";

interface PreferenceIconsProps {
  onChange: (weights: number[]) => void;
}

export default function PreferenceIcons({ onChange }: PreferenceIconsProps) {
  const [taps, setTaps] = useState<number[]>(DIMENSIONS.map(() => 0));

  const handleTap = (index: number) => {
    const next = [...taps];
    next[index] = (next[index] + 1) % 4;
    setTaps(next);
    onChange(next.map((t) => t / 3));
  };

  return (
    <div className="flex items-center justify-center gap-3 px-4 py-3 bg-white border-t border-slate-200">
      {DIMENSIONS.map((dim, i) => (
        <button
          key={dim.key}
          onClick={() => handleTap(i)}
          className={`
            flex flex-col items-center gap-1 p-2 rounded-xl transition-all
            ${taps[i] === 0 ? "opacity-40" : ""}
            ${taps[i] === 1 ? "opacity-70 bg-slate-100" : ""}
            ${taps[i] === 2 ? "opacity-90 bg-blue-50 ring-1 ring-blue-200" : ""}
            ${taps[i] === 3 ? "opacity-100 bg-blue-100 ring-2 ring-blue-400 scale-110" : ""}
          `}
          title={`${dim.label}: ${["Off", "Nice to have", "Important", "Must have"][taps[i]]}`}
        >
          <span className="text-2xl">{dim.icon}</span>
          <div className="flex gap-0.5">
            {[1, 2, 3].map((level) => (
              <div
                key={level}
                className={`w-1.5 h-1.5 rounded-full ${
                  taps[i] >= level ? "bg-blue-500" : "bg-slate-200"
                }`}
              />
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}
