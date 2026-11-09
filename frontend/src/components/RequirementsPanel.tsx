"use client";

import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { EXAMPLES } from "@/lib/agents";

interface Props {
  onRun: (requirements: string) => void;
}

export function RequirementsPanel({ onRun }: Props) {
  const [requirements, setRequirements] = useState("");
  const ready = requirements.trim().length >= 10;

  return (
    <section className="rounded-2xl border border-line bg-card p-3 shadow-card">
      <label htmlFor="requirements" className="sr-only">
        What should we build?
      </label>
      <textarea
        id="requirements"
        value={requirements}
        onChange={(event) => setRequirements(event.target.value)}
        maxLength={4000}
        rows={5}
        placeholder="Describe the software you need, in plain English. Include the rules that matter."
        className="w-full resize-none rounded-xl bg-transparent px-4 py-3 text-[15px] leading-relaxed outline-none placeholder:text-muted/70"
      />
      <div className="flex items-center justify-between gap-3 border-t border-line px-3 pt-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs text-muted">Try</span>
          {EXAMPLES.map((example) => (
            <button
              key={example.label}
              type="button"
              onClick={() => setRequirements(example.text)}
              className="rounded-full border border-line px-3 py-1 text-xs text-ink/80 transition hover:border-forest/50 hover:bg-forest/5 hover:text-forest"
            >
              {example.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          disabled={!ready}
          onClick={() => onRun(requirements)}
          className="flex shrink-0 items-center gap-2 rounded-xl bg-forest px-5 py-2.5 text-sm font-medium text-card transition hover:bg-forest/90 disabled:cursor-not-allowed disabled:opacity-35"
        >
          Build it
          <ArrowRight className="size-4" />
        </button>
      </div>
    </section>
  );
}
