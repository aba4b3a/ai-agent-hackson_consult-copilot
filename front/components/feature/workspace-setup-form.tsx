"use client";

import { useState } from "react";
import Link from "next/link";

import { useCreateWorkspace } from "@/hooks/use-create-workspace";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input, Textarea } from "@/components/ui/field";
import { Pill } from "@/components/ui/pill";

/** Split a comma / newline separated string into a trimmed, non-empty list. */
function toList(value: string): string[] {
  return value
    .split(/[,、\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function WorkspaceSetupForm() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [products, setProducts] = useState("");
  const [segments, setSegments] = useState("");
  const [competitors, setCompetitors] = useState("");
  const [issues, setIssues] = useState("");
  const [kpis, setKpis] = useState("");
  const [topics, setTopics] = useState("");

  const create = useCreateWorkspace();
  const workspace = create.data;

  function handleSubmit() {
    create.mutate({
      workspace_name: name.trim(),
      business_description: description.trim(),
      products: toList(products),
      customer_segments: toList(segments),
      competitors: toList(competitors),
      known_issues: toList(issues),
      kpis: toList(kpis),
      observation_topics: toList(topics),
    });
  }

  if (workspace) {
    return (
      <Card>
        <h2 className="text-lg font-semibold">ワークスペースを作成しました</h2>
        <p className="mt-1 text-sm text-text-muted">{workspace.workspace_name}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {workspace.customer_segments.map((s) => (
            <Pill key={s}>{s}</Pill>
          ))}
          {workspace.competitors.map((c) => (
            <Pill key={c} tone="warning">
              {c}
            </Pill>
          ))}
        </div>
        <Link href="/" className="mt-4 inline-block">
          <Button>ダッシュボードへ</Button>
        </Link>
      </Card>
    );
  }

  return (
    <Card>
      <div className="space-y-4">
        <Field label="会社・ワークスペース名" htmlFor="ws-name">
          <Input
            id="ws-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="みどり薬局チェーン"
          />
        </Field>
        <Field label="事業内容" htmlFor="ws-desc" optional>
          <Textarea
            id="ws-desc"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="地域密着型の調剤薬局。処方箋受付、在宅訪問、健康相談を提供。"
          />
        </Field>
        <Field label="商品・サービス" htmlFor="ws-products" optional hint="カンマまたは改行区切り">
          <Input id="ws-products" value={products} onChange={(e) => setProducts(e.target.value)} placeholder="処方箋受付, 在宅訪問, 健康相談" />
        </Field>
        <Field label="顧客層" htmlFor="ws-segments" optional hint="カンマまたは改行区切り">
          <Input id="ws-segments" value={segments} onChange={(e) => setSegments(e.target.value)} placeholder="高齢者, 子育て世帯, 慢性疾患患者" />
        </Field>
        <Field label="競合" htmlFor="ws-competitors" optional hint="カンマまたは改行区切り">
          <Input id="ws-competitors" value={competitors} onChange={(e) => setCompetitors(e.target.value)} placeholder="駅前ドラッグ, オンライン服薬指導サービス" />
        </Field>
        <Field label="現在の課題" htmlFor="ws-issues" optional hint="カンマまたは改行区切り">
          <Input id="ws-issues" value={issues} onChange={(e) => setIssues(e.target.value)} placeholder="待ち時間, 価格不安, 在庫切れ" />
        </Field>
        <Field label="固定KPI" htmlFor="ws-kpis" optional hint="カンマまたは改行区切り">
          <Input id="ws-kpis" value={kpis} onChange={(e) => setKpis(e.target.value)} placeholder="再来店率, 待ち時間, 処方箋受付数" />
        </Field>
        <Field label="重点観測項目" htmlFor="ws-topics" optional hint="カンマまたは改行区切り">
          <Input id="ws-topics" value={topics} onChange={(e) => setTopics(e.target.value)} placeholder="価格比較, 待ち時間, オンライン服薬指導への反応" />
        </Field>

        {create.isError ? (
          <p className="text-sm text-danger">作成に失敗しました。時間をおいて再試行してください。</p>
        ) : null}

        <Button className="w-full" disabled={create.isPending || !name.trim()} onClick={handleSubmit}>
          {create.isPending ? "作成中…" : "ワークスペースを作成"}
        </Button>
      </div>
    </Card>
  );
}
