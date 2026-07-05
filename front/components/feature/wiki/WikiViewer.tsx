"use client";

import { useEffect, useMemo, useState } from "react";

import { BottomNav } from "@/components/feature/discovery/BottomNav";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { PhoneFrame } from "@/components/ui/PhoneFrame";
import { useWikiFileContent, useWikiFiles, useWikiVersions } from "@/hooks/use-wiki";
import { toRelativeWikiPath } from "@/services/wiki-service";

const computeLineDiff = (left: string, right: string) => {
  const leftLines = left.split("\n");
  const rightLines = right.split("\n");
  const out: { kind: "same" | "add" | "del"; line: string }[] = [];
  const max = Math.max(leftLines.length, rightLines.length);
  for (let i = 0; i < max; i += 1) {
    const l = leftLines[i];
    const r = rightLines[i];
    if (l === r) {
      out.push({ kind: "same", line: r ?? "" });
    } else {
      if (l !== undefined) out.push({ kind: "del", line: l });
      if (r !== undefined) out.push({ kind: "add", line: r });
    }
  }
  return out;
};

export const WikiViewer = () => {
  const filesQuery = useWikiFiles();
  const versionsQuery = useWikiVersions();
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [compareVersion, setCompareVersion] = useState<string | null>(null);

  const relativePath = useMemo(() => {
    if (!selectedPath) return null;
    return toRelativeWikiPath(selectedPath);
  }, [selectedPath]);

  const currentContent = useWikiFileContent(relativePath, undefined, Boolean(relativePath));
  const versionContent = useWikiFileContent(
    relativePath,
    compareVersion ?? undefined,
    Boolean(relativePath && compareVersion),
  );

  useEffect(() => {
    const files = filesQuery.data?.items ?? [];
    if (files.length === 0) {
      setSelectedPath(null);
      setCompareVersion(null);
      return;
    }

    if (!selectedPath || !files.some((file) => file.path === selectedPath)) {
      setSelectedPath(files[0].path);
      setCompareVersion(null);
    }
  }, [filesQuery.data?.items, selectedPath]);

  if (filesQuery.isLoading) return <LoadingState message="Wiki ファイルを読込中..." />;
  if (filesQuery.isError || !filesQuery.data) {
    return <LoadingState isError message="Wiki ファイル一覧を取得できませんでした。" />;
  }

  const versionList = versionsQuery.data?.versions ?? [];
  const diff =
    compareVersion && currentContent.data && versionContent.data
      ? computeLineDiff(versionContent.data.content, currentContent.data.content)
      : null;

  return (
    <PhoneFrame>
      <div className="px-5 pb-24 pt-5 md:px-7 md:pb-8 md:pt-8">
        <header className="space-y-1">
          <p className="text-xs font-black text-blue-600">LLM Wiki</p>
          <h1 className="text-xl font-black tracking-tight text-slate-950 md:text-2xl">企業ナレッジ Wiki</h1>
          <p className="text-xs font-bold text-slate-500">
            company_profile.md / kpi_definitions.yaml / focus_metrics.yaml / research_policy.yaml をここで閲覧できます。
          </p>
        </header>

        <section className="mt-4 grid gap-2">
          {filesQuery.data.items.length === 0 ? (
            <Card className="rounded-lg p-3 text-xs font-bold text-slate-500">
              Wiki ファイルがまだありません。
            </Card>
          ) : (
            filesQuery.data.items.map((file) => (
              <button
                key={file.path}
                type="button"
                onClick={() => {
                  setSelectedPath(file.path);
                  setCompareVersion(null);
                }}
                className={`w-full rounded-lg border px-3 py-2 text-left text-xs font-bold transition ${
                  file.path === selectedPath
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-700"
                }`}
              >
                {file.path}
              </button>
            ))
          )}
        </section>

        {relativePath ? (
          <Card className="mt-4 space-y-3 rounded-lg">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-black text-slate-950">{relativePath}</p>
              <div className="flex items-center gap-2">
                <label className="text-[11px] font-black text-slate-500">差分:</label>
                <select
                  className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-semibold"
                  value={compareVersion ?? ""}
                  onChange={(event) => setCompareVersion(event.target.value || null)}
                >
                  <option value="">(なし)</option>
                  {versionList.map((version) => (
                    <option key={version} value={version}>
                      {version}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {currentContent.isLoading ? <p className="text-xs font-bold text-slate-500">読込中...</p> : null}
            {currentContent.isError ? (
              <p className="text-xs font-black text-rose-700">本文を取得できませんでした。</p>
            ) : null}

            {diff ? (
              <pre className="max-h-[480px] overflow-auto rounded-lg bg-slate-50 p-3 font-mono text-[11px] leading-relaxed">
                {diff.map((row, index) => (
                  <div
                    key={index}
                    className={
                      row.kind === "add"
                        ? "bg-teal-50 text-teal-700"
                        : row.kind === "del"
                          ? "bg-rose-50 text-rose-700"
                          : "text-slate-700"
                    }
                  >
                    {row.kind === "add" ? "+ " : row.kind === "del" ? "- " : "  "}
                    {row.line}
                  </div>
                ))}
              </pre>
            ) : currentContent.data ? (
              <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 font-mono text-[11px] leading-relaxed text-slate-700">
                {currentContent.data.content}
              </pre>
            ) : null}
          </Card>
        ) : null}
      </div>
      <BottomNav active="wiki" />
    </PhoneFrame>
  );
};
