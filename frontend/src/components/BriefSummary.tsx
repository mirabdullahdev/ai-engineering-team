import { RotateCcw } from "lucide-react";

interface Props {
  requirements: string;
  running: boolean;
  onReset: () => void;
}

export function BriefSummary({ requirements, running, onReset }: Props) {
  return (
    <section className="rounded-2xl border border-line bg-card p-4 shadow-card">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">The brief</h2>
        {!running && (
          <button
            type="button"
            onClick={onReset}
            className="flex items-center gap-1.5 text-xs text-muted transition hover:text-forest"
          >
            <RotateCcw className="size-3" />
            New build
          </button>
        )}
      </div>
      <p className="line-clamp-4 text-sm leading-relaxed text-ink/80">{requirements}</p>
    </section>
  );
}
