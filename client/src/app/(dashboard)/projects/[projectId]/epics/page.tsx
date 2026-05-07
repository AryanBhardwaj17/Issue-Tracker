"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useProject } from "@/hooks/useProjects";
import { useEpics, useCreateEpic, useUpdateEpic, useDeleteEpic } from "@/hooks/useEpics";
import { useAuthStore } from "@/stores/authStore";
import Pagination from "@/components/projects/Pagination";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import type { Epic } from "@/lib/api";

// ─── Progress bar ─────────────────────────────────────────────────────────────

function ProgressBar({ total, done }: { total: number; done: number }) {
  const pct = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="mt-2">
      <div className="mb-1 flex justify-between text-xs text-gray-500">
        <span>{done}/{total} stories done</span>
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

// ─── Create / Edit form ───────────────────────────────────────────────────────

interface EpicFormProps {
  initialName?: string;
  initialDescription?: string;
  onSubmit: (name: string, description: string | null) => void;
  onCancel: () => void;
  isLoading?: boolean;
  submitLabel: string;
}

function EpicForm({
  initialName = "",
  initialDescription = "",
  onSubmit,
  onCancel,
  isLoading,
  submitLabel,
}: EpicFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    onSubmit(name.trim(), description.trim() || null);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <Input
        label="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Epic name"
        required
      />
      <div className="w-full">
        <label className="mb-1.5 block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description"
          rows={3}
          className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" isLoading={isLoading}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}

// ─── Epic card ────────────────────────────────────────────────────────────────

interface EpicCardProps {
  epic: Epic;
  canEdit: boolean;
  projectId: string;
}

function EpicCard({ epic, canEdit, projectId }: EpicCardProps) {
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const updateMutation = useUpdateEpic(projectId, epic.id);
  const deleteMutation = useDeleteEpic(projectId);

  function handleUpdate(name: string, description: string | null) {
    updateMutation.mutate({ name, description }, { onSuccess: () => setEditing(false) });
  }

  function handleDelete() {
    deleteMutation.mutate(epic.id, { onSuccess: () => setConfirmDelete(false) });
  }

  if (editing) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <EpicForm
          initialName={epic.name}
          initialDescription={epic.description ?? ""}
          onSubmit={handleUpdate}
          onCancel={() => setEditing(false)}
          isLoading={updateMutation.isPending}
          submitLabel="Save"
        />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <Link
            href={`/projects/${projectId}/epics/${epic.id}`}
            className="truncate text-sm font-semibold text-gray-900 hover:text-blue-600 hover:underline"
          >
            {epic.name}
          </Link>
          {epic.description && (
            <p className="mt-1 text-xs text-gray-500 line-clamp-2">{epic.description}</p>
          )}
          <p className="mt-1.5 text-xs text-gray-400">
            Reporter: {epic.reporter.name}
          </p>
          <ProgressBar total={epic.progress.total} done={epic.progress.done} />
        </div>

        {canEdit && (
          <div className="flex shrink-0 gap-1">
            <Button
              variant="secondary"
              className="px-2 py-1 text-xs"
              onClick={() => setEditing(true)}
            >
              Edit
            </Button>
            {confirmDelete ? (
              <div className="flex gap-1">
                <Button
                  variant="danger"
                  className="px-2 py-1 text-xs"
                  onClick={handleDelete}
                  isLoading={deleteMutation.isPending}
                >
                  Confirm
                </Button>
                <Button
                  variant="secondary"
                  className="px-2 py-1 text-xs"
                  onClick={() => setConfirmDelete(false)}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <Button
                variant="danger"
                className="px-2 py-1 text-xs"
                onClick={() => setConfirmDelete(true)}
              >
                Delete
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function EpicsPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const [page, setPage] = useState(1);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data: project } = useProject(projectId);
  const { data, isLoading, isError, refetch } = useEpics(projectId, page);
  const currentUser = useAuthStore((s) => s.user);
  const createMutation = useCreateEpic(projectId);

  const items = data?.items ?? [];
  const pagination = data?.pagination;

  // An epic's edit/delete controls are shown when:
  // - the user is the project owner (can always edit any epic), OR
  // - the user is the epic's reporter (they can edit their own)
  // We surface the buttons; the server enforces the same rule.
  const isOwner = project?.role === "owner";

  function handleCreate(name: string, description: string | null) {
    createMutation.mutate({ name, description }, { onSuccess: () => setShowCreateForm(false) });
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Epics</h1>
          <p className="mt-1 text-sm text-gray-500">
            High-level themes grouping related stories
          </p>
        </div>
        {!showCreateForm && (
          <Button onClick={() => setShowCreateForm(true)}>+ New Epic</Button>
        )}
      </div>

      {/* Inline create form */}
      {showCreateForm && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">New Epic</h2>
          <EpicForm
            onSubmit={handleCreate}
            onCancel={() => setShowCreateForm(false)}
            isLoading={createMutation.isPending}
            submitLabel="Create Epic"
          />
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-20">
          <p className="mb-4 text-sm text-gray-600">Failed to load epics.</p>
          <Button variant="secondary" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && items.length === 0 && page === 1 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 py-16">
          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-gray-200 text-2xl">
            🗂
          </div>
          <h2 className="mb-1 text-base font-semibold text-gray-900">No epics yet</h2>
          <p className="mb-4 max-w-xs text-center text-xs text-gray-500">
            Create an epic to group related stories under a common theme
          </p>
          <Button onClick={() => setShowCreateForm(true)}>+ New Epic</Button>
        </div>
      )}

      {/* Epic list */}
      {!isLoading && !isError && items.length > 0 && (
        <>
          <div className="space-y-3">
            {items.map((epic) => (
              <EpicCard
                key={epic.id}
                epic={epic}
                projectId={projectId}
                canEdit={isOwner || epic.reporter.id === currentUser?.id}
              />
            ))}
          </div>

          {pagination && (
            <Pagination
              page={page}
              totalPages={pagination.totalPages}
              onPageChange={setPage}
            />
          )}
        </>
      )}
    </div>
  );
}

