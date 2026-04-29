"use client";
 
import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
 
export default function Navbar() {
  const { user } = useAuthStore();

 
  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
      <h1 className="text-sm font-medium text-gray-700">
        Issue Tracker
      </h1>

      <div className="flex items-center gap-2">
        <Link
          href="/profile"
          className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-200 text-xs font-semibold text-gray-700">
            {user?.name?.[0]?.toUpperCase() ?? "U"}
          </span>
          <span>{user?.name ?? ""}</span>
        </Link>
      </div>
    </header>
  );
}
 