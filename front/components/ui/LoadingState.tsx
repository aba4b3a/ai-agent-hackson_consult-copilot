import { PhoneFrame } from "@/components/ui/PhoneFrame";

export const LoadingState = ({ message, isError = false }: { message: string; isError?: boolean }) => (
  <PhoneFrame>
    <div className={`flex min-h-screen items-center justify-center px-6 text-center text-sm font-bold md:min-h-[720px] ${isError ? "text-rose-500" : "text-slate-500"}`}>
      {message}
    </div>
  </PhoneFrame>
);
