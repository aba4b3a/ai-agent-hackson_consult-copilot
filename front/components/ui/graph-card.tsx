import { cn } from "./cn";

export type GraphCardNode = {
  id: string;
  label: string;
  type?: string;
};

export type GraphCardEdge = {
  source: string;
  target: string;
  fact_or_hypothesis?: string;
};

/**
 * Bounded mini network view for demo clarity (not a full graph renderer).
 * Nodes are laid out on a circle with a deterministic order so the same slice
 * always renders identically. Hypothesis edges are drawn dashed to keep the
 * fact/hypothesis distinction visible.
 */
export function GraphCard({
  nodes,
  edges,
  limit = 8,
  className,
}: {
  nodes: GraphCardNode[];
  edges: GraphCardEdge[];
  limit?: number;
  className?: string;
}) {
  const shown = nodes.slice(0, limit);
  const positions = new Map<string, { x: number; y: number }>();
  const count = shown.length;

  shown.forEach((node, index) => {
    if (count === 1) {
      positions.set(node.id, { x: 50, y: 50 });
      return;
    }
    const angle = (2 * Math.PI * index) / count - Math.PI / 2;
    positions.set(node.id, {
      x: 50 + 38 * Math.cos(angle),
      y: 50 + 38 * Math.sin(angle),
    });
  });

  const visibleEdges = edges.filter(
    (edge) => positions.has(edge.source) && positions.has(edge.target),
  );

  return (
    <div
      className={cn(
        "relative h-72 overflow-hidden rounded-md border border-border bg-background",
        className,
      )}
    >
      <svg className="absolute inset-0 h-full w-full" role="img" aria-label="Knowledge graph relationships">
        {visibleEdges.map((edge, index) => {
          const from = positions.get(edge.source)!;
          const to = positions.get(edge.target)!;
          const isHypothesis = edge.fact_or_hypothesis === "hypothesis";
          return (
            <line
              key={`${edge.source}-${edge.target}-${index}`}
              x1={`${from.x}%`}
              y1={`${from.y}%`}
              x2={`${to.x}%`}
              y2={`${to.y}%`}
              stroke={isHypothesis ? "var(--color-warning)" : "var(--color-border)"}
              strokeWidth={2}
              strokeDasharray={isHypothesis ? "5 5" : undefined}
            />
          );
        })}
      </svg>
      {shown.map((node) => {
        const pos = positions.get(node.id)!;
        return (
          <div
            key={node.id}
            className="absolute max-w-36 -translate-x-1/2 -translate-y-1/2 rounded-md border border-border bg-surface px-3 py-2 text-xs font-medium shadow-sm"
            style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
          >
            {node.label}
          </div>
        );
      })}
    </div>
  );
}
