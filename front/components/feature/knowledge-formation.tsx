"use client";

import { ChartNoAxesCombined } from "lucide-react";

import { useDashboard } from "@/hooks/use-dashboard";
import { Card, Section } from "@/components/ui/card";

export function KnowledgeFormation({ workspaceId }: { workspaceId: string }) {
  const { data } = useDashboard(workspaceId);
  const observations = data?.observations ?? [];
  const hypotheses = data?.hypotheses ?? [];

  return (
    <Section id="knowledge" title="Knowledge Formation" icon={<ChartNoAxesCombined size={18} />}>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="font-medium">Observed facts</h3>
          <ul className="mt-3 space-y-3">
            {observations.map((item) => (
              <li key={item.observation_id} className="text-sm leading-6 text-text">
                {item.summary}
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3 className="font-medium">Hypotheses under observation</h3>
          <ul className="mt-3 space-y-3">
            {hypotheses.map((item) => (
              <li key={item.hypothesis_id} className="text-sm leading-6 text-text">
                {item.statement}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </Section>
  );
}
