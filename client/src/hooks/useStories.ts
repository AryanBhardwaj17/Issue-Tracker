import {
  useMutation,
  useQuery,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";

import {
  createStory,
  deleteStory,
  listEpics,
  listStories,
  patchStory,
  type Story,
  type StoryCreateBody,
  type StoryFilters,
  type StoryPatchBody,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { invalidateStoryRelated } from "@/lib/query-helpers";

// ─── Read hooks ───────────────────────────────────────────────────────────────

export function useStories(projectId: string, filters: StoryFilters = {}) {
  return useQuery({
    queryKey: ["stories", projectId, filters],
    queryFn: () => listStories(projectId, filters),
    enabled: !!projectId,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

/**
 * Fetches all epics (up to 100) for use in dropdowns and the epics panel.
 * Separate from the paged useEpics hook to avoid polluting pagination state.
 */
export function useAllEpics(projectId: string) {
  return useQuery({
    queryKey: ["epics", projectId, "all"],
    queryFn: () => listEpics(projectId, 1, 100),
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

// ─── Mutation hooks ───────────────────────────────────────────────────────────

export function useCreateStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: StoryCreateBody) => createStory(projectId, body),
    onSuccess: () => {
      toast.success("Story created");
      invalidateStoryRelated(qc, projectId);
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to create story")),
  });
}

export function usePatchStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ storyId, body }: { storyId: string; body: StoryPatchBody }) =>
      patchStory(projectId, storyId, body),
    onSuccess: (_data, variables) => {
      invalidateStoryRelated(qc, projectId, variables.storyId);
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update story")),
  });
}

/**
 * Convenience wrapper for the common "Move to Todo" action from Backlog.
 * Always patches status → "todo".
 */
export function useMoveToTodo(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (storyId: string) =>
      patchStory(projectId, storyId, { status: "todo" }),
    onSuccess: () => {
      toast.success("Moved to board");
      invalidateStoryRelated(qc, projectId);
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to move story")),
  });
}

export function useDeleteStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (storyId: string) => deleteStory(projectId, storyId),
    onSuccess: () => {
      toast.success("Story deleted");
      invalidateStoryRelated(qc, projectId);
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete story")),
  });
}
