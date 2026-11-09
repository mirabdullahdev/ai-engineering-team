import { Check } from "lucide-react";
import type { CSSProperties } from "react";
import { agentStyle } from "@/lib/agents";
import type { AgentStatus, TeamMember } from "@/lib/types";

interface Props {
  team: TeamMember[];
  statuses: Record<string, AgentStatus>;
}

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "Waiting",
  working: "Working",
  done: "Done",
};

export function Pipeline({ team, statuses }: Props) {
  return (
    <ol className="rounded-2xl border border-line bg-card p-4 shadow-card">
      {team.map((member, index) => {
        const status = statuses[member.key] ?? "idle";
        const style = agentStyle(member.key);
        const Icon = style.icon;
        const last = index === team.length - 1;
        return (
          <li key={member.key} className="relative flex gap-3.5 pb-5 last:pb-0">
            {!last && (
              <span
                aria-hidden
                className="absolute left-[19px] top-10 h-[calc(100%-2.5rem)] w-px transition-colors"
                style={{ background: status === "done" ? style.color : "#e5dfd2" }}
              />
            )}
            <span
              style={{ "--ring": `${style.color}55`, background: status === "idle" ? "#f1ece0" : style.color } as CSSProperties}
              className={`relative z-10 grid size-10 shrink-0 place-items-center rounded-full text-card transition ${
                status === "working" ? "animate-ring" : ""
              } ${status === "idle" ? "!text-muted" : ""}`}
            >
              {status === "done" ? <Check className="size-[18px]" /> : <Icon className="size-[18px]" />}
            </span>
            <div className="min-w-0 pt-0.5">
              <div className="flex items-baseline gap-2">
                <h3 className="text-sm font-semibold">{style.name}</h3>
                <span className="text-xs text-muted">{member.role}</span>
              </div>
              <p className="mt-0.5 text-xs leading-snug text-muted">{style.blurb}</p>
              <p className="mt-1.5 text-[11px] font-medium uppercase tracking-[0.12em]" style={{ color: status === "idle" ? "#a8a396" : style.color }}>
                {STATUS_LABEL[status]}
                {status === "working" && <span className="ml-1 inline-block animate-pulse">…</span>}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
