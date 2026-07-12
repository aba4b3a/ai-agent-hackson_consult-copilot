"use client";

import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * AIアシスタントの返答（Markdown）をチャットバブル内の小さい文字サイズに
 * 合わせて描画する。react-markdown は生HTMLをデフォルトで描画しないため、
 * モデル出力をそのまま渡してもXSSにはならない。
 */
export const ChatMarkdown = ({ text }: { text: string }) => (
  <div className="space-y-2 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }: { children?: ReactNode }) => (
          <p className="mt-2 text-[12px] font-black md:text-sm">{children}</p>
        ),
        h2: ({ children }: { children?: ReactNode }) => (
          <p className="mt-2 text-[12px] font-black md:text-sm">{children}</p>
        ),
        h3: ({ children }: { children?: ReactNode }) => (
          <p className="mt-2 text-[11px] font-black md:text-sm">{children}</p>
        ),
        p: ({ children }: { children?: ReactNode }) => (
          <p className="my-1 leading-relaxed">{children}</p>
        ),
        ul: ({ children }: { children?: ReactNode }) => (
          <ul className="my-1 list-disc space-y-0.5 pl-4">{children}</ul>
        ),
        ol: ({ children }: { children?: ReactNode }) => (
          <ol className="my-1 list-decimal space-y-0.5 pl-4">{children}</ol>
        ),
        li: ({ children }: { children?: ReactNode }) => (
          <li className="leading-relaxed">{children}</li>
        ),
        strong: ({ children }: { children?: ReactNode }) => (
          <strong className="font-black">{children}</strong>
        ),
        a: ({ href, children }: { href?: string; children?: ReactNode }) => (
          <a className="text-blue-600 underline" href={href} target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
        code: ({ children }: { children?: ReactNode }) => (
          <code className="rounded bg-slate-200/70 px-1 py-0.5 font-mono text-[10px] md:text-xs">
            {children}
          </code>
        ),
        pre: ({ children }: { children?: ReactNode }) => (
          <pre className="my-1 overflow-x-auto rounded-md bg-slate-200/70 p-2 text-[10px] md:text-xs">
            {children}
          </pre>
        ),
        table: ({ children }: { children?: ReactNode }) => (
          <div className="my-1 overflow-x-auto">
            <table className="min-w-full border-collapse text-left">{children}</table>
          </div>
        ),
        th: ({ children }: { children?: ReactNode }) => (
          <th className="border-b border-slate-300 px-2 py-1 font-black">{children}</th>
        ),
        td: ({ children }: { children?: ReactNode }) => (
          <td className="border-b border-slate-200 px-2 py-1">{children}</td>
        ),
        blockquote: ({ children }: { children?: ReactNode }) => (
          <blockquote className="my-1 border-l-2 border-slate-300 pl-2 text-slate-600">
            {children}
          </blockquote>
        ),
        hr: () => <hr className="my-2 border-slate-200" />,
      }}
    >
      {text}
    </ReactMarkdown>
  </div>
);
