export const PhoneFrame = ({ children }: { children: React.ReactNode }) => {
  return (
    <main className="min-h-screen bg-slate-100 px-0 py-0 md:flex md:items-start md:justify-center md:px-8 md:py-10">
      <div className="relative mx-auto min-h-screen w-full overflow-hidden bg-[#f7fbff] shadow-none md:min-h-[720px] md:max-w-[430px] md:rounded-[42px] md:border-[10px] md:border-slate-950 md:shadow-2xl">
        <div className="hidden md:absolute md:left-1/2 md:top-2 md:z-20 md:block md:h-1.5 md:w-24 md:-translate-x-1/2 md:rounded-full md:bg-slate-950/70" />
        {children}
      </div>
    </main>
  );
};
