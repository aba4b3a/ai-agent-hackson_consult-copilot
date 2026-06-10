export function ReleaseGateCard() {
  return (
    <article className="rounded-2xl border bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-slate-500">Release Gate</p>
      <p className="mt-3 text-2xl font-bold text-slate-900">Human Approval Required</p>
      <p className="mt-2 text-sm text-slate-600">
        AIはGo / No-Goを提案し、最終判断は人間が行います。
      </p>
    </article>
  );
}
