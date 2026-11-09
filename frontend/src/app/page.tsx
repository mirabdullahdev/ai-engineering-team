"use client";

import { AlertTriangle, CircleCheck, Timer } from "lucide-react";
import { useEffect, useState } from "react";
import { ActivityFeed } from "@/components/ActivityFeed";
import { BriefSummary } from "@/components/BriefSummary";
import { Pipeline } from "@/components/Pipeline";
import { RequirementsPanel } from "@/components/RequirementsPanel";
import { Workspace } from "@/components/Workspace";
import { agentStyle } from "@/lib/agents";
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
  const [brief, setBrief] = useState("");
  const elapsed = useElapsed(state.startedAt, state.endedAt);
  const running = state.status === "running";
  const idle = state.status === "idle";

  useEffect(() => {
    fetchTeam()
      .then(setTeam)
      .catch(() => setOffline(true));
  }, []);

  const run = (requirements: string) => {
    setBrief(requirements);
    start(requirements);
  };

  const errorBanner = state.error && (
    <p className="flex items-start gap-2 rounded-xl border border-terracotta/30 bg-terracotta/5 p-3 text-sm text-terracotta">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" />
      <span className="break-words">{state.error}</span>
    </p>
  );

  const header = (
    <header className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-5">
      <div className="flex items-baseline gap-2.5">
        <span className="text-xl font-semibold tracking-tight">Engineering Team</span>
      </div>
      {running && (
        <span className="flex items-center gap-2 text-xs text-muted">
          <span className="size-1.5 animate-pulse rounded-full bg-primary" />
          {agentStyle(state.activeAgent).name} is working
        </span>
      )}
    </header>
  );

  if (idle) {
    return (
      <>
        {header}
        <main className="mx-auto max-w-3xl px-6 pb-20 pt-14 sm:pt-20">
          <h1 className="text-balance text-center text-4xl font-semibold leading-[1.1] tracking-tight text-primary sm:text-6xl">
            Your team of Software Engineers
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-balance text-center text-base leading-relaxed text-muted">
            Tell the team what you need. A lead designs it, engineers build the backend and the interface, and a test engineer
            proves it works, while you watch the app take shape.
          </p>

          <div className="mt-10">
            <RequirementsPanel onRun={run} />
          </div>
          {errorBanner && <div className="mt-4">{errorBanner}</div>}
          {offline && (
            <p className="mt-4 flex items-start gap-2 rounded-xl border border-ochre/30 bg-ochre/5 p-3 text-xs text-ochre">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" />
              <span>
                Backend not reachable. Start it from <code className="font-mono">backend/</code> with{" "}
                <code className="font-mono">uv run python -m uvicorn app.main:app --port 8000</code>.
              </span>
            </p>
          )}

          <ul className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {team.map((member) => {
              const style = agentStyle(member.key);
              return (
                <li key={member.key} className="card-tri p-6">
                  <p className="text-lg font-semibold text-primary">
                    {style.name}, {member.role}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-ink/85">{style.blurb}</p>
                </li>
              );
            })}
          </ul>
        </main>
      </>
    );
  }

  return (
    <>
      {header}
      <main className="mx-auto grid max-w-[1400px] gap-5 px-6 pb-8 lg:h-[calc(100vh-5.5rem)] lg:grid-cols-[380px_1fr]">
        <div className="flex min-h-0 flex-col gap-4 lg:overflow-y-auto">
          <BriefSummary requirements={brief} running={running} onReset={reset} />
          <Pipeline team={team} statuses={state.agents} />
          <ActivityFeed feed={state.feed} />
        </div>

        <div className="flex min-h-0 flex-col gap-3">
          <div className="flex min-h-6 items-center justify-between text-xs">
            <span className="text-muted">
              {state.status === "finished" ? (
                <span className={`flex items-center gap-1.5 font-medium ${state.testsPassed && state.webOk ? "text-primary" : "text-terracotta"}`}>
                  <CircleCheck className="size-3.5" />
                  {state.testsPassed && state.webOk
                    ? "Build complete, tests passing, app running"
                    : !state.testsPassed
                      ? "Build finished with failing tests"
                      : "Build finished, the app still has errors"}
                </span>
              ) : (
                running && "Building…"
              )}
            </span>
            <span className="flex items-center gap-4 font-mono text-muted">
              {state.tokens && <span>{state.tokens.toLocaleString()} tokens</span>}
              {elapsed && (
                <span className="flex items-center gap-1.5">
                  <Timer className="size-3.5" />
                  {elapsed}
                </span>
              )}
            </span>
          </div>
          {errorBanner}
          <div className="min-h-0 flex-1">
            <Workspace fileText={state.fileText} streaming={state.streaming} executions={state.executions} previewUrl={state.previewUrl} finished={state.status === "finished"} />
          </div>
        </div>
      </main>
    </>
  );
}
