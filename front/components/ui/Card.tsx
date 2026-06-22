export const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => {
  return <section className={`rounded-[22px] bg-white p-4 shadow-[0_12px_28px_rgba(15,23,42,0.05)] ${className}`}>{children}</section>;
};
