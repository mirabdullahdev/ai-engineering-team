"use client";

import { CircleCheck, CircleX, FilePlus2, MessageSquareText, Play, Terminal, Wrench } from "lucide-react";
import { useEffect, useRef } from "react";
import { agentStyle } from "@/lib/agents";
import type { FeedItem } from "@/lib/types";

const ICONS = {
  thought: MessageSquareText,
  tool: Wrench,
  file: FilePlus2,
  exec: Terminal,
  milestone: Play,
} as const;

function Row({ item }: { item: FeedItem }) {
  const style = agentStyle(item.agent);
  const Icon = item.ok === false ? CircleX : item.kind === "milestone" && item.ok ? CircleCheck : ICONS[item.kind];
  const tone = item.ok === false ? "#f87171" : item.ok ? "#34d399" : style.color;

  return (
    <li className="flex animate-rise gap-3 py-2">
      <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md" style={{ background: `${tone}1a`, color: tone }}>
        <Icon className="size-3.5" />
      </span>
      {item.kind === "milestone" ? (
        <p className="text-[13px]">
          <span className="font-semibold" style={{ color: style.color }}>
            {style.name}
          </span>{" "}
          <span className="text-muted">{item.text}</span>
        </p>
      ) : (
        <p className={`min-w-0 break-words text-[13px] leading-snug ${item.kind === "thought" ? "text-[#c3c7d8]" : "font-mono text-xs text-muted"}`}>
          {item.text}
        </p>
      )}
    </li>
  );
}

export function ActivityFeed({ feed, running }: { feed: FeedItem[]; running: boolean }) {
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [feed.length]);

  return (
    <section className="flex h-[520px] flex-col rounded-2xl border border-line bg-panel/80">
      <h2 className="flex items-center gap-2 border-b border-line px-4 py-3 text-xs font-medium uppercase tracking-wider text-muted">
        Activity
        {running && <span className="size-1.5 animate-pulse rounded-full bg-emerald-400" />}
      </h2>
      <div className="flex-1 overflow-y-auto px-4">
        {feed.length === 0 ? (
          <p className="grid h-full place-items-center text-center text-sm text-muted">
            Agent activity streams here
            <br />
            as the team works.
          </p>
        ) : (
          <ul className="divide-y divide-line/40">
            {feed.map((item) => (
              <Row key={item.id} item={item} />
            ))}
          </ul>
        )}
        <div ref={end} />
      </div>
    </section>
  );
}
