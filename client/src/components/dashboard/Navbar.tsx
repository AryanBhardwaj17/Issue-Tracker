"use client";
 
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
 
export default function Navbar() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
 
  async function handleLogout() {
    await logout();
    router.replace("/login");
  }
 
  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
      <h1 className="text-sm font-medium text-gray-700">
        {user?.name ?? ""}
      </h1>
 
      <button
        onClick={handleLogout}
        className="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
      >
        Logout
      </button>
    </header>
  );
}
 