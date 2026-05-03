import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";

import {
  createStory,
  deleteStory,
  getStory,
  listEpics,
  listStories,
  patchStory,
  type PaginatedResult,
  type Story,
  type StoryCreateBody,
  type StoryFilters,
  type StoryPatchBody,
} from "@/lib/api";
import type { InfiniteData } from "@tanstack/react-query";
import { extractErrorMessage } from "@/lib/errors";
import { invalidateStoryRelated } from "@/lib/query-helpers";

// ─── Read hooks ───────────────────────────────────────────────────────────────

export function useInfiniteStories(projectId: string, filters: StoryFilters = {}) {
  return useInfiniteQuery({
    queryKey: ["stories", projectId, filters],
    queryFn: ({ pageParam }) =>
      listStories(projectId, { ...filters, page: pageParam as number }),
    initialPageParam: 1,
    getNextPageParam: (lastPage: PaginatedResult<Story>) => {
      const { page, totalPages } = lastPage.pagination;
      return page < totalPages ? page + 1 : undefined;
    },
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

export function useStories(projectId: string, filters: StoryFilters = {}) {
  return useQuery({
    queryKey: ["stories", projectId, filters],
    queryFn: () => listStories(projectId, filters),
    enabled: !!projectId,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useStory(projectId: string, storyId: string) {
  return useQuery({
    queryKey: ["story", storyId],
    queryFn: () => getStory(projectId, storyId),
    enabled: !!projectId && !!storyId,
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

/** Alias kept for backward-compat with board page (1-param) and detail page (2-param). */
export function useUpdateStory(projectId: string, storyId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (bodyOrObj: StoryPatchBody | { storyId: string; body: StoryPatchBody }) => {
      if ("storyId" in bodyOrObj && "body" in bodyOrObj) {
        return patchStory(projectId, bodyOrObj.storyId, bodyOrObj.body);
      }
      return patchStory(projectId, storyId!, bodyOrObj as StoryPatchBody);
    },
    onSuccess: (_data, variables) => {
      const resolvedId = storyId ?? ("storyId" in variables ? (variables as { storyId: string }).storyId : undefined);
      invalidateStoryRelated(qc, projectId, resolvedId);
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update story")),
  });
}

/**
 * Optimistic-update variant used by the Kanban board drag-drop.
 * Immediately moves the card in the infinite-query cache, then
 * rolls back on error.
 */
export function useOptimisticPatchStory(
  projectId: string,
  filters: StoryFilters,
) {
  const qc = useQueryClient();
  const qKey = ["stories", projectId, filters] as const;
  return useMutation({
    mutationFn: ({ storyId, body }: { storyId: string; body: StoryPatchBody }) =>
      patchStory(projectId, storyId, body),
    onMutate: async ({ storyId, body }) => {
      await qc.cancelQueries({ queryKey: qKey });
      const previous = qc.getQueryData<InfiniteData<PaginatedResult<Story>>>(qKey);
      if (previous && body.status) {
        qc.setQueryData<InfiniteData<PaginatedResult<Story>>>(qKey, (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              items: page.items.map((s) =>
                s.id === storyId ? { ...s, status: body.status! } : s,
              ),
            })),
          };
        });
      }
      return { previous };
    },
    onError: (err, _vars, ctx) => {
      if (ctx?.previous) qc.setQueryData(qKey, ctx.previous);
      toast.error(extractErrorMessage(err, "Failed to update story"));
    },
    onSettled: () => {
      invalidateStoryRelated(qc, projectId);
    },
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
