"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { useProject } from "@/hooks/useProject";
import { useAllEpics, useMoveToTodo, useStories } from "@/hooks/useStories";
import { useFilterBar } from "@/hooks/useFilterBar";
import Button from "@/components/ui/Button";
import Pagination from "@/components/projects/Pagination";
import PriorityBadge from "@/components/stories/PriorityBadge";
import AssigneeAvatar from "@/components/stories/AssigneeAvatar";
import DueDate from "@/components/stories/DueDate";
import SearchBox from "@/components/stories/SearchBox";
import FilterBar from "@/components/stories/FilterBar";
import CreateDialog from "@/components/stories/CreateDialog";
import type { Story } from "@/lib/api";

// ─── Progress bar (same implementation as epics page) ────────────────────────

function ProgressBar({ total, done }: { total: number; done: number }) {
  const pct = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="mt-1.5">
      <div className="h-1.5 w-full rounded-full bg-gray-100">
        <div
          className="h-1.5 rounded-full bg-gray-800 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-0.5 text-xs text-gray-400">
        {done}/{total} done
      </p>
    </div>
  );
}

// ─── Story row ────────────────────────────────────────────────────────────────

interface StoryRowProps {
  story: Story;
  epicName: string | null;
  canMove: boolean;
  onMoveToTodo: (storyId: string) => void;
  isMoving: boolean;
}

function StoryRow({
  story,
  epicName,
  canMove,
  onMoveToTodo,
  isMoving,
}: StoryRowProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm transition-colors hover:border-gray-300">
      <PriorityBadge priority={story.priority} />

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-gray-900">{story.title}</p>
        <p className="text-xs text-gray-400">{story.storyKey}</p>
      </div>

      {/* Right-side metadata — hidden on small screens */}
      <div className="hidden shrink-0 items-center gap-4 sm:flex">
        {story.storyPoints !== null && (
          <span className="text-xs font-medium text-gray-500">
            {story.storyPoints}pt
          </span>
        )}

        <AssigneeAvatar assignee={story.assignee} showName />

        {epicName && (
          <span className="hidden max-w-[120px] truncate rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 lg:inline-flex">
            {epicName}
          </span>
        )}

        <DueDate dueDate={story.dueDate} isDone={false} />
      </div>

      <Button
        variant="secondary"
        className="shrink-0 px-2.5 py-1.5 text-xs"
        onClick={() => onMoveToTodo(story.id)}
        disabled={!canMove || isMoving}
        title={
          !canMove
            ? "Only the assignee or project Owner can move this story"
            : "Move to Board (Todo)"
        }
      >
        Move to Todo
      </Button>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function BacklogPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [page, setPage] = useState(1);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createDialogTab, setCreateDialogTab] = useState<"story" | "epic">("story");

  const currentUser = useAuthStore((s) => s.user);
  const { data: project } = useProject(projectId);
  const { data: epicsData, isLoading: epicsLoading } = useAllEpics(projectId);
  const { filters, setFilter, setSearch } = useFilterBar();
  const moveToTodo = useMoveToTodo(projectId);

  const isOwner = project?.role === "owner";
  const epics = epicsData?.items ?? [];

  // epicId[] from URL: [] = All, ["none"] = No Epic, ["<uuid>"] = specific epic
  const selectedEpicId = filters.epicId[0] ?? null;

  // Always force status=backlog; layer other URL filters on top
  const storyFilters = {
    status: ["backlog" as const],
    priority: filters.priority,
    assigneeId: filters.assigneeId,
    epicId: filters.epicId,
    search: filters.search || undefined,
    sortBy: "priority",
    sortOrder: "desc" as const,
    page,
    pageSize: 25,
  };

  const {
    data: storiesData,
    isLoading: storiesLoading,
    isError: storiesError,
    refetch,
  } = useStories(projectId, storyFilters);

  const stories = storiesData?.items ?? [];
  const pagination = storiesData?.pagination;

  // Build epicId → name lookup from epics already fetched for the panel
  const epicMap = new Map(epics.map((e) => [e.id, e.name]));

  function canMoveToTodo(story: Story): boolean {
    if (!story.assignee) return true;
    return story.assignee.id === currentUser?.id || isOwner;
  }

  function selectEpic(epicId: string | null) {
    setFilter("epicId", epicId ? [epicId] : []);
    setPage(1);
  }

  function openCreateDialog(tab: "story" | "epic") {
    setCreateDialogTab(tab);
    setShowCreateDialog(true);
  }

  const hasActiveFilters =
    filters.priority.length > 0 ||
    filters.assigneeId.length > 0 ||
    !!filters.search;

  return (
    <div className="grid grid-cols-[288px_1fr] gap-6">
      {/* ── Epics Panel ──────────────────────────────────────────────────── */}
      <aside className="flex flex-col gap-1.5">
        <div className="mb-1 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">Epics</h2>
          <button
            type="button"
            onClick={() => openCreateDialog("epic")}
            className="rounded p-1 text-xs text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900"
            title="Create new epic"
          >
            + New
          </button>
        </div>

        {/* All Epics */}
        <button
          type="button"
          onClick={() => selectEpic(null)}
          className={`w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${
            selectedEpicId === null
              ? "bg-gray-900 text-white"
              : "text-gray-700 hover:bg-gray-100"
          }`}
        >
          All Epics
        </button>

        {/* No Epic */}
        <button
          type="button"
          onClick={() => selectEpic("none")}
          className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
            selectedEpicId === "none"
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          No Epic
        </button>

        {/* Loading skeleton */}
        {epicsLoading && (
          <div className="space-y-2 pt-1">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!epicsLoading && epics.length === 0 && (
          <p className="py-3 text-center text-xs text-gray-400">No epics yet</p>
        )}

        {/* Epic rows */}
        {!epicsLoading &&
          epics.map((epic) => (
            <button
              key={epic.id}
              type="button"
              onClick={() => selectEpic(epic.id)}
              className={`w-full rounded-lg px-3 py-2.5 text-left transition-colors ${
                selectedEpicId === epic.id
                  ? "bg-gray-100 ring-1 ring-gray-300"
                  : "hover:bg-gray-50"
              }`}
            >
              <p className="truncate text-sm font-medium text-gray-900">
                {epic.name}
              </p>
              <ProgressBar
                total={epic.progress.total}
                done={epic.progress.done}
              />
            </button>
          ))}
      </aside>

      {/* ── Stories List ──────────────────────────────────────────────────── */}
      <section className="flex min-w-0 flex-col gap-4">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Backlog</h1>
            <p className="mt-0.5 text-sm text-gray-500">
              Stories not yet committed to the board
            </p>
          </div>
          <Button onClick={() => openCreateDialog("story")}>+ Create Story</Button>
        </div>

        {/* Filter row */}
        <div className="flex flex-wrap items-center gap-2">
          <SearchBox
            value={filters.search}
            onChange={(v) => {
              setSearch(v);
              setPage(1);
            }}
          />
          <FilterBar
            projectId={projectId}
            filters={filters}
            onFilterChange={(key, vals) => {
              setFilter(key, vals);
              setPage(1);
            }}
            omit={["status", "epicId"]}
          />
        </div>

        {/* Loading spinner */}
        {storiesLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
          </div>
        )}

        {/* Error state */}
        {storiesError && (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="mb-4 text-sm text-gray-600">Failed to load stories.</p>
            <Button variant="secondary" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!storiesLoading && !storiesError && stories.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 py-16">
            <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-gray-200 text-2xl">
              📋
            </div>
            <h2 className="mb-1 text-base font-semibold text-gray-900">
              {hasActiveFilters ? "No stories match your filters" : "Backlog is empty"}
            </h2>
            <p className="mb-4 max-w-xs text-center text-xs text-gray-500">
              {hasActiveFilters
                ? "Try adjusting your filters or search query"
                : "Create your first story to get started"}
            </p>
            {!hasActiveFilters && (
              <Button onClick={() => openCreateDialog("story")}>+ Create Story</Button>
            )}
          </div>
        )}

        {/* Story rows */}
        {!storiesLoading && !storiesError && stories.length > 0 && (
          <div className="space-y-2">
            {stories.map((story) => (
              <StoryRow
                key={story.id}
                story={story}
                epicName={
                  story.epicId ? (epicMap.get(story.epicId) ?? null) : null
                }
                canMove={canMoveToTodo(story)}
                onMoveToTodo={(id) => moveToTodo.mutate(id)}
                isMoving={moveToTodo.isPending}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.totalPages > 1 && (
          <Pagination
            page={page}
            totalPages={pagination.totalPages}
            onPageChange={(p) => {
              setPage(p);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        )}
      </section>

      {/* Create dialog — rendered at page root to avoid z-index stacking issues */}
      {showCreateDialog && (
        <CreateDialog
          projectId={projectId}
          defaultStatus="backlog"
          defaultTab={createDialogTab}
          onClose={() => setShowCreateDialog(false)}
        />
      )}
    </div>
  );
}
