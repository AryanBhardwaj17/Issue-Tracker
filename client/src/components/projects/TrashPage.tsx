"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { useTrash, useRestoreStory } from "@/hooks/useTrash";
import { useMembership } from "@/hooks/useMembership";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import type { Story } from "@/lib/api";

interface Props {
  projectId: string;
}

export default function TrashPage({ projectId }: Props) {
  const { data, isLoading } = useTrash(projectId);
  const restoreMutation = useRestoreStory(projectId);
  const { role } = useMembership(projectId);
  const [restoreId, setRestoreId] = useState<string | null>(null);

  const canRestore = role === "owner";
  const items: Story[] = data?.items ?? [];
  const storyToRestore = items.find((s) => s.id === restoreId);

  function handleConfirmRestore() {
    if (!restoreId) return;
    restoreMutation.mutate(restoreId, {
      onSuccess: () => setRestoreId(null),
    });
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Trash</h1>
        <p className="mt-1 text-sm text-gray-500">
          Soft-deleted stories from this project
        </p>
      </div>

      {/* Info banner */}
      <div className="mb-6 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
        Items in trash have been soft-deleted and are not visible in the backlog
        or board. Project owners can restore them at any time.
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && items.length === 0 && (
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
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          <h2 className="mb-1 text-base font-semibold text-gray-900">
            Trash is empty
          </h2>
          <p className="text-sm text-gray-500">
            Deleted stories will appear here.
          </p>
        </div>
      )}

      {/* Story list */}
      {!isLoading && items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          {items.map((story, idx) => (
            <div
              key={story.id}
              className={`flex items-center gap-4 px-5 py-4 ${
                idx !== items.length - 1 ? "border-b border-gray-100" : ""
              }`}
            >
              {/* Story key badge */}
              <span className="shrink-0 rounded bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-600">
                {story.storyKey}
              </span>

              {/* Title + meta */}
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-gray-400 line-through">
                  {story.title}
                </p>
                <p className="mt-0.5 text-xs text-gray-400">
                  by {story.reporter.name} ·{" "}
                  {formatDistanceToNow(new Date(story.updatedAt), {
                    addSuffix: true,
                  })}
                </p>
              </div>

              {/* Restore button — owners only */}
              {canRestore && (
                <button
                  onClick={() => setRestoreId(story.id)}
                  className="shrink-0 rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-700 transition-colors hover:bg-gray-50"
                >
                  Restore
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Restore confirmation */}
      <ConfirmDialog
        open={!!restoreId}
        title="Restore Story"
        message={`Restore "${storyToRestore?.title ?? ""}" to the backlog?`}
        confirmLabel="Restore"
        variant="primary"
        isLoading={restoreMutation.isPending}
        onConfirm={handleConfirmRestore}
        onCancel={() => setRestoreId(null)}
      />
    </div>
  );
}
