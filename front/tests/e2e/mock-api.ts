import type { Page } from "@playwright/test";

const dashboard = {
  consultant: {
    name: "Consultant Copilot",
    subtitle: "Demo workspace",
    isLive: true,
  },
  hero: {
    title: "Observed facts",
    count: 3,
    summary: "Signals collected from customer and operations interviews.",
  },
  insights: [
    {
      id: "i1",
      title: "Production lead time is stretching",
      description: "Custom orders are increasing and affecting delivery estimates.",
      meta: "today",
      priority: "danger",
    },
  ],
  portfolio: [{ id: "SMB-1042", name: "Demo Manufacturing", status: "active" }],
  nextActions: [{ id: "a1", title: "Report Copilot", description: "Review the next report draft." }],
};

const knowledge = {
  header: {
    title: "Knowledge Farm",
    subtitle: "ナレッジ形成ダッシュボード",
    statusLabel: "Synced",
    statusDescription: "Demo Manufacturing",
  },
  health: {
    score: 82,
    title: "Knowledge Health",
    signals: ["KPI candidates are linked to evidence."],
  },
  accumulation: [
    { id: "m1", label: "Nodes", value: 3, tone: "blue" },
    { id: "m2", label: "Edges", value: 2, tone: "green" },
    { id: "m3", label: "KPI", value: 1, tone: "yellow" },
    { id: "m4", label: "Signals", value: 1, tone: "purple" },
  ],
  pipeline: [
    { id: "p1", label: "Survey", value: 1, tone: "blue" },
    { id: "p2", label: "Research", value: 1, tone: "teal" },
    { id: "p3", label: "Approval", value: 1, tone: "amber" },
  ],
  gap: {
    title: "Open Questions",
    description: "Confirm whether custom orders are a leading indicator of delivery risk.",
    tags: [
      { id: "g1", label: "Hypothesis graph", tone: "rose" },
      { id: "g2", label: "Evidence needed", tone: "blue" },
    ],
  },
  recentKnowledge: ["Custom orders pressure production lead time."],
};

const kpiTrends = {
  items: [
    {
      id: "k1",
      label: "Lead time",
      category: "operations",
      description: "Average production lead time.",
      latest_value: 14,
      latest_collected_at: "2026-07-12T00:00:00Z",
      direction: "up",
      history: [
        { collected_at: "2026-07-01T00:00:00Z", value: 10 },
        { collected_at: "2026-07-12T00:00:00Z", value: 14 },
      ],
      related_kpis: ["On-time delivery"],
      trigger_condition: "Lead time rises above 12 days",
      measurement_frequency: "weekly",
      approval_status: "proposed",
    },
  ],
};

const graphSlice = {
  nodes: [
    {
      node_id: "company",
      node_type: "CompanyProfile",
      label: "Demo Manufacturing",
      description: "Demo company",
      confidence: 0.9,
      status: "approved",
    },
    {
      node_id: "signal",
      node_type: "Signal",
      label: "Custom orders",
      description: "Custom order demand is increasing.",
      confidence: 0.82,
      status: "proposed",
    },
    {
      node_id: "kpi",
      node_type: "KPI",
      label: "Lead time",
      description: "Production lead time.",
      confidence: 0.76,
      status: "proposed",
    },
  ],
  edges: [
    {
      source_node_id: "signal",
      target_node_id: "kpi",
      edge_type: "LEADING_INDICATOR_OF",
      strength: 0.8,
      observed_count: 2,
      description: "Custom orders may indicate lead-time risk.",
    },
    {
      source_node_id: "company",
      target_node_id: "signal",
      edge_type: "OBSERVES",
      strength: 0.6,
      observed_count: 1,
      description: "The company observes the signal.",
    },
  ],
  meta: {
    truncated: false,
    center_node_id: null,
    period: "latest",
    source: "sample",
  },
};

export const mockApi = async (page: Page) => {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "knowledge-farmer.auth-session",
      JSON.stringify({
        consultantName: "Test Consultant",
        email: "test@example.com",
        companyCode: "SMB-1042",
      }),
    );
  });

  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    if (path.endsWith("/companies")) {
      await route.fulfill({ json: [] });
      return;
    }
    if (path.endsWith("/dashboard")) {
      await route.fulfill({ json: dashboard });
      return;
    }
    if (path.endsWith("/knowledge/stats")) {
      await route.fulfill({ json: knowledge });
      return;
    }
    if (path.endsWith("/knowledge/kpi-trends")) {
      await route.fulfill({ json: kpiTrends });
      return;
    }
    if (path.endsWith("/graph/slice")) {
      await route.fulfill({ json: graphSlice });
      return;
    }

    await route.fulfill({ status: 404, json: { detail: `Unhandled test API route: ${path}` } });
  });
};
