import { CostGuardCard } from "@/components/cost-guard-card";
import { QualityScoreCard } from "@/components/quality-score-card";
import { ReleaseGateCard } from "@/components/release-gate-card";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <section className="mx-auto max-w-6xl space-y-6">
        <div>
          <p className="text-sm font-medium text-slate-500">AI QualityOps Agent</p>
          <h1 className="text-3xl font-bold text-slate-900">Quality Dashboard</h1>
          <p className="mt-2 text-slate-600">
            PR品質、AI評価、リリース判定、コストガードを確認します。
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <QualityScoreCard />
          <ReleaseGateCard />
          <CostGuardCard />
        </div>
      </section>
    </main>
  );
}
