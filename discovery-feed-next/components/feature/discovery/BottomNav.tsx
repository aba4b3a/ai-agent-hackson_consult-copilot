type BottomNavKey = "home" | "knowledge" | "graph" | "report";

type BottomNavProps = {
  active?: BottomNavKey;
};

const tabs: { key: BottomNavKey; label: string; href: string }[] = [
  { key: "home", label: "Home", href: "/" },
  { key: "knowledge", label: "Knowledge", href: "/knowledge" },
  { key: "graph", label: "Graph", href: "/graph" },
  { key: "report", label: "Report", href: "/report" },
];

export const BottomNav = ({ active = "home" }: BottomNavProps) => {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-100 bg-white/95 px-5 py-2 backdrop-blur md:hidden">
      <div className="mx-auto grid max-w-[430px] grid-cols-4 gap-2">
        {tabs.map((tab) => {
          const isActive = tab.key === active;

          return (
            <a key={tab.key} className="flex flex-col items-center gap-1" href={tab.href} aria-current={isActive ? "page" : undefined}>
              <span className={`h-5 w-5 rounded-full ${isActive ? "bg-blue-600" : "bg-slate-300"}`} />
              <span className={`text-[8px] font-bold ${isActive ? "text-blue-600" : "text-slate-400"}`}>{tab.label}</span>
            </a>
          );
        })}
      </div>
    </nav>
  );
};
