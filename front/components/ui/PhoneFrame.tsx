export const PhoneFrame = ({ children }: { children: React.ReactNode }) => {
  return (
    <main className="min-h-screen bg-slate-100 px-4 py-5 text-slate-950 sm:px-6 md:px-8 md:pl-[10rem] lg:px-10 xl:px-12">
      <div className="mx-auto w-full max-w-[min(100%,1200px)]">{children}</div>
    </main>
  );
};
