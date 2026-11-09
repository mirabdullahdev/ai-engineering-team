import { Check, ChevronRight, Loader2 } from "lucide-react";
import { Fragment, type CSSProperties } from "react";
import { agentStyle } from "@/lib/agents";
import type { AgentStatus, TeamMember } from "@/lib/types";

interface Props {
  team: TeamMember[];
  statuses: Record<string, AgentStatus>;
}

export function Pipeline({ team, statuses }: Props) {
  return (
    <div className="flex flex-col items-stretch gap-2 sm:flex-row">
      {team.map((member, index) => {
        const status = statuses[member.key] ?? "idle";
        const style = agentStyle(member.key);
        const Icon = style.icon;
        return (
          <Fragment key={member.key}>
            <article
              style={{ "--ring": `${style.color}88`, borderColor: status === "idle" ? undefined : `${style.color}66` } as CSSProperties}
              className={`relative flex-1 rounded-2xl border bg-panel/80 p-4 transition ${
                status === "working" ? "animate-ring" : "border-line"
              } ${status === "idle" ? "opacity-60" : ""}`}
            >
              <div className="flex items-start justify-between">
                <div className="grid size-10 place-items-center rounded-xl" style={{ background: `${style.color}1f`, color: style.color }}>
                  <Icon className="size-5" />
                </div>
                {status === "working" && <Loader2 className="size-4 animate-spin" style={{ color: style.color }} />}
                {status === "done" && (
                  <span className="grid size-5 place-items-center rounded-full bg-emerald-500/15 text-emerald-400">
                    <Check className="size-3" />
                  </span>
                )}
              </div>
              <h3 className="mt-3 text-sm font-semibold">{style.name}</h3>
              <p className="text-xs font-medium" style={{ color: style.color }}>
                {member.role}
              </p>
              <p className="mt-1.5 text-xs leading-snug text-muted">{style.blurb}</p>
            </article>
            {index < team.length - 1 && (
              <div className="hidden items-center text-line sm:flex">
                <ChevronRight className="size-5" />
              </div>
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
