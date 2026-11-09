import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export function Input({ className, invalid, ...props }: InputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cn(
        "w-full rounded-lg border bg-card px-3 py-2 text-sm outline-none transition placeholder:text-muted/70",
        "focus:border-accent focus:ring-2 focus:ring-accent/20",
        invalid ? "border-danger" : "border-line",
        className,
      )}
      {...props}
    />
  );
}
