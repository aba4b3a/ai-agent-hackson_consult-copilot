import { BottomNav, type BottomNavKey } from "@/components/feature/discovery/BottomNav";
import { PhoneFrame } from "@/components/ui/PhoneFrame";

export const LoadingState = ({
  message,
  isError = false,
  active,
}: {
  message: string;
  isError?: boolean;
  active?: BottomNavKey;
}) => (
  <PhoneFrame>
    <div className={`flex min-h-screen items-center justify-center px-6 text-center text-sm font-bold md:min-h-[720px] ${isError ? "text-rose-500" : "text-slate-500"}`}>
      {message}
    </div>
    <BottomNav active={active} />
  </PhoneFrame>
);
