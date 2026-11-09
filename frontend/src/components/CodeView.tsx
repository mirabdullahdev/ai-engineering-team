"use client";

import hljs from "highlight.js/lib/core";
import css from "highlight.js/lib/languages/css";
import python from "highlight.js/lib/languages/python";
import typescript from "highlight.js/lib/languages/typescript";
import { useMemo } from "react";
import ReactMarkdown from "react-markdown";

hljs.registerLanguage("python", python);
hljs.registerLanguage("typescript", typescript);
hljs.registerLanguage("css", css);

function languageOf(name: string): string | null {
  if (name.endsWith(".py")) return "python";
  if (name.endsWith(".ts") || name.endsWith(".tsx")) return "typescript";
  if (name.endsWith(".css")) return "css";
  return null;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function CodeView({ name, content, caret }: { name: string; content: string; caret: boolean }) {
  const isMarkdown = name.endsWith(".md");
  const html = useMemo(() => {
    if (isMarkdown) return "";
    const language = languageOf(name);
    return language ? hljs.highlight(content, { language, ignoreIllegals: true }).value : escapeHtml(content);
  }, [content, isMarkdown, name]);

  if (isMarkdown) {
    return (
      <div className="doc px-8 py-7">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="flex font-mono text-[12.5px] leading-[1.7]">
      <div aria-hidden className="select-none border-r border-line px-3 py-5 text-right text-muted/50">
        {content.split("\n").map((_, index) => (
          <div key={index}>{index + 1}</div>
        ))}
      </div>
      <pre className="flex-1 overflow-x-auto px-5 py-5">
        <code className="hljs" dangerouslySetInnerHTML={{ __html: caret ? `${html}<span class="stream-caret"></span>` : html }} />
      </pre>
    </div>
  );
}
