import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  listEpics,
  createEpic,
  updateEpic,
  deleteEpic,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useEpics(projectId: string, page = 1) {
  return useQuery({
    queryKey: ["epics", projectId, page],
    queryFn: () => listEpics(projectId, page),
    enabled: !!projectId,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useCreateEpic(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; description?: string | null }) =>
      createEpic(projectId, body),
    onSuccess: () => {
      toast.success("Epic created");
      qc.invalidateQueries({ queryKey: ["epics", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to create epic")),
  });
}

export function useUpdateEpic(projectId: string, epicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name?: string; description?: string | null }) =>
      updateEpic(projectId, epicId, body),
    onSuccess: () => {
      toast.success("Epic updated");
      qc.invalidateQueries({ queryKey: ["epics", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update epic")),
  });
}

export function useDeleteEpic(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (epicId: string) => deleteEpic(projectId, epicId),
    onSuccess: () => {
      toast.success("Epic deleted");
      qc.invalidateQueries({ queryKey: ["epics", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete epic")),
  });
}
