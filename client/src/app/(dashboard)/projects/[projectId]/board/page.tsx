"use client";

import { use, useCallback, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useProject, useProjectMembers } from "@/hooks/useProject";
import { useEpics } from "@/hooks/useEpics";
import { useInfiniteStories, useCreateStory, useUpdateStory } from "@/hooks/useStories";
import { useAuthStore } from "@/stores/authStore";
import FilterBar, { type BoardFilters } from "@/components/board/FilterBar";
import KanbanColumn from "@/components/board/KanbanColumn";
import CreateStoryDialog from "@/components/board/CreateStoryDialog";
import type { StoryStatus, Story } from "@/lib/api";

// ── Column definitions ────────────────────────────────────────────────────────

const COLUMNS: { id: StoryStatus; label: string }[] = [
  { id: "todo", label: "To Do" },
  { id: "in_progress", label: "In Progress" },
  { id: "in_review", label: "In Review" },
  { id: "testing", label: "Testing" },
  { id: "ready_for_prod", label: "Ready for Prod" },
  { id: "done", label: "Done" },
];

const ALL_STATUSES = COLUMNS.map((c) => c.id);

// ── Helpers ───────────────────────────────────────────────────────────────────

function filtersFromSearchParams(sp: URLSearchParams): BoardFilters {
  return {
    search: sp.get("search") ?? "",
    assigneeId: sp.get("assigneeId"),
    assigneeName: sp.get("assigneeName"),
    epicId: sp.get("epicId"),
    epicName: sp.get("epicName"),
    priority: sp.getAll("priority"),
    status: sp.getAll("status"),
  };
}

function filtersToSearchParams(f: BoardFilters): URLSearchParams {
  const sp = new URLSearchParams();
  if (f.search) sp.set("search", f.search);
  if (f.assigneeId) {
    sp.set("assigneeId", f.assigneeId);
    if (f.assigneeName) sp.set("assigneeName", f.assigneeName);
  }
  if (f.epicId) {
    sp.set("epicId", f.epicId);
    if (f.epicName) sp.set("epicName", f.epicName);
  }
  f.priority.forEach((p) => sp.append("priority", p));
  f.status.forEach((s) => sp.append("status", s));
  return sp;
}

// ── Board Page ────────────────────────────────────────────────────────────────

export default function BoardPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentUser = useAuthStore((s) => s.user);
  const [showCreate, setShowCreate] = useState(false);

  // Filters — sourced from URL
  const filters = filtersFromSearchParams(searchParams);

  const handleFiltersChange = useCallback(
    (next: BoardFilters) => {
      router.replace(`?${filtersToSearchParams(next).toString()}`, { scroll: false });
    },
    [router],
  );

  // ── Data fetching ──────────────────────────────────────────────────────────
  const { data: project } = useProject(projectId);
  const { data: members = [] } = useProjectMembers(projectId);
  // Fetch up to 100 epics so filter bar can list them all
  const { data: epicsPage } = useEpics(projectId, 1);
  const epics = epicsPage?.items ?? [];

  // Build API filter params
  const apiFilters = {
    ...(filters.search && { search: filters.search }),
    ...(filters.assigneeId && { assigneeId: [filters.assigneeId] }),
    ...(filters.epicId && { epicId: [filters.epicId] }),
    ...(filters.priority.length > 0 && { priority: filters.priority }),
    // If user has selected specific statuses, use those; otherwise fetch all board statuses
    status: filters.status.length > 0 ? filters.status : ALL_STATUSES,
    sortBy: "priority" as const,
    sortOrder: "desc" as const,
  };

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useInfiniteStories(projectId, apiFilters);

  const createMutation = useCreateStory(projectId);
  const updateMutation = useUpdateStory(projectId, apiFilters);

  // Flatten all pages
  const allStories: Story[] = data?.pages.flatMap((p) => p.items) ?? [];

  // Group by status
  const grouped = Object.fromEntries(
    COLUMNS.map((c) => [c.id, allStories.filter((s) => s.status === c.id)]),
  ) as Record<StoryStatus, Story[]>;

  // ── DnD ───────────────────────────────────────────────────────────────────
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;

    const storyId = active.id as string;
    const newStatus = over.id as StoryStatus;
    const story = allStories.find((s) => s.id === storyId);
    if (!story || story.status === newStatus) return;

    updateMutation.mutate({ storyId, body: { status: newStatus } });
  }

  // ── Role ──────────────────────────────────────────────────────────────────
  const role = project?.role ?? "member";
  const currentUserId = currentUser?.id ?? "";

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Filter bar */}
      <FilterBar
        filters={filters}
        onFiltersChange={handleFiltersChange}
        members={members}
        epics={epics}
        onCreateStory={() => setShowCreate(true)}
      />

      {/* Board */}
      {isError ? (
        <div className="flex items-center justify-center py-20">
          <p className="text-sm text-red-500">Failed to load stories.</p>
        </div>
      ) : isLoading ? (
        <div className="flex items-center justify-center py-20">
          <p className="text-sm text-gray-400">Loading board…</p>
        </div>
      ) : (
        <>
          <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
            <div className="flex gap-4 overflow-x-auto pb-4">
              {COLUMNS.map((col) => (
                <KanbanColumn
                  key={col.id}
                  id={col.id}
                  label={col.label}
                  stories={grouped[col.id]}
                  currentUserId={currentUserId}
                  role={role}
                />
              ))}
            </div>
          </DndContext>

          {/* Load More */}
          {hasNextPage && (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isFetchingNextPage ? "Loading…" : "Load More"}
              </button>
            </div>
          )}
        </>
      )}

      {/* Create story dialog */}
      {showCreate && (
        <CreateStoryDialog
          members={members}
          epics={epics}
          isLoading={createMutation.isPending}
          onClose={() => setShowCreate(false)}
          onSubmit={(body) => {
            createMutation.mutate(body, {
              onSuccess: () => setShowCreate(false),
            });
          }}
        />
      )}
    </div>
  );
}
