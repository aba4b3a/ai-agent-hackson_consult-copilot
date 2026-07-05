import {
  FiBarChart2,
  FiBookOpen,
  FiCheckCircle,
  FiHome,
  FiClipboard,
  FiMessageSquare,
  FiSearch,
} from "react-icons/fi";
import type { IconType } from "react-icons";

export type BottomNavKey =
  | "home"
  | "intake"
  | "knowledge"
  | "report"
  | "approvals"
  | "research"
  | "wiki";

type BottomNavProps = {
  active?: BottomNavKey;
};

const tabs: { key: BottomNavKey; label: string; href: string; icon: IconType }[] = [
  { key: "home", label: "Home", href: "/", icon: FiHome },
  { key: "intake", label: "Intake", href: "/intake", icon: FiClipboard },
  { key: "research", label: "Research", href: "/research", icon: FiSearch },
  { key: "knowledge", label: "Knowledge", href: "/knowledge", icon: FiBarChart2 },
  { key: "wiki", label: "Wiki", href: "/wiki", icon: FiBookOpen },
  { key: "approvals", label: "Approve", href: "/approvals", icon: FiCheckCircle },
  { key: "report", label: "Report", href: "/report", icon: FiMessageSquare },
];

export const BottomNav = ({ active = "home" }: BottomNavProps) => {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-100 bg-white/95 px-4 py-2 backdrop-blur md:inset-y-0 md:left-0 md:right-auto md:w-32 md:border-r md:border-t-0 md:px-0 md:py-4 lg:px-6">
      <div className="mx-auto grid w-full max-w-[min(100%,640px)] grid-cols-8 gap-1 md:mx-0 md:max-w-none md:flex md:flex-col md:gap-3">
        {tabs.map((tab) => {
          const isActive = tab.key === active;
          const Icon = tab.icon;

          return (
            <a
              key={tab.key}
              className={`flex flex-col items-center gap-1 rounded-3xl px-2 py-2 transition md:flex-row md:justify-start md:rounded-full md:px-3 md:py-3 ${
                isActive ? "bg-blue-50" : "hover:bg-slate-50"
              }`}
              href={tab.href}
              aria-current={isActive ? "page" : undefined}
              title={tab.label}
            >
              <span
                className={`grid h-6 w-6 place-items-center rounded-full transition md:h-8 md:w-8 ${
                  isActive ? "bg-blue-600 text-white shadow-[0_8px_18px_rgba(37,99,235,0.22)]" : "bg-slate-100 text-slate-400"
                }`}
              >
                <Icon aria-hidden="true" className="h-3.5 w-3.5 md:h-4 md:w-4" />
              </span>
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
