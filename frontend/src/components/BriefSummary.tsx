import { RotateCcw } from "lucide-react";

interface Props {
  requirements: string;
  running: boolean;
  onReset: () => void;
}

export function BriefSummary({ requirements, running, onReset }: Props) {
  return (
    <section className="card-tri p-5">
      <p className="line-clamp-3 text-sm leading-relaxed text-ink/85">{requirements}</p>
      {!running && (
        <button
          type="button"
          onClick={onReset}
          className="mt-3 flex items-center gap-1.5 text-xs font-medium text-primary transition hover:text-primary/70"
        >
          <RotateCcw className="size-3" />
          New build
        </button>
      )}
    </section>
  );
}
