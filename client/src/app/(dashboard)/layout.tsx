"use client";
 
import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import Navbar from "@/components/dashboard/Navbar";
 
export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, hydrate, isHydrated } = useAuthStore();
 
  useEffect(() => {
    hydrate();
  }, [hydrate]);
 
  useEffect(() => {
    if (isHydrated && !user) {
      router.replace("/login");
    }
  }, [isHydrated, user, router]);
 
  if (!isHydrated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
      </div>
    );
  }
 
  return (
    <div className="flex min-h-screen">
      {/* Sidebar placeholder */}
      <aside className="hidden w-64 border-r border-gray-200 bg-white md:block">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900">
            Issue Tracker
          </h2>
        </div>
      </aside>
 
      {/* Main content */}
      <div className="flex flex-1 flex-col">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}