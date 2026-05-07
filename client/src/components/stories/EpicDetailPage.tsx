"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useEpic, useUpdateEpic, useDeleteEpic } from "@/hooks/useEpics";
import { useStories } from "@/hooks/useStories";
import { useProject } from "@/hooks/useProject";
import { useMembership } from "@/hooks/useMembership";
import ActivityTimeline from "@/components/stories/ActivityTimeline";
import CommentsSection from "@/components/stories/CommentsSection";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import type { Story } from "@/lib/api";

// ─── Progress bar (same style as epics/page.tsx) ─────────────────────────────

function ProgressBar({ total, done }: { total: number; done: number }) {
  const pct = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="mt-3">
      <div className="mb-1 flex justify-between text-xs text-gray-500">
        <span>
          {done}/{total} stories done
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-gray-100">
        <div
          className="h-1.5 rounded-full bg-gray-800 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Status badge colours ─────────────────────────────────────────────────────

const STATUS_CLASSES: Record<string, string> = {
  todo: "bg-gray-100 text-gray-600",
  in_progress: "bg-blue-100 text-blue-700",
  in_review: "bg-yellow-100 text-yellow-700",
  done: "bg-green-100 text-green-700",
};

// ─── Main component ───────────────────────────────────────────────────────────

export default function EpicDetailPage() {
  const { projectId, epicId } =
    useParams<{ projectId: string; epicId: string }>();
  const router = useRouter();

  const [showAll, setShowAll] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const {
    data: epic,
    isLoading: epicLoading,
    error: epicError,
  } = useEpic(projectId, epicId);
  const { data: project } = useProject(projectId);
  const { data: storiesData } = useStories(projectId, {
    epicId: [epicId],
    pageSize: 100,
  });
  const { role, userId } = useMembership(projectId);
  const updateEpic = useUpdateEpic(projectId, epicId);
  const deleteEpic = useDeleteEpic(projectId);

  const stories: Story[] = storiesData?.items ?? [];
  const displayedStories = showAll ? stories : stories.slice(0, 10);
  const canDelete =
    role === "owner" || (!!epic && epic.reporter.id === userId);

  function handleDelete() {
    deleteEpic.mutate(epicId, {
      onSuccess: () => router.push(`/projects/${projectId}/epics`),
    });
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (epicLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-gray-800" />
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (epicError || !epic) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4">
        <p className="text-gray-500">
          Epic not found or you don&apos;t have access.
        </p>
        <button
          className="text-sm text-blue-600 hover:underline"
          onClick={() => router.back()}
        >
          Go back
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
      {/* Breadcrumb */}
      <nav className="mb-6 flex items-center gap-2 text-sm text-gray-500">
        <button
          onClick={() => router.push(`/projects/${projectId}/epics`)}
          className="hover:text-gray-900"
        >
          ← Back
        </button>
        <span>·</span>
        <Link
          href={`/projects/${projectId}`}
          className="hover:text-gray-900"
        >
          {project?.name ?? "Project"}
        </Link>
        <span>·</span>
        <span className="text-gray-900">{epic.name}</span>
      </nav>

      {/* Epic header card */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold text-gray-900">{epic.name}</h1>
            {epic.description && (
              <p className="mt-2 text-sm text-gray-500">{epic.description}</p>
            )}
            <p className="mt-2 text-xs text-gray-400">
              Reporter: {epic.reporter.name}
            </p>
            <ProgressBar
              total={epic.progress.total}
              done={epic.progress.done}
            />
          </div>

          {canDelete && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="shrink-0 rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-600 transition-colors hover:bg-red-50"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <div className="mt-6 space-y-6">
        {/* Stories in this epic */}
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-5 py-4">
            <h2 className="text-sm font-semibold text-gray-900">
              Stories in this Epic ({stories.length})
            </h2>
          </div>

          {stories.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-gray-400">
              No stories linked to this epic yet.
            </p>
          ) : (
            <div className="divide-y divide-gray-50">
              {displayedStories.map((story) => (
                <Link
                  key={story.id}
                  href={`/projects/${projectId}/stories/${story.id}`}
                  className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-gray-50"
                >
                  <span className="shrink-0 rounded bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-600">
                    {story.storyKey}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-sm text-gray-900">
                    {story.title}
                  </span>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs capitalize ${STATUS_CLASSES[story.status] ?? "bg-gray-100 text-gray-600"}`}
                  >
                    {story.status.replace(/_/g, " ")}
                  </span>
                </Link>
              ))}

              {stories.length > 10 && (
                <button
                  onClick={() => setShowAll((v) => !v)}
                  className="w-full py-3 text-center text-xs text-blue-600 hover:underline"
                >
                  {showAll
                    ? "Show less"
                    : `Show all ${stories.length} stories`}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Activity */}
        <ActivityTimeline
          entityType="epic"
          entityId={epicId}
          projectId={projectId}
        />

        {/* Comments */}
        <CommentsSection
          projectId={projectId}
          epicId={epicId}
          userRole={role}
        />
      </div>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={showDeleteConfirm}
        title="Delete Epic"
        message={`Are you sure you want to delete "${epic.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteEpic.isPending}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
