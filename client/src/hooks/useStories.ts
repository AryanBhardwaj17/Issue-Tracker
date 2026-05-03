import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  getStory,
  listStories,
  createStory,
  updateStory,
  deleteStory,
  type StoryCreatePayload,
  type StoryPatchPayload,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useStories(
  projectId: string,
  page = 1,
  filters?: { status?: string; priority?: string; epicId?: string; assigneeId?: string },
) {
  return useQuery({
    queryKey: ["stories", projectId, page, filters],
    queryFn: () => listStories(projectId, page, 25, filters),
    enabled: !!projectId,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useStory(projectId: string, storyId: string) {
  return useQuery({
    queryKey: ["story", projectId, storyId],
    queryFn: () => getStory(projectId, storyId),
    enabled: !!projectId && !!storyId,
  });
}

export function useCreateStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: StoryCreatePayload) => createStory(projectId, body),
    onSuccess: () => {
      toast.success("Story created");
      qc.invalidateQueries({ queryKey: ["stories", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to create story")),
  });
}

export function useUpdateStory(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: StoryPatchPayload) => updateStory(projectId, storyId, body),
    onSuccess: () => {
      toast.success("Story updated");
      qc.invalidateQueries({ queryKey: ["stories", projectId] });
      qc.invalidateQueries({ queryKey: ["story", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update story")),
  });
}

export function useDeleteStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (storyId: string) => deleteStory(projectId, storyId),
    onSuccess: () => {
      toast.success("Story deleted");
      qc.invalidateQueries({ queryKey: ["stories", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete story")),
  });
}
