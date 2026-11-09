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
  const tone = item.ok === false ? "#b4532a" : item.ok ? "#1f6f4a" : style.color;

  return (
    <li className="flex animate-rise gap-3 py-2.5">
      <Icon className="mt-0.5 size-3.5 shrink-0" style={{ color: tone }} />
      {item.kind === "milestone" ? (
        <p className="text-[13px]">
          <span className="font-semibold" style={{ color: style.color }}>
            {style.name}
          </span>{" "}
          <span className="text-muted">{item.text}</span>
        </p>
      ) : (
        <p className={`min-w-0 break-words text-[13px] leading-snug ${item.kind === "thought" ? "text-ink/80" : "font-mono text-xs text-muted"}`}>
          {item.text}
        </p>
      )}
    </li>
  );
}

export function ActivityFeed({ feed }: { feed: FeedItem[] }) {
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [feed.length]);

  return (
    <section className="card-tri flex min-h-[220px] flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-5 py-2">
        <ul className="divide-y divide-line/60">
          {feed.map((item) => (
            <Row key={item.id} item={item} />
          ))}
        </ul>
        <div ref={end} />
      </div>
    </section>
  );
}
