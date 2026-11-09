"use client";

import { useState } from "react";

interface Props {
  onRun: (requirements: string) => void;
}

export function RequirementsPanel({ onRun }: Props) {
  const [requirements, setRequirements] = useState("");
  const ready = requirements.trim().length >= 10;

  return (
    <section className="card-tri p-6">
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
        className="w-full resize-none bg-transparent text-[15px] leading-relaxed outline-none placeholder:text-muted/70"
      />
      <div className="mt-4 flex justify-end">
        <button
          type="button"
          disabled={!ready}
          onClick={() => onRun(requirements)}
          className="bg-primary px-6 py-2.5 text-sm font-medium text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Build it
        </button>
      </div>
    </section>
  );
}
