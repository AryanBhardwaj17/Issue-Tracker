import { useProjectMembers } from "./useProject";
import { useAuthStore } from "@/stores/authStore";

/**
 * Derives the current user's project role from the members list + auth store.
 * Returns { role, userId, isLoading }.
 */
export function useMembership(projectId: string) {
  const user = useAuthStore((s) => s.user);
  const { data: members, isLoading } = useProjectMembers(projectId);

  const me = members?.find((m) => m.userId === user?.id);

  return {
    role: (me?.role ?? "member") as "owner" | "member",
    userId: user?.id ?? "",
    isLoading,
  };
}
