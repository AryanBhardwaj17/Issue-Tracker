"use client";

import { format, parseISO } from "date-fns";
import { useRouter } from "next/navigation";
import type { Story } from "@/lib/api";
import StatusBadge from "@/components/stories/StatusBadge";
import PriorityBadge from "@/components/stories/PriorityBadge";
import DueDate from "@/components/stories/DueDate";
import AssigneeAvatar from "@/components/stories/AssigneeAvatar";
import TaskRows from "@/components/issues/TaskRows";

// ─── Sort helpers ─────────────────────────────────────────────────────────────

export type SortField = "priority" | "created_at" | "updated_at" | "due_date" | "story_key";
export type SortOrder = "asc" | "desc";

interface SortState {
  sortBy: SortField;
  sortOrder: SortOrder;
}

const HEADER_COLUMNS: { key: SortField | null; label: string; className?: string }[] = [
  { key: null, label: "", className: "w-10" },
  { key: "story_key", label: "Title" },
  { key: null, label: "Status" },
  { key: "priority", label: "Priority" },
  { key: null, label: "Points", className: "w-16" },
  { key: null, label: "Assignee" },
  { key: null, label: "Epic" },
  { key: "due_date", label: "Due Date" },
  { key: "created_at", label: "Created" },
];

function SortIcon({ field, sort }: { field: SortField; sort: SortState }) {
  if (sort.sortBy !== field) {
    return (
      <svg className="ml-1 inline h-3 w-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
      </svg>
    );
  }
  return sort.sortOrder === "asc" ? (
    <svg className="ml-1 inline h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ) : (
    <svg className="ml-1 inline h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

interface IssuesTableProps {
  stories: Story[];
  projectId: string;
  userId: string;
  role: "owner" | "member";
  expandedStories: Set<string>;
  onToggleExpand: (storyId: string) => void;
  sort: SortState;
  onSortChange: (sort: SortState) => void;
  epicMap: Map<string, string>;
}

export default function IssuesTable({
  stories,
  projectId,
  userId,
  role,
  expandedStories,
  onToggleExpand,
  sort,
  onSortChange,
  epicMap,
}: IssuesTableProps) {
  function handleHeaderClick(field: SortField) {
    if (sort.sortBy === field) {
      if (sort.sortOrder === "asc") {
        onSortChange({ sortBy: field, sortOrder: "desc" });
      } else {
        // desc → reset to default
        onSortChange({ sortBy: "priority", sortOrder: "desc" });
      }
    } else {
      onSortChange({ sortBy: field, sortOrder: "asc" });
    }
  }

  if (stories.length === 0) {
    return null;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            {HEADER_COLUMNS.map((col, i) => (
              <th
                key={i}
                className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 ${col.className ?? ""} ${col.key ? "cursor-pointer select-none hover:text-gray-900" : ""}`}
                onClick={col.key ? () => handleHeaderClick(col.key!) : undefined}
              >
                {col.label}
                {col.key && <SortIcon field={col.key} sort={sort} />}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {stories.map((story) => {
            const isExpanded = expandedStories.has(story.id);
            const epicName = story.epicId ? epicMap.get(story.epicId) ?? null : null;

            return (
              <StoryRow
                key={story.id}
                story={story}
                epicName={epicName}
                isExpanded={isExpanded}
                onToggleExpand={() => onToggleExpand(story.id)}
                projectId={projectId}
                userId={userId}
                role={role}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Story Row ────────────────────────────────────────────────────────────────

interface StoryRowProps {
  story: Story;
  epicName: string | null;
  isExpanded: boolean;
  onToggleExpand: () => void;
  projectId: string;
  userId: string;
  role: "owner" | "member";
}

function StoryRow({
  story,
  epicName,
  isExpanded,
  onToggleExpand,
  projectId,
  userId,
  role,
}: StoryRowProps) {
  const router = useRouter();
  const isOverdue =
    story.dueDate &&
    story.status !== "done" &&
    new Date(story.dueDate) < new Date() &&
    !isToday(story.dueDate);

  return (
    <>
      <tr
        className={`group cursor-pointer transition-colors hover:bg-gray-50 ${isOverdue ? "bg-red-50/40" : ""}`}
        onClick={() => router.push(`/projects/${projectId}/stories/${story.id}`)}
      >
        {/* Expand chevron */}
        <td className="px-4 py-3">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
            className="flex h-5 w-5 items-center justify-center rounded border border-gray-200 bg-gray-50 text-xs text-gray-500 transition-colors hover:bg-gray-100"
          >
            {isExpanded ? "▼" : "▶"}
          </button>
        </td>

        {/* Title */}
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-400">{story.storyKey}</span>
            <span className="text-sm font-semibold text-gray-900">{story.title}</span>
          </div>
        </td>

        {/* Status */}
        <td className="px-4 py-3">
          <StatusBadge status={story.status} />
        </td>

        {/* Priority */}
        <td className="px-4 py-3">
          <PriorityBadge priority={story.priority} />
        </td>

        {/* Points */}
        <td className="px-4 py-3 text-sm text-gray-500">
          {story.storyPoints ?? "—"}
        </td>

        {/* Assignee */}
        <td className="px-4 py-3">
          <AssigneeAvatar assignee={story.assignee} showName />
        </td>

        {/* Epic */}
        <td className="px-4 py-3">
          {epicName ? (
            <span className="inline-flex max-w-[120px] truncate rounded-full bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700">
              {epicName}
            </span>
          ) : (
            <span className="text-xs text-gray-400">—</span>
          )}
        </td>

        {/* Due Date */}
        <td className="px-4 py-3">
          <DueDate dueDate={story.dueDate} isDone={story.status === "done"} />
        </td>

        {/* Created */}
        <td className="px-4 py-3 text-xs text-gray-500">
          {format(parseISO(story.createdAt), "MMM d")}
        </td>
      </tr>

      {/* Expanded tasks */}
      {isExpanded && (
        <TaskRows
          projectId={projectId}
          storyId={story.id}
          userId={userId}
          role={role}
        />
      )}
    </>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function isToday(dateStr: string): boolean {
  const d = parseISO(dateStr);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}
