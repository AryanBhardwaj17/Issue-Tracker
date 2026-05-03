import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
  type InfiniteData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  listStories,
  createStory,
  updateStory,
  type Story,
  type StoryFilters,
  type PaginatedResult,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

const BOARD_PAGE_SIZE = 100;

export function storiesQueryKey(projectId: string, filters: StoryFilters) {
  return ["stories", projectId, filters] as const;
}

// ── useInfiniteStories ────────────────────────────────────────────────────────

export function useInfiniteStories(projectId: string, filters: StoryFilters) {
  return useInfiniteQuery({
    queryKey: storiesQueryKey(projectId, filters),
    queryFn: ({ pageParam }) =>
      listStories(projectId, {
        ...filters,
        page: pageParam as number,
        pageSize: BOARD_PAGE_SIZE,
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const { page, totalPages } = lastPage.pagination;
      return page < totalPages ? page + 1 : undefined;
    },
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

// ── useCreateStory ────────────────────────────────────────────────────────────

export function useCreateStory(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof createStory>[1]) =>
      createStory(projectId, body),
    onSuccess: () => {
      toast.success("Story created");
      qc.invalidateQueries({ queryKey: ["stories", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to create story")),
  });
}

// ── useUpdateStory (with optimistic update for drag-drop) ─────────────────────

export function useUpdateStory(projectId: string, filters: StoryFilters) {
  const qc = useQueryClient();
  const qKey = storiesQueryKey(projectId, filters);

  return useMutation({
    mutationFn: ({
      storyId,
      body,
    }: {
      storyId: string;
      body: Parameters<typeof updateStory>[2];
    }) => updateStory(projectId, storyId, body),

    onMutate: async ({ storyId, body }) => {
      await qc.cancelQueries({ queryKey: qKey });
      const previous =
        qc.getQueryData<InfiniteData<PaginatedResult<Story>>>(qKey);

      if (previous && body.status) {
        qc.setQueryData<InfiniteData<PaginatedResult<Story>>>(qKey, (old) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              items: page.items.map((s) =>
                s.id === storyId
                  ? { ...s, status: body.status as Story["status"] }
                  : s,
              ),
            })),
          };
        });
      }
      return { previous };
    },

    onError: (err, _vars, ctx) => {
      if (ctx?.previous) {
        qc.setQueryData(qKey, ctx.previous);
      }
      toast.error(extractErrorMessage(err, "Failed to update story"));
    },

    onSettled: () => {
      qc.invalidateQueries({ queryKey: qKey });
    },
  });
}
