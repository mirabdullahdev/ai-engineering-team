"use client";

import { CircleCheck, CircleX, Download, ExternalLink, FileCode2, FileText, Globe, RotateCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { DOWNLOAD_URL, fetchFile } from "@/lib/api";
import type { Execution } from "@/lib/types";
import { CodeView } from "./CodeView";

interface Props {
  files: Record<string, number>;
  executions: Execution[];
  previewUrl: string | null;
  finished: boolean;
}

const PREVIEW = "__preview__";
const WEB_PREFIX = "web/";

interface Group {
  title: string;
  names: string[];
}

function groupFiles(names: string[]): Group[] {
  const isTest = (name: string) => name.startsWith("test");
  const groups: Group[] = [
    { title: "Design", names: names.filter((name) => name === "design.md") },
    { title: "Backend", names: names.filter((name) => !name.startsWith(WEB_PREFIX) && name !== "design.md" && !isTest(name)) },
    { title: "Frontend", names: names.filter((name) => name.startsWith(WEB_PREFIX)) },
    { title: "Tests", names: names.filter((name) => isTest(name)) },
  ];
  return groups.filter((group) => group.names.length > 0);
}

const labelOf = (name: string) => name.replace(/^web\/src\//, "");

export function Workspace({ files, executions, previewUrl, finished }: Props) {
  const names = useMemo(() => Object.keys(files).sort(), [files]);
  const groups = useMemo(() => groupFiles(names), [names]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [reloads, setReloads] = useState(0);

  const hasWebFiles = names.some((name) => name.startsWith(WEB_PREFIX));
  const defaultTab = previewUrl && hasWebFiles ? PREVIEW : (names[0] ?? null);
  const active = selected && (selected === PREVIEW ? previewUrl : names.includes(selected)) ? selected : defaultTab;
  const version = active && active !== PREVIEW ? files[active] : 0;

  useEffect(() => {
    if (!active || active === PREVIEW) return;
    let cancelled = false;
    fetchFile(active)
      .then((text) => !cancelled && setContent(text))
      .catch(() => !cancelled && setContent("Could not load this file."));
    return () => {
      cancelled = true;
    };
  }, [active, version]);

  const lastTest = [...executions].reverse().find((run) => run.file.startsWith("test"));
  const itemClass = (isActive: boolean) =>
    `flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs transition ${
      isActive ? "bg-primary/10 font-medium text-primary" : "text-ink/75 hover:bg-ink/5"
    }`;

  return (
    <section className="flex min-h-[460px] flex-col overflow-hidden bg-card lg:h-full">
      <div className="flex items-center justify-between gap-2 border-b border-line px-4 py-2.5">
        <span className="truncate text-xs font-medium text-ink/80">
          {active === PREVIEW ? "Live preview" : active ? labelOf(active) : "Workspace"}
        </span>
        <div className="flex shrink-0 items-center gap-2">
          {lastTest && (
            <span
              className={`flex items-center gap-1.5 text-xs font-medium ${lastTest.code === 0 ? "text-primary" : "text-terracotta"}`}
            >
              {lastTest.code === 0 ? <CircleCheck className="size-3" /> : <CircleX className="size-3" />}
              {lastTest.code === 0 ? "Tests passing" : "Tests failing"}
            </span>
          )}
          {finished && (
            <a
              href={DOWNLOAD_URL}
              className="flex items-center gap-1.5 rounded-lg bg-ink px-3 py-1.5 text-xs font-medium text-card transition hover:bg-ink/85"
            >
              <Download className="size-3.5" />
              Download
            </a>
          )}
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        <nav className="hidden w-52 shrink-0 overflow-y-auto border-r border-line p-3 sm:block">
          {previewUrl && (
            <button type="button" onClick={() => setSelected(PREVIEW)} className={`mb-3 ${itemClass(active === PREVIEW)}`}>
              <Globe className="size-3.5 shrink-0" />
              Live preview
            </button>
          )}
          {groups.length === 0 && !previewUrl && <p className="px-2 text-xs text-muted">Files appear here as they are written.</p>}
          {groups.map((group) => (
            <div key={group.title} className="mb-3">
              <p className="mb-1 px-2.5 text-xs font-semibold text-muted">{group.title}</p>
              {group.names.map((name) => {
                const Icon = name.endsWith(".md") ? FileText : FileCode2;
                return (
                  <button key={name} type="button" onClick={() => setSelected(name)} className={itemClass(name === active)}>
                    <Icon className="size-3.5 shrink-0" />
                    <span className="truncate">{labelOf(name)}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="flex min-w-0 flex-1 flex-col">
          {active === PREVIEW && previewUrl ? (
            <>
              <div className="flex items-center gap-2 border-b border-line bg-card px-3 py-2">
                <span className="min-w-0 flex-1 truncate rounded-md bg-paper px-3 py-1 font-mono text-[11px] text-muted">{previewUrl}</span>
                <button
                  type="button"
                  onClick={() => setReloads((count) => count + 1)}
                  aria-label="Reload preview"
                  className="grid size-7 place-items-center rounded-md text-muted transition hover:bg-ink/5 hover:text-ink"
                >
                  <RotateCw className="size-3.5" />
                </button>
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Open preview in a new tab"
                  className="grid size-7 place-items-center rounded-md text-muted transition hover:bg-ink/5 hover:text-ink"
                >
                  <ExternalLink className="size-3.5" />
                </a>
              </div>
              <iframe
                key={reloads}
                src={previewUrl}
                title="Live preview of the app being built"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                className="min-h-0 w-full flex-1 bg-white"
              />
            </>
          ) : (
            <div className="min-h-0 flex-1 overflow-auto">
              {active ? (
                <CodeView name={active} content={content} />
              ) : (
                <p className="grid h-full min-h-[300px] place-items-center px-6 text-center text-lg text-muted">
                  The code and a live preview appear here
                  <br />
                  as the engineers work.
                </p>
              )}
            </div>
          )}

          {active !== PREVIEW && lastTest?.output && (
            <details className="border-t border-line">
              <summary className="cursor-pointer px-4 py-2 text-xs text-muted hover:text-ink">Test output</summary>
              <pre className="max-h-40 overflow-auto px-4 pb-3 font-mono text-[11.5px] leading-relaxed text-ink/70">{lastTest.output}</pre>
            </details>
          )}
        </div>
      </div>
    </section>
  );
}
