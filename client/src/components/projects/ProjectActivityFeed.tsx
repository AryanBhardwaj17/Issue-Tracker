"use client";

import { useState } from "react";
import { format, isToday, isYesterday } from "date-fns";
import Link from "next/link";
import { useActivity } from "@/hooks/useActivity";
import type { ActivityLogOut } from "@/lib/api";

interface Props {
  projectId: string;
}

const ACTION_BORDER_CLASS: Record<string, string> = {
  created: "border-green-400",
  status_changed: "border-blue-400",
  assigned: "border-purple-400",
  field_updated: "border-gray-300",
  completed: "border-emerald-500",
  deleted: "border-red-400",
  restored: "border-blue-400",
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function formatActionText(entry: ActivityLogOut): string {
  switch (entry.action) {
    case "created":
      return "created this";
    case "deleted":
      return "deleted this";
    case "restored":
      return "restored this";
    case "status_changed":
      return `changed status from ${entry.oldValue ?? "—"} → ${entry.newValue ?? "—"}`;
    case "assigned":
      return entry.newValue ? `assigned to ${entry.newValue}` : "unassigned";
    case "completed":
      return entry.newValue === "true" ? "marked as done" : "marked as not done";
    case "field_updated": {
      const field = entry.fieldName ?? "a field";
      if (entry.oldValue && entry.newValue)
        return `updated ${field} from "${entry.oldValue}" → "${entry.newValue}"`;
      return `updated the ${field}`;
    }
    default:
      return entry.action.replace(/_/g, " ");
  }
}

function formatGroupLabel(dateStr: string): string {
  const d = new Date(dateStr);
  if (isToday(d)) return "Today";
  if (isYesterday(d)) return "Yesterday";
  return format(d, "MMMM d, yyyy");
}

function groupByDate(
  entries: ActivityLogOut[],
): { label: string; items: ActivityLogOut[] }[] {
  const map = new Map<string, ActivityLogOut[]>();
  for (const entry of entries) {
    const label = formatGroupLabel(entry.createdAt);
    if (!map.has(label)) map.set(label, []);
    map.get(label)!.push(entry);
  }
  return Array.from(map.entries()).map(([label, items]) => ({ label, items }));
}

function EntityLink({
  entry,
  projectId,
}: {
  entry: ActivityLogOut;
  projectId: string;
}) {
  if (entry.storyId) {
    return (
      <Link
        href={`/projects/${projectId}/stories/${entry.storyId}`}
        className="text-xs text-blue-600 hover:underline"
      >
        view story
      </Link>
    );
  }
  if (entry.epicId) {
    return (
      <Link
        href={`/projects/${projectId}/epics/${entry.epicId}`}
        className="text-xs text-blue-600 hover:underline"
      >
        view epic
      </Link>
    );
  }
  return null;
}

export default function ProjectActivityFeed({ projectId }: Props) {
  const [page, setPage] = useState(1);
  const [accumulated, setAccumulated] = useState<ActivityLogOut[]>([]);
  const [prevData, setPrevData] = useState<unknown>(null);

  const { data, isLoading } = useActivity(
    "project",
    projectId,
    projectId,
    page,
    30,
  );

  // Accumulate pages (render-time update pattern — same as ActivityTimeline)
  if (data !== prevData) {
    setPrevData(data);
    if (data?.items) {
      if (page === 1) setAccumulated(data.items);
      else setAccumulated((prev) => [...prev, ...data.items]);
    }
  }

  const groups = groupByDate(accumulated);
  const hasMore = (data?.pagination?.totalPages ?? 0) > page;

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Activity</h1>
        <p className="mt-1 text-sm text-gray-500">
          All recent activity across this project
        </p>
      </div>

      {/* Loading spinner */}
      {isLoading && accumulated.length === 0 && (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && accumulated.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 py-16">
          <svg
            className="mb-3 h-12 w-12 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h2 className="mb-1 text-base font-semibold text-gray-900">
            No activity yet
          </h2>
          <p className="text-sm text-gray-500">
            Activity will appear here as your team makes changes.
          </p>
        </div>
      )}

      {/* Grouped activity entries */}
      {groups.length > 0 && (
        <div className="space-y-4">
          {groups.map(({ label, items }) => (
            <div key={label}>
              {/* Date header */}
              <div className="mb-2 rounded-md bg-gray-50 px-4 py-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  {label}
                </span>
              </div>
              {/* Entries for this date */}
              <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                {items.map((entry) => {
                  const borderClass =
                    ACTION_BORDER_CLASS[entry.action] ?? "border-gray-300";
                  const initials = getInitials(entry.actorName);
                  return (
                    <div
                      key={entry.id}
                      className={`flex items-center gap-3 border-l-2 px-4 py-2.5 ${borderClass} border-b border-b-gray-50 last:border-b-0`}
                    >
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-200 text-[10px] font-semibold text-gray-600">
                        {initials}
                      </div>
                      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-1">
                        <span className="text-xs font-semibold text-gray-900">
                          {entry.actorName}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatActionText(entry)}
                        </span>
                        <EntityLink entry={entry} projectId={projectId} />
                      </div>
                      <span className="ml-auto shrink-0 text-xs text-gray-400">
                        {format(new Date(entry.createdAt), "h:mm a")}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Load more */}
          {hasMore && (
            <div className="py-2 text-center">
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={isLoading}
                className="text-xs text-blue-600 hover:underline disabled:opacity-50"
              >
                {isLoading ? "Loading..." : "Load more"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
