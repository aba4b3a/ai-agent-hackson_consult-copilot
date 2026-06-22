import type { ReportMessage } from "@/lib/schemas";
import {TbBrandBaidu} from "react-icons/tb";

const userBubbleClass = "max-w-[85%] md:max-w-[72%] rounded-[20px] rounded-tr-md bg-blue-600 px-4 py-3 text-white shadow-[0_14px_28px_rgba(37,99,235,0.22)]";
const agentBubbleClass = "max-w-[85%] md:max-w-[68%] rounded-[20px] rounded-tl-md bg-white px-4 py-3 shadow-[0_10px_24px_rgba(15,23,42,0.05)]";

export const ChatBubble = ({ message }: { message: ReportMessage }) => {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className={userBubbleClass}>
          <p className="text-[12px] font-black leading-relaxed md:text-sm">{message.body}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-blue-100 text-base font-black text-blue-500">
        <TbBrandBaidu />
      </span>
      <div className={agentBubbleClass}>
        <p className="text-[11px] font-extrabold leading-relaxed text-slate-700 md:text-sm">{message.body}</p>
      </div>
    </div>
  );
};
