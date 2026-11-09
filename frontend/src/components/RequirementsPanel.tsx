"use client";

import { Play, RotateCcw } from "lucide-react";
import { useState } from "react";
import { EXAMPLES } from "@/lib/agents";

interface Props {
  running: boolean;
  canReset: boolean;
  onRun: (requirements: string) => void;
  onReset: () => void;
}

export function RequirementsPanel({ running, canReset, onRun, onReset }: Props) {
  const [requirements, setRequirements] = useState(EXAMPLES[0].text);
  const ready = requirements.trim().length >= 10 && !running;

  return (
    <section className="space-y-4 rounded-2xl border border-line bg-panel/80 p-5 backdrop-blur">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <label htmlFor="requirements" className="text-xs font-medium uppercase tracking-wider text-muted">
            What should we build?
          </label>
          <span className="text-[11px] text-muted">{requirements.length}/4000</span>
        </div>
        <textarea
          id="requirements"
          value={requirements}
          onChange={(event) => setRequirements(event.target.value)}
          maxLength={4000}
          rows={9}
          disabled={running}
          placeholder="Describe the software you want, in plain English…"
          className="w-full resize-none rounded-lg border border-line bg-ink/60 px-3 py-2.5 text-sm leading-relaxed outline-none transition placeholder:text-muted/60 focus:border-accent focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
        />
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {EXAMPLES.map((example) => (
            <button
              key={example.label}
              type="button"
              disabled={running}
              onClick={() => setRequirements(example.text)}
              className="rounded-full border border-line px-2.5 py-1 text-[11px] text-muted transition hover:border-accent/60 hover:text-white disabled:opacity-40"
            >
              {example.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          disabled={!ready}
          onClick={() => onRun(requirements)}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#753991] to-[#209dd7] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-900/30 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Play className="size-4" />
          {running ? "Building…" : "Build it"}
        </button>
        {canReset && !running && (
          <button
            type="button"
            onClick={onReset}
            aria-label="Start over"
            className="grid place-items-center rounded-xl border border-line px-3 text-muted transition hover:border-accent/60 hover:text-white"
          >
            <RotateCcw className="size-4" />
          </button>
        )}
      </div>
    </section>
  );
}
