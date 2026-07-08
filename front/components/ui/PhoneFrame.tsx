"use client";

import { useNavVisibility } from "@/components/feature/discovery/NavVisibilityProvider";

export const PhoneFrame = ({ children }: { children: React.ReactNode }) => {
  const { isNavCollapsed } = useNavVisibility();

  return (
    <main
      className={`min-h-screen bg-slate-100 px-4 py-5 text-slate-950 sm:px-6 lg:px-10 xl:pr-[28rem] ${
        isNavCollapsed ? "md:px-8" : "md:px-8 md:pl-[10rem]"
      }`}
    >
      <div className="mx-auto w-full max-w-[min(100%,1200px)]">{children}</div>
    </main>
  );
};
