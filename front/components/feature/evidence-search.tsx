"use client";

import { useState } from "react";
import { FileSearch, Search } from "lucide-react";

import { useEvidenceSearch } from "@/hooks/use-evidence-search";
import { Card, Section } from "@/components/ui/card";
import { Pill } from "@/components/ui/pill";

export function EvidenceSearch({ workspaceId }: { workspaceId: string }) {
  const [query, setQuery] = useState("");
  const { data } = useEvidenceSearch(workspaceId, query);
  const results = data ?? [];

  return (
    <Section id="evidence" title="Evidence Search" icon={<FileSearch size={18} />}>
      <Card>
        <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-text-muted">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="価格・競合・待ち時間などで検索"
            className="w-full bg-transparent text-text outline-none placeholder:text-text-muted"
          />
        </label>
        <div className="mt-4 space-y-3">
          {results.map((item) => (
            <article key={item.source_id} className="border-t border-border pt-3">
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
                {item.source_type}
              </p>
              <p className="mt-1 text-sm leading-6 text-text">{item.snippet}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {item.tags.map((tag) => (
                  <Pill key={tag}>{tag}</Pill>
                ))}
              </div>
            </article>
          ))}
          {results.length === 0 ? (
            <p className="pt-3 text-sm text-text-muted">一致する証拠が見つかりません。</p>
          ) : null}
        </div>
      </Card>
    </Section>
  );
}
