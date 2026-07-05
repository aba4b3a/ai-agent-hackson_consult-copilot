"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function KnowledgeGraphPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/knowledge");
  }, [router]);

  return <div className="grid min-h-screen place-items-center text-sm font-bold text-slate-500">Redirecting...</div>;
}
