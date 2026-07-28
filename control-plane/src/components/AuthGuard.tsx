"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, isLoaded, load } = useAuth();

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (isLoaded && !token) router.replace("/login");
  }, [isLoaded, token, router]);

  if (!isLoaded) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  if (!token) return null;
  return <>{children}</>;
}
