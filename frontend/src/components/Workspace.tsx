"use client";

import { CircleCheck, CircleX, Download, FileCode2, FileText } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { DOWNLOAD_URL, fetchFile } from "@/lib/api";
import type { Execution } from "@/lib/types";
import { CodeView } from "./CodeView";

interface Props {
  files: Record<string, number>;
  executions: Execution[];
  finished: boolean;
}

const rank = (name: string) => (name === "design.md" ? 0 : name.startsWith("test") ? 2 : 1);

export function Workspace({ files, executions, finished }: Props) {
  const names = useMemo(() => Object.keys(files).sort((a, b) => rank(a) - rank(b) || a.localeCompare(b)), [files]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");

  const active = selected && names.includes(selected) ? selected : (names[0] ?? null);
  const version = active ? files[active] : 0;

  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    fetchFile(active)
      .then((text) => !cancelled && setContent(text))
      .catch(() => !cancelled && setContent("Could not load this file."));
    return () => {
      cancelled = true;
    };
  }, [active, version]);

  const lastTest = [...executions].reverse().find((run) => run.file.startsWith("test"));

  return (
    <section className="flex h-[520px] flex-col overflow-hidden rounded-2xl border border-line bg-panel/80">
      <div className="flex items-center justify-between gap-2 border-b border-line pr-3">
        <div className="flex min-w-0 overflow-x-auto">
          {names.map((name) => {
            const Icon = name.endsWith(".md") ? FileText : FileCode2;
            return (
              <button
                key={name}
                type="button"
                onClick={() => setSelected(name)}
                className={`flex shrink-0 items-center gap-1.5 border-b-2 px-3.5 py-3 text-xs transition ${
                  name === active ? "border-accent text-white" : "border-transparent text-muted hover:text-white"
                }`}
              >
                <Icon className="size-3.5" />
                {name}
              </button>
            );
          })}
          {names.length === 0 && <span className="px-4 py-3 text-xs text-muted">Code</span>}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {lastTest && (
            <span
              className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${
                lastTest.code === 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
              }`}
            >
              {lastTest.code === 0 ? <CircleCheck className="size-3" /> : <CircleX className="size-3" />}
              {lastTest.code === 0 ? "Tests passing" : "Tests failing"}
            </span>
          )}
          {finished && (
            <a
              href={DOWNLOAD_URL}
              className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-black transition hover:bg-white/90"
            >
              <Download className="size-3.5" />
              Download
            </a>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {active ? (
          <CodeView name={active} content={content} />
        ) : (
          <p className="grid h-full place-items-center px-6 text-center text-sm text-muted">
            The code appears here, live, as each engineer writes it.
          </p>
        )}
      </div>

      {lastTest?.output && (
        <details className="border-t border-line bg-ink/60">
          <summary className="cursor-pointer px-4 py-2 text-xs text-muted hover:text-white">Test output</summary>
          <pre className="max-h-40 overflow-auto px-4 pb-3 font-mono text-[11.5px] leading-relaxed text-muted">{lastTest.output}</pre>
        </details>
      )}
    </section>
  );
}
