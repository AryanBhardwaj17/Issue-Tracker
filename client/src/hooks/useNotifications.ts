import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useNotifications(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["notifications", page, pageSize],
    queryFn: () => fetchNotifications(page, pageSize),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notificationUnreadCount"],
    queryFn: fetchUnreadCount,
    refetchInterval: 45_000,
    staleTime: 30_000,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => markNotificationRead(notificationId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notificationUnreadCount"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to mark notification as read")),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: (count) => {
      if (count > 0) toast.success(`Marked ${count} notification${count > 1 ? "s" : ""} as read`);
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notificationUnreadCount"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to mark all as read")),
  });
}
