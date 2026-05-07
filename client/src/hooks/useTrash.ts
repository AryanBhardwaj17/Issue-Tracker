import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { listDeletedStories, restoreStory } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useTrash(projectId: string) {
  return useQuery({
    queryKey: ["trash", projectId],
    queryFn: () => listDeletedStories(projectId),
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

export function useRestoreStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (storyId: string) => restoreStory(projectId, storyId),
    onSuccess: () => {
      toast.success("Story restored");
      qc.invalidateQueries({ queryKey: ["trash", projectId] });
      qc.invalidateQueries({ queryKey: ["stories", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to restore story")),
  });
}
