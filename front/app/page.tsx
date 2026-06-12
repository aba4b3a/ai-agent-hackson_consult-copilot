import {
  AudioLines,
  Bot,
  ChartNoAxesCombined,
  FileSearch,
  GitBranch,
  Link2,
  MessageSquareText,
  PenLine,
  Search,
  Sparkles,
} from "lucide-react";

const metrics = [
  ["Sources", "18", "daily reports, voice notes, competitor clips"],
  ["Facts", "42", "observations separated from hypotheses"],
  ["Entities", "27", "segments, products, issues, competitors, KPIs"],
  ["Signals", "5", "rule-based discovery alerts this week"],
];

const signals = [
  {
    title: "Competitor wait-time mentions increased",
    detail: "High-value pharmacy customers mentioned Station Drug wait times 2.2x more than baseline.",
    severity: "warning",
    evidence: "4 evidence snippets",
  },
  {
    title: "Online consultation interest appeared",
    detail: "Parents asked whether medication guidance could happen after store hours.",
    severity: "info",
    evidence: "3 evidence snippets",
  },
  {
    title: "Inventory confirmation became a recurring issue",
    detail: "Several reports connect stock checks with repeat-visit hesitation.",
    severity: "danger",
    evidence: "5 evidence snippets",
  },
];

const observations = [
  "高齢者から、競合店の待ち時間が短いという比較発言があった。",
  "子育て世帯から、オンライン服薬指導の相談が増えた。",
  "夕方の在庫確認に時間がかかり、再来店を迷う発言があった。",
];

const hypotheses = [
  "競合の利便性訴求が、待ち時間への不満を強めている可能性がある。",
  "子育て世帯では、営業時間外の相談手段が継続利用に影響している可能性がある。",
];

const evidence = [
  {
    source: "Daily report",
    snippet: "駅前ドラッグのほうが待ち時間が短いと言われた。",
    tags: ["高齢者", "待ち時間", "駅前ドラッグ"],
  },
  {
    source: "Voice transcript",
    snippet: "通院後に店舗へ寄る時間が取りづらいそうです。",
    tags: ["子育て世帯", "オンライン服薬指導"],
  },
  {
    source: "Consultant note",
    snippet: "在庫確認の遅れが再来店意向に影響しているかもしれない。",
    tags: ["在庫切れ", "再来店率"],
  },
];

const graphNodes = [
  { label: "高齢者", x: "8%", y: "18%", tone: "segment" },
  { label: "待ち時間", x: "44%", y: "10%", tone: "issue" },
  { label: "駅前ドラッグ", x: "72%", y: "24%", tone: "competitor" },
  { label: "再来店率", x: "58%", y: "66%", tone: "kpi" },
  { label: "競合利便性仮説", x: "20%", y: "68%", tone: "hypothesis" },
];

function Pill({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600">{children}</span>;
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4 border-t border-slate-200 py-6">
      <div className="flex items-center gap-2">
        <span className="grid h-9 w-9 place-items-center rounded-md border border-slate-200 bg-white text-slate-700">
          {icon}
        </span>
        <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#f6f7f9] text-slate-950">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Continuous Discovery Agent</p>
            <h1 className="text-xl font-semibold">Consultant Copilot</h1>
          </div>
          <button className="grid h-10 w-10 place-items-center rounded-md border border-slate-200 bg-white text-slate-700" aria-label="Search">
            <Search size={18} />
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          <section className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">Active workspace</p>
                <h2 className="mt-1 text-2xl font-semibold">みどり薬局チェーン</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                  日報、音声入力、競合情報、KPIを継続的に集め、観察事実・仮説・証拠を分けて週次レポートにまとめます。
                </p>
              </div>
              <div className="flex gap-2">
                <button className="inline-flex items-center gap-2 rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white">
                  <Link2 size={16} />
                  Intake link
                </button>
                <button className="grid h-10 w-10 place-items-center rounded-md border border-slate-200 bg-white text-slate-700" aria-label="Add note">
                  <PenLine size={17} />
                </button>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {metrics.map(([label, value, detail]) => (
                <div key={label} className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="text-sm text-slate-500">{label}</p>
                  <p className="mt-2 text-3xl font-semibold">{value}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p>
                </div>
              ))}
            </div>
          </section>

          <Section title="Discovery Feed" icon={<Sparkles size={18} />}>
            <div className="space-y-3">
              {signals.map((signal) => (
                <article key={signal.title} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium">{signal.title}</h3>
                      <p className="mt-1 text-sm leading-6 text-slate-600">{signal.detail}</p>
                    </div>
                    <Pill>{signal.evidence}</Pill>
                  </div>
                </article>
              ))}
            </div>
          </Section>

          <Section title="Knowledge Formation" icon={<ChartNoAxesCombined size={18} />}>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="font-medium">Observed facts</h3>
                <ul className="mt-3 space-y-3">
                  {observations.map((item) => (
                    <li key={item} className="text-sm leading-6 text-slate-700">{item}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="font-medium">Hypotheses under observation</h3>
                <ul className="mt-3 space-y-3">
                  {hypotheses.map((item) => (
                    <li key={item} className="text-sm leading-6 text-slate-700">{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Section>

          <Section title="Graph Viewer" icon={<GitBranch size={18} />}>
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-4 flex flex-wrap gap-2">
                {["Customer x Issue", "Competitor Impact", "KPI Causal", "Hypothesis", "Gap Graph"].map((tab) => (
                  <Pill key={tab}>{tab}</Pill>
                ))}
              </div>
              <div className="relative h-72 overflow-hidden rounded-md border border-slate-200 bg-slate-50">
                <svg className="absolute inset-0 h-full w-full" role="img" aria-label="Knowledge graph relationships">
                  <line x1="16%" y1="26%" x2="48%" y2="18%" stroke="#94a3b8" strokeWidth="2" />
                  <line x1="52%" y1="20%" x2="76%" y2="30%" stroke="#94a3b8" strokeWidth="2" />
                  <line x1="49%" y1="21%" x2="62%" y2="72%" stroke="#94a3b8" strokeWidth="2" />
                  <line x1="30%" y1="72%" x2="60%" y2="72%" stroke="#f59e0b" strokeWidth="2" strokeDasharray="5 5" />
                </svg>
                {graphNodes.map((node) => (
                  <div
                    key={node.label}
                    className="absolute max-w-36 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-medium shadow-sm"
                    style={{ left: node.x, top: node.y }}
                  >
                    {node.label}
                  </div>
                ))}
              </div>
            </div>
          </Section>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-20 lg:self-start">
          <Section title="Business Intake" icon={<AudioLines size={18} />}>
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="space-y-3">
                <div className="max-w-[85%] rounded-lg bg-slate-100 p-3 text-sm leading-6">
                  今日、顧客から普段と違う反応や相談はありましたか。
                </div>
                <div className="ml-auto max-w-[85%] rounded-lg bg-slate-950 p-3 text-sm leading-6 text-white">
                  子育て世帯からオンライン服薬指導の相談が増えました。
                </div>
                <div className="max-w-[85%] rounded-lg bg-slate-100 p-3 text-sm leading-6">
                  どの時間帯、商品、競合名と関係していましたか。
                </div>
              </div>
              <button className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white">
                <AudioLines size={16} />
                Simulate voice intake
              </button>
            </div>
          </Section>

          <Section title="Evidence Search" icon={<FileSearch size={18} />}>
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-500">
                <Search size={16} />
                price competitor wait time
              </div>
              <div className="mt-4 space-y-3">
                {evidence.map((item) => (
                  <article key={item.snippet} className="border-t border-slate-100 pt-3">
                    <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{item.source}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-700">{item.snippet}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {item.tags.map((tag) => <Pill key={tag}>{tag}</Pill>)}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </Section>

          <Section title="Weekly Report" icon={<MessageSquareText size={18} />}>
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="text-sm leading-6 text-slate-700">
                待ち時間と競合利便性に関する言及が増加。因果は未確定のため、次週は比較理由と再来店意向を同時に観察します。
              </p>
              <div className="mt-4 grid gap-2">
                <Pill>Facts separated</Pill>
                <Pill>Hypotheses labeled</Pill>
                <Pill>Evidence linked</Pill>
              </div>
            </div>
          </Section>

          <Section title="Report Copilot" icon={<Bot size={18} />}>
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="text-sm font-medium">なぜ価格・待ち時間関連の発言が増えた？</p>
              <p className="mt-3 text-sm leading-6 text-slate-700">
                観察事実では競合比較の発言が確認できます。競合の利便性が影響している可能性は仮説として扱い、次回の観察で比較理由を確認してください。
              </p>
            </div>
          </Section>
        </aside>
      </div>
    </main>
  );
}
