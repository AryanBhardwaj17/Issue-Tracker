"use client";

import { use, useCallback, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useStories, useAllEpics } from "@/hooks/useStories";
import { useFilterBar } from "@/hooks/useFilterBar";
import { useMembership } from "@/hooks/useMembership";
import SearchBox from "@/components/stories/SearchBox";
import FilterBar from "@/components/stories/FilterBar";
import Pagination from "@/components/projects/Pagination";
import ViewToggle from "@/components/issues/ViewToggle";
import IssuesTable, {
  type SortField,
  type SortOrder,
} from "@/components/issues/IssuesTable";

export default function IssuesPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();

  const { filters, setFilter, setSearch } = useFilterBar();
  const { role, userId } = useMembership(projectId);

  // ── Sort state from URL ────────────────────────────────────────────────────
  const sortBy = (searchParams.get("sortBy") ?? "priority") as SortField;
  const sortOrder = (searchParams.get("sortOrder") ?? "desc") as SortOrder;
  const page = Number(searchParams.get("page") ?? "1");

  const setSort = useCallback(
    (next: { sortBy: SortField; sortOrder: SortOrder }) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("sortBy", next.sortBy);
      params.set("sortOrder", next.sortOrder);
      params.delete("page");
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [searchParams, router],
  );

  const setPage = useCallback(
    (p: number) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", String(p));
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [searchParams, router],
  );

  // ── Expand state ───────────────────────────────────────────────────────────
  // ── Expand state ───────────────────────────────────────────────────────────
  // Compute a stable key from all filter/sort/page state.
  const filterKey = [
    filters.priority.join(","),
    filters.assigneeId.join(","),
    filters.epicId.join(","),
    filters.search,
    sortBy,
    sortOrder,
    page,
  ].join("|");

  // Store the filter key alongside the expanded set in a single state object so
  // we can reset the set during render (React "derived state" pattern) without
  // needing an effect or a ref — both of which trigger ESLint/React-compiler rules.
  const [{ trackedKey, expandedStories }, setExpandState] = useState({
    trackedKey: filterKey,
    expandedStories: new Set<string>(),
  });

  // When the filter key changes, clear expanded rows.  React will re-render
  // immediately with an empty set; the current render uses `activeExpanded`.
  const activeExpanded =
    trackedKey === filterKey ? expandedStories : new Set<string>();
  if (trackedKey !== filterKey) {
    setExpandState({ trackedKey: filterKey, expandedStories: new Set() });
  }

  function toggleExpand(storyId: string) {
    setExpandState(({ expandedStories: prev }) => {
      const next = new Set(prev);
      if (next.has(storyId)) {
        next.delete(storyId);
      } else {
        next.add(storyId);
      }
      return { trackedKey: filterKey, expandedStories: next };
    });
  }

  // ── Data fetching ──────────────────────────────────────────────────────────
  const storyFilters = {
    priority: filters.priority,
    assigneeId: filters.assigneeId,
    epicId: filters.epicId,
    search: filters.search || undefined,
    sortBy,
    sortOrder,
    page,
    pageSize: 25,
  };

  const {
    data: storiesData,
    isLoading,
    isError,
    refetch,
  } = useStories(projectId, storyFilters);

  const stories = storiesData?.items ?? [];
  const pagination = storiesData?.pagination;

  // ── Epic lookup map ────────────────────────────────────────────────────────
  const { data: epicsData } = useAllEpics(projectId);
  const epicMap = new Map((epicsData?.items ?? []).map((e) => [e.id, e.name]));

  // ── Render ─────────────────────────────────────────────────────────────────
  const hasActiveFilters =
    filters.priority.length > 0 ||
    filters.assigneeId.length > 0 ||
    filters.epicId.length > 0 ||
    !!filters.search;

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Issues</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            All stories, tasks, and subtasks
          </p>
        </div>
        <ViewToggle active="issues" />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <SearchBox
          value={filters.search}
          onChange={(v) => setSearch(v)}
        />
        <FilterBar
          projectId={projectId}
          filters={filters}
          onFilterChange={(key, vals) => setFilter(key, vals)}
        />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-20">
          <p className="mb-4 text-sm text-gray-600">Failed to load stories.</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && stories.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 py-16">
          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-gray-200 text-2xl">
            📋
          </div>
          <h2 className="mb-1 text-base font-semibold text-gray-900">
            {hasActiveFilters ? "No stories match your filters" : "No issues yet"}
          </h2>
          <p className="max-w-xs text-center text-xs text-gray-500">
            {hasActiveFilters
              ? "Try adjusting your filters or search query"
              : "Stories will appear here once created"}
          </p>
        </div>
      )}

      {/* Table */}
      {!isLoading && !isError && stories.length > 0 && (
        <IssuesTable
          stories={stories}
          projectId={projectId}
          userId={userId}
          role={role}
          expandedStories={activeExpanded}
          onToggleExpand={toggleExpand}
          sort={{ sortBy, sortOrder }}
          onSortChange={setSort}
          epicMap={epicMap}
        />
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
    </div>
  );
}
