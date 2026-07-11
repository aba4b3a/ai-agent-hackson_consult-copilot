"use client";

import {
  FiBarChart2,
  FiBookOpen,
  FiCheckCircle,
  FiChevronLeft,
  FiChevronRight,
  FiHome,
  FiClipboard,
  FiMessageSquare,
  FiSearch,
} from "react-icons/fi";
import type { IconType } from "react-icons";
import { useNavVisibility } from "@/components/feature/discovery/NavVisibilityProvider";

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
  { key: "home", label: "発見", href: "/", icon: FiHome },
  { key: "intake", label: "初期把握", href: "/intake", icon: FiClipboard },
  { key: "research", label: "質問", href: "/research", icon: FiSearch },
  { key: "knowledge", label: "知識", href: "/knowledge", icon: FiBarChart2 },
  { key: "wiki", label: "記録", href: "/wiki", icon: FiBookOpen },
  { key: "approvals", label: "確認", href: "/approvals", icon: FiCheckCircle },
  { key: "report", label: "月次", href: "/report", icon: FiMessageSquare },
];

export const BottomNav = ({ active = "home" }: BottomNavProps) => {
  const { isNavCollapsed, toggleNav } = useNavVisibility();

  return (
    <>
      <nav
        className={`fixed inset-x-0 bottom-0 z-30 border-t border-slate-100 bg-white/95 px-4 py-2 backdrop-blur md:inset-y-0 md:left-0 md:right-auto md:w-32 md:border-r md:border-t-0 md:px-0 md:py-4 lg:px-6 ${
          isNavCollapsed ? "md:hidden" : ""
        }`}
      >
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

      {/* 画面幅が狭いと左サイドメニューが本文に被るため、md以上でのみ開閉トグルを出す */}
      <button
        type="button"
        onClick={toggleNav}
        className={`fixed top-1/2 z-40 hidden h-8 w-8 -translate-y-1/2 place-items-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-md transition hover:bg-slate-50 md:grid ${
          isNavCollapsed ? "left-2" : "left-[7.25rem]"
        }`}
        aria-label={isNavCollapsed ? "サイドメニューを表示" : "サイドメニューを非表示"}
        title={isNavCollapsed ? "サイドメニューを表示" : "サイドメニューを非表示"}
      >
        {isNavCollapsed ? (
          <FiChevronRight aria-hidden="true" className="h-4 w-4" />
        ) : (
          <FiChevronLeft aria-hidden="true" className="h-4 w-4" />
        )}
      </button>
    </>
  );
};
