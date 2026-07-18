import { memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import css from "react-syntax-highlighter/dist/esm/languages/prism/css";
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import markdown from "react-syntax-highlighter/dist/esm/languages/prism/markdown";
import markup from "react-syntax-highlighter/dist/esm/languages/prism/markup";
import powershell from "react-syntax-highlighter/dist/esm/languages/prism/powershell";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import sql from "react-syntax-highlighter/dist/esm/languages/prism/sql";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import yaml from "react-syntax-highlighter/dist/esm/languages/prism/yaml";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import remarkGfm from "remark-gfm";

const SUPPORTED_LANGUAGES = new Set([
  "bash",
  "css",
  "javascript",
  "json",
  "jsx",
  "markdown",
  "markup",
  "powershell",
  "python",
  "sql",
  "tsx",
  "typescript",
  "yaml",
]);

const LANGUAGE_ALIASES: Record<string, string> = {
  html: "markup",
  js: "javascript",
  md: "markdown",
  ps1: "powershell",
  py: "python",
  shell: "bash",
  sh: "bash",
  ts: "typescript",
  xml: "markup",
  yml: "yaml",
};

SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("css", css);
SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("jsx", jsx);
SyntaxHighlighter.registerLanguage("markdown", markdown);
SyntaxHighlighter.registerLanguage("markup", markup);
SyntaxHighlighter.registerLanguage("powershell", powershell);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("sql", sql);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("typescript", typescript);
SyntaxHighlighter.registerLanguage("yaml", yaml);

const resolveLanguage = (value: string | undefined) => {
  if (!value) return null;
  const normalized = value.toLowerCase();
  const language = LANGUAGE_ALIASES[normalized] || normalized;
  return SUPPORTED_LANGUAGES.has(language) ? language : null;
};

const createComponents = (streaming: boolean): Components => ({
  h1: ({ children }) => <h1 className="mb-2 mt-3 text-base font-semibold leading-6 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-3 text-[15px] font-semibold leading-6 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1.5 mt-2.5 text-sm font-semibold leading-6 first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="mb-2 whitespace-pre-wrap break-words last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  del: ({ children }) => <del className="text-gray-600">{children}</del>,
  ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5 marker:text-brand-600">{children}</ul>,
  ol: ({ children, start }) => <ol start={start} className="my-2 list-decimal space-y-1 pl-5 marker:font-medium marker:text-brand-700">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5">{children}</li>,
  blockquote: ({ children }) => <blockquote className="my-2 rounded-xl bg-white/70 px-3 py-2 text-gray-700">{children}</blockquote>,
  a: ({ children, href, title }) => (
    <a
      href={href}
      title={title}
      target="_blank"
      rel="noopener noreferrer"
      className="break-words font-medium text-brand-800 underline decoration-brand-300 underline-offset-2 hover:text-brand-900"
    >
      {children}
    </a>
  ),
  hr: () => <hr className="my-3 border-0 border-t border-sand-300" />,
  table: ({ children }) => (
    <div className="my-3 max-w-full overflow-x-auto rounded-xl border border-sand-300 bg-white">
      <table className="min-w-full border-collapse text-left text-xs">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-sand-100 text-gray-800">{children}</thead>,
  tbody: ({ children }) => <tbody className="divide-y divide-sand-200">{children}</tbody>,
  tr: ({ children }) => <tr className="divide-x divide-sand-200">{children}</tr>,
  th: ({ children, align }) => <th align={align} className="whitespace-nowrap px-3 py-2 font-semibold">{children}</th>,
  td: ({ children, align }) => <td align={align} className="px-3 py-2 align-top">{children}</td>,
  input: ({ checked }) => (
    <input
      type="checkbox"
      checked={checked}
      disabled
      readOnly
      className="mr-1.5 h-3.5 w-3.5 rounded border-sand-300 accent-brand-600"
    />
  ),
  img: ({ alt }) => (
    <span className="inline-flex rounded-lg bg-white/70 px-2 py-1 text-xs text-gray-600">
      {alt ? `[Hình ảnh: ${alt}]` : "[Hình ảnh đã được ẩn]"}
    </span>
  ),
  pre: ({ children }) => <>{children}</>,
  code: ({ children, className, node }) => {
    const match = /language-([\w-]+)/.exec(className || "");
    const requestedLanguage = match?.[1];
    const language = resolveLanguage(requestedLanguage);
    const source = String(children).replace(/\n$/, "");
    const position = node?.position;
    const block = Boolean(match || (position && position.start.line !== position.end.line));

    if (!block) {
      return (
        <code className="rounded-md bg-white px-1.5 py-0.5 font-mono text-[0.85em] font-medium text-brand-900">
          {children}
        </code>
      );
    }

    if (!streaming && language) {
      return (
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          PreTag="div"
          CodeTag="code"
          showLineNumbers={false}
          wrapLongLines={false}
          customStyle={{
            margin: "0.75rem 0",
            maxWidth: "100%",
            overflowX: "auto",
            borderRadius: "0.75rem",
            background: "#0f172a",
            padding: "0.875rem",
            fontSize: "0.75rem",
            lineHeight: "1.25rem",
          }}
          codeTagProps={{
            style: {
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            },
          }}
        >
          {source}
        </SyntaxHighlighter>
      );
    }

    return (
      <div className="my-3 max-w-full overflow-x-auto rounded-xl bg-slate-950 p-3 text-left">
        <code className="block whitespace-pre font-mono text-xs leading-5 text-slate-100">{source}</code>
      </div>
    );
  },
});

interface ChatMarkdownProps {
  content: string;
  streaming?: boolean;
}

export const ChatMarkdown = memo(function ChatMarkdown({ content, streaming = false }: ChatMarkdownProps) {
  const components = useMemo(() => createComponents(streaming), [streaming]);

  return (
    <div className="min-w-0 text-left">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components} skipHtml>
        {content}
      </ReactMarkdown>
    </div>
  );
});
