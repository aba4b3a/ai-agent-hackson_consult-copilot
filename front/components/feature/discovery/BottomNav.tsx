type BottomNavKey =
  | "home"
  | "intake"
  | "knowledge"
  | "graph"
  | "report"
  | "approvals"
  | "research"
  | "wiki";

type BottomNavProps = {
  active?: BottomNavKey;
};

const tabs: { key: BottomNavKey; label: string; href: string }[] = [
  { key: "home", label: "Home", href: "/" },
  { key: "intake", label: "Intake", href: "/intake" },
  { key: "research", label: "Research", href: "/research" },
  { key: "knowledge", label: "Knowledge", href: "/knowledge" },
  { key: "graph", label: "Graph", href: "/graph" },
  { key: "wiki", label: "Wiki", href: "/wiki" },
  { key: "approvals", label: "Approve", href: "/approvals" },
  { key: "report", label: "Report", href: "/report" },
];

export const BottomNav = ({ active = "home" }: BottomNavProps) => {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-100 bg-white/95 px-4 py-2 backdrop-blur md:inset-y-0 md:left-0 md:right-auto md:w-32 md:border-r md:border-t-0 md:px-0 md:py-4 lg:px-6">
      <div className="mx-auto grid w-full max-w-[min(100%,640px)] grid-cols-8 gap-1 md:mx-0 md:max-w-none md:flex md:flex-col md:gap-3">
        {tabs.map((tab) => {
          const isActive = tab.key === active;

          return (
            <a
              key={tab.key}
              className="flex flex-col items-center gap-1 rounded-3xl px-2 py-2 transition hover:bg-slate-50 md:flex-row md:justify-start md:px-3 md:py-3 md:rounded-full"
              href={tab.href}
              aria-current={isActive ? "page" : undefined}
            >
              <span className={`h-4 w-4 rounded-full md:h-5 md:w-5 ${isActive ? "bg-blue-600" : "bg-slate-300"}`} />
              <span className={`text-[8px] font-bold ${isActive ? "text-blue-600" : "text-slate-400"} md:text-[11px]`}>
                {tab.label}
              </span>
            </a>
          );
        })}
      </div>
    </nav>
  );
};
