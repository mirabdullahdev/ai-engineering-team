"use client";

import { AlertTriangle, CircleCheck, Sparkles, Timer } from "lucide-react";
import { useEffect, useState } from "react";
import { ActivityFeed } from "@/components/ActivityFeed";
import { Pipeline } from "@/components/Pipeline";
import { RequirementsPanel } from "@/components/RequirementsPanel";
import { Workspace } from "@/components/Workspace";
import { fetchTeam } from "@/lib/api";
import type { TeamMember } from "@/lib/types";
import { useRun } from "@/lib/useRun";

function useElapsed(startedAt: number | null, endedAt: number | null): string | null {
  const [now, setNow] = useState(0);

  useEffect(() => {
    if (!startedAt || endedAt) return;
    const timer = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(timer);
  }, [startedAt, endedAt]);

  if (!startedAt) return null;
  const seconds = Math.max(0, Math.round(((endedAt ?? (now || startedAt)) - startedAt) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export default function Home() {
  const { state, start, reset } = useRun();
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [offline, setOffline] = useState(false);
  const elapsed = useElapsed(state.startedAt, state.endedAt);
  const running = state.status === "running";

  useEffect(() => {
    fetchTeam()
      .then(setTeam)
      .catch(() => setOffline(true));
  }, []);

  return (
    <>
      <header className="flex items-center gap-3 border-b border-line/70 px-6 py-4">
        <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-[#753991] to-[#209dd7] shadow-lg shadow-violet-900/30">
          <Sparkles className="size-[18px] text-white" />
        </div>
        <div>
          <h1 className="text-[15px] font-semibold leading-tight tracking-tight">AI Engineering Team</h1>
          <p className="text-xs text-muted">Describe software. Watch the team build it.</p>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1400px] gap-6 p-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <RequirementsPanel running={running} canReset={state.status !== "idle"} onRun={start} onReset={reset} />
          {offline && (
            <p className="flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-200">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" />
              <span>
                Backend not reachable. Start it from <code className="font-mono">backend/</code> with{" "}
                <code className="font-mono">uv run python -m uvicorn app.main:app --port 8000</code>.
              </span>
            </p>
          )}
        </div>

        <div className="min-w-0 space-y-5">
          <div className="flex min-h-7 items-center justify-between">
            <h2 className="text-xs font-medium uppercase tracking-wider text-muted">The team</h2>
            <div className="flex items-center gap-3 text-xs text-muted">
              {elapsed && (
                <span className="flex items-center gap-1.5 font-mono">
                  <Timer className="size-3.5" />
                  {elapsed}
                </span>
              )}
              {state.status === "finished" && (
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <CircleCheck className="size-3.5" />
                  Build complete
                </span>
              )}
            </div>
          </div>

          <Pipeline team={team} statuses={state.agents} />

          {state.error && (
            <p className="flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-200">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" />
              <span className="break-words">{state.error}</span>
            </p>
          )}

          <div className="grid gap-5 xl:grid-cols-[minmax(0,340px)_1fr]">
            <ActivityFeed feed={state.feed} running={running} />
            <Workspace files={state.files} executions={state.executions} finished={state.status === "finished"} />
          </div>
        </div>
      </main>
    </>
  );
}
