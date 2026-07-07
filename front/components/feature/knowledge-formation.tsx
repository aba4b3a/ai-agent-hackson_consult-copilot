"use client";

import { ChartNoAxesCombined, CircleDashed, Lightbulb, Network } from "lucide-react";

import type { Dashboard, Observation, Workspace } from "@/lib/schemas";
import { useDashboard } from "@/hooks/use-dashboard";
import { Card, Section } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { Pill } from "@/components/ui/pill";

type KnowledgeCategory = {
  key: string;
  label: string;
  terms: string[];
};

function buildCategories(workspace: Workspace | undefined): KnowledgeCategory[] {
  if (!workspace) return [];
  return [
    { key: "segments", label: "Customer segments", terms: workspace.customer_segments },
    { key: "products", label: "Products", terms: workspace.products },
    { key: "issues", label: "Issues", terms: workspace.known_issues },
    { key: "competitors", label: "Competitors", terms: workspace.competitors },
    { key: "kpis", label: "KPIs", terms: workspace.kpis },
  ];
}

function observationsForTerms(observations: Observation[], terms: string[]) {
  return observations.filter((observation) =>
    observation.related_entities.some((entity) => terms.includes(entity)),
  );
}

function uniqueValues(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function buildKnowledgeGaps(data: Dashboard | undefined) {
  if (!data) return [];
  const observedEntities = new Set(data.observations.flatMap((item) => item.related_entities));
  const missingTopics = data.workspace.observation_topics.filter((topic) => !observedEntities.has(topic));
  const missingKpis = data.workspace.kpis.filter((kpi) => !observedEntities.has(kpi));
  const sparseCategories = buildCategories(data.workspace)
    .filter((category) => category.terms.length > 0)
    .filter((category) => observationsForTerms(data.observations, category.terms).length === 0)
    .map((category) => `${category.label} の新規観察が不足`);

  return uniqueValues([
    ...missingTopics.map((topic) => `${topic} の観察が不足`),
    ...missingKpis.map((kpi) => `${kpi} と観察事実の接続が不足`),
    ...sparseCategories,
  ]).slice(0, 5);
}

function buildRecommendedObservations(data: Dashboard | undefined) {
  if (!data) return [];
  const fromHypotheses = data.hypotheses.flatMap((item) => item.recommended_observations);
  const fromGaps = buildKnowledgeGaps(data).map((gap) => gap.replace("が不足", "を追加で確認"));
  return uniqueValues([...fromHypotheses, ...fromGaps]).slice(0, 5);
}

export function KnowledgeFormation({ workspaceId }: { workspaceId: string }) {
  const { data } = useDashboard(workspaceId);
  const observations = data?.observations ?? [];
  const hypotheses = data?.hypotheses ?? [];
  const metrics = data?.metrics;
  const categories = buildCategories(data?.workspace);
  const knowledgeGaps = buildKnowledgeGaps(data);
  const recommendedObservations = buildRecommendedObservations(data);
  const evidenceCoverage = metrics ? `${Math.round(metrics.evidence_coverage * 100)}%` : "-";

  return (
    <Section id="knowledge" title="Knowledge Formation" icon={<ChartNoAxesCombined size={18} />}>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="Sources ingested"
          value={metrics?.sources_ingested ?? "-"}
          caption="Raw reports, transcripts, and notes"
        />
        <MetricCard
          label="Observations extracted"
          value={metrics?.observations_extracted ?? "-"}
          caption="Observed facts separated from hypotheses"
        />
        <MetricCard
          label="Entities formed"
          value={metrics?.entities_formed ?? "-"}
          caption="Segments, products, issues, competitors, KPIs"
        />
        <MetricCard
          label="Relationships created"
          value={metrics?.relationships_created ?? "-"}
          caption="Evidence-backed links for graph views"
        />
        <MetricCard
          label="Hypotheses observing"
          value={metrics?.hypotheses_under_observation ?? "-"}
          caption="Unconfirmed explanations under watch"
        />
        <MetricCard
          label="Evidence coverage"
          value={evidenceCoverage}
          caption="Share of findings with source snippets"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <div className="flex items-center gap-2">
            <Network size={16} className="text-text-muted" />
            <h3 className="font-medium">Recent knowledge additions</h3>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {categories.map((category) => {
              const categoryObservations = observationsForTerms(observations, category.terms);
              const formedEntities = uniqueValues(
                categoryObservations.flatMap((item) =>
                  item.related_entities.filter((entity) => category.terms.includes(entity)),
                ),
              );

              return (
                <article key={category.key} className="rounded-md border border-border p-3">
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="text-sm font-medium">{category.label}</h4>
                    <Pill>{categoryObservations.length}</Pill>
                  </div>
                  {formedEntities.length > 0 ? (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {formedEntities.map((entity) => (
                        <Pill key={entity} tone="info">
                          {entity}
                        </Pill>
                      ))}
                    </div>
                  ) : null}
                  <ul className="mt-3 space-y-2">
                    {categoryObservations.slice(0, 2).map((item) => (
                      <li key={item.observation_id} className="text-sm leading-6 text-text">
                        {item.summary}
                      </li>
                    ))}
                    {categoryObservations.length === 0 ? (
                      <li className="text-sm leading-6 text-text-muted">No recent additions</li>
                    ) : null}
                  </ul>
                </article>
              );
            })}
          </div>
        </Card>

        <Card>
          <h3 className="font-medium">Observed facts</h3>
          <ul className="mt-3 space-y-3">
            {observations.map((item) => (
              <li key={item.observation_id} className="text-sm leading-6 text-text">
                {item.summary}
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {item.related_entities.map((entity) => (
                    <Pill key={`${item.observation_id}-${entity}`}>{entity}</Pill>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2">
          <h3 className="font-medium">Hypotheses under observation</h3>
          <div className="mt-3 space-y-3">
            {hypotheses.map((item) => (
              <article key={item.hypothesis_id} className="border-t border-border pt-3 first:border-t-0 first:pt-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Pill tone="warning">仮説</Pill>
                  <Pill>{item.status}</Pill>
                  <span className="text-xs text-text-muted">
                    confidence {Math.round(item.confidence * 100)}%
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-text">{item.statement}</p>
              </article>
            ))}
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2">
            <CircleDashed size={16} className="text-text-muted" />
            <h3 className="font-medium">Knowledge gaps</h3>
          </div>
          <ul className="mt-3 space-y-2">
            {knowledgeGaps.map((gap) => (
              <li key={gap} className="text-sm leading-6 text-text">
                {gap}
              </li>
            ))}
            {knowledgeGaps.length === 0 ? (
              <li className="text-sm leading-6 text-text-muted">No priority gaps detected</li>
            ) : null}
          </ul>
        </Card>
      </div>

      <Card>
        <div className="flex items-center gap-2">
          <Lightbulb size={16} className="text-text-muted" />
          <h3 className="font-medium">Recommended observations</h3>
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {recommendedObservations.map((item) => (
            <div key={item} className="rounded-md border border-border px-3 py-2 text-sm leading-6 text-text">
              {item}
            </div>
          ))}
          {recommendedObservations.length === 0 ? (
            <p className="text-sm leading-6 text-text-muted">No recommended observations yet</p>
          ) : null}
        </div>
      </Card>
    </Section>
  );
}
