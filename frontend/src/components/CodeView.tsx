"use client";

import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import { useMemo } from "react";
import ReactMarkdown from "react-markdown";

hljs.registerLanguage("python", python);

export function CodeView({ name, content }: { name: string; content: string }) {
  const isMarkdown = name.endsWith(".md");
  const html = useMemo(
    () => (isMarkdown ? "" : hljs.highlight(content, { language: "python", ignoreIllegals: true }).value),
    [content, isMarkdown],
  );

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
        <code className="hljs" dangerouslySetInnerHTML={{ __html: html }} />
      </pre>
    </div>
  );
}
