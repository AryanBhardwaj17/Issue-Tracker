"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { useActivity, type ActivityEntityType } from "@/hooks/useActivity";
import type { ActivityLogOut } from "@/lib/api";

interface ActivityTimelineProps {
  entityType: ActivityEntityType;
  entityId: string;
  projectId: string;
}

const KEY_CHANGE_ACTIONS = new Set(["created", "deleted", "status_changed", "assigned", "completed"]);

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
      if (entry.newValue) return `assigned to ${entry.newValue}`;
      return "unassigned";
    case "completed":
      return entry.newValue === "true" ? "marked as done" : "marked as not done";
    case "field_updated": {
      const field = entry.fieldName ?? "a field";
      if (entry.oldValue && entry.newValue) {
        return `updated ${field} from "${entry.oldValue}" → "${entry.newValue}"`;
      }
      return `updated the ${field}`;
    }
    default:
      return entry.action.replace(/_/g, " ");
  }
}

export default function ActivityTimeline({ entityType, entityId, projectId }: ActivityTimelineProps) {
  const [page, setPage] = useState(1);
  const [showAll, setShowAll] = useState(false);
  const [accumulated, setAccumulated] = useState<ActivityLogOut[]>([]);

  // ── Reset page & list when the viewed entity changes ─────────────────────
  // Render-time state update pattern (no useEffect):
  // https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  const entityKey = `${entityType}:${entityId}:${projectId}`;
  const [prevEntityKey, setPrevEntityKey] = useState(entityKey);
  if (prevEntityKey !== entityKey) {
    setPrevEntityKey(entityKey);
    setPage(1);
    setAccumulated([]);
  }

  const { data, isLoading } = useActivity(entityType, entityId, projectId, page, 20);

  // ── Accumulate pages as they load ────────────────────────────────────────
  // Same render-time update pattern: when the query result reference changes,
  // either replace (page 1) or append (page > 1).
  const [prevData, setPrevData] = useState(data);
  if (data !== prevData) {
    setPrevData(data);
    if (data?.items) {
      if (page === 1) {
        setAccumulated(data.items);
      } else {
        setAccumulated((prev) => [...prev, ...data.items]);
      }
    }
  }

  const displayed = showAll
    ? accumulated
    : accumulated.filter((e) => KEY_CHANGE_ACTIONS.has(e.action));

  const hasMore = (data?.pagination?.totalPages ?? 0) > page;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-900">Activity</h3>
        <button
          onClick={() => setShowAll((v) => !v)}
          className="text-xs text-blue-600 hover:underline"
        >
          {showAll ? "Show key changes" : "Show all"}
        </button>
      </div>

      {/* Loading */}
      {isLoading && accumulated.length === 0 && (
        <div className="flex items-center justify-center py-8">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-gray-600" />
        </div>
      )}

      {/* Empty */}
      {!isLoading && displayed.length === 0 && (
        <p className="py-8 text-center text-sm text-gray-400">No activity recorded yet.</p>
      )}

      {/* Entry list */}
      {displayed.length > 0 && (
        <div className="divide-y divide-gray-50">
          {displayed.map((entry) => {
            const borderClass = ACTION_BORDER_CLASS[entry.action] ?? "border-gray-300";
            const initials = getInitials(entry.actorName);
            return (
              <div
                key={entry.id}
                className={`flex items-center gap-3 border-l-2 px-4 py-2.5 ${borderClass}`}
              >
                {/* Avatar */}
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gray-200 text-[9px] font-semibold text-gray-600">
                  {initials}
                </div>

                {/* Text */}
                <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-1">
                  <span className="text-xs font-semibold text-gray-900">{entry.actorName}</span>
                  <span className="text-xs text-gray-500">{formatActionText(entry)}</span>
                </div>

                {/* Timestamp */}
                <span className="ml-auto shrink-0 text-xs text-gray-400">
                  {formatDistanceToNow(new Date(entry.createdAt), { addSuffix: true })}
                </span>
              </div>
            );
          })}
        </div>
      )}

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
  );
}
