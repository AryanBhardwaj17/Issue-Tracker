"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { z } from "zod";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import ErrorMessage from "@/components/ui/ErrorMessage";
import { useProject, useProjectMembers, useAddMember, useUpdateProject } from "@/hooks/useProject";
import TransferModal from "@/components/dashboard/TransferModal";
import DeleteProjectModal from "@/components/dashboard/DeleteProjectModal";
import { useAuthStore } from "@/stores/authStore";

const emailSchema = z.string().email("Please enter a valid email");

export default function ProjectSettingsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project, isLoading } = useProject(projectId);
  const { data: membersData } = useProjectMembers(projectId);
  const addMemberMutation = useAddMember(projectId);
  const updateMutation = useUpdateProject(projectId);

  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [name, setName] = useState(project?.name ?? "");
  const [description, setDescription] = useState(project?.description ?? "");
  const [showTransfer, setShowTransfer] = useState(false);
  const [showDelete, setShowDelete] = useState(false);

  const user = useAuthStore((s) => s.user);
  const isOwner = project?.role === "owner";
  const members = membersData?.data ?? [];

  function handleUpdateProject(e: React.FormEvent) {
    e.preventDefault();
    updateMutation.mutate({ name: name.trim(), description: description.trim() || undefined });
  }

  function handleAddMember(e: React.FormEvent) {
    e.preventDefault();
    const result = emailSchema.safeParse(email);
    if (!result.success) {
      setEmailError(result.error.issues[0].message);
      return;
    }
    setEmailError(null);
    addMemberMutation.mutate(email, { onSuccess: () => setEmail("") });
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-gray-900" />
      </div>
    );
  }

  if (!project) {
    return <p className="text-sm text-gray-500">Project not found.</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Project Settings</h1>

      {!isOwner && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          You are a member. Only the owner can edit settings.
        </div>
      )}

      {/* ─── Members Section ─────────────────────────────────────────── */}
      <Card>
        <h2 className="text-lg font-medium text-gray-900">Members</h2>
        <div className="mt-4 max-h-64 space-y-2 overflow-y-auto">
          {members.map((m) => (
            <div
              key={m.id}
              className="flex items-center justify-between rounded-lg border border-gray-100 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">{m.name}</p>
                <p className="text-xs text-gray-500">
                  Joined {new Date(m.joinedAt).toLocaleDateString()}
                </p>
              </div>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  m.role === "owner"
                    ? "bg-gray-900 text-white"
                    : "bg-gray-200 text-gray-700"
                }`}
              >
                {m.role}
              </span>
            </div>
          ))}
        </div>

        {isOwner && (
          <form onSubmit={handleAddMember} className="mt-4 flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="Add member by email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={emailError ?? undefined}
              />
            </div>
            <Button type="submit" isLoading={addMemberMutation.isPending}>
              Add
            </Button>
          </form>
        )}
        {addMemberMutation.isError && (
          <ErrorMessage
            message={addMemberMutation.error?.message ?? "Failed to add member"}
          />
        )}
      </Card>

      {/* ─── Details Section ────────────────────────────────────────── */}
      <Card>
        <h2 className="text-lg font-medium text-gray-900">Details</h2>
        {isOwner ? (
          <form onSubmit={handleUpdateProject} className="mt-4 space-y-4">
            <Input
              label="Project Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <div className="w-full">
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
                placeholder="Project description (optional)"
              />
            </div>
            <Button type="submit" isLoading={updateMutation.isPending}>
              Save Changes
            </Button>
          </form>
        ) : (
          <div className="mt-4 space-y-3">
            <div>
              <p className="text-sm font-medium text-gray-500">Name</p>
              <p className="text-sm text-gray-900">{project.name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Description</p>
              <p className="text-sm text-gray-900">{project.description || "—"}</p>
            </div>
          </div>
        )}
      </Card>

      {/* ─── Danger Zone ──────────────────────────────────────────── */}
      {isOwner && (
        <Card className="border-red-200">
          <h2 className="text-lg font-medium text-red-700">Danger Zone</h2>
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Transfer Ownership</p>
                <p className="text-xs text-gray-500">Transfer this project to another member.</p>
              </div>
              <Button variant="secondary" onClick={() => setShowTransfer(true)}>
                Transfer
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Delete Project</p>
                <p className="text-xs text-gray-500">Permanently delete this project and all data.</p>
              </div>
              <Button variant="danger" onClick={() => setShowDelete(true)}>
                Delete
              </Button>
            </div>
          </div>
        </Card>
      )}

      {showTransfer && (
        <TransferModal
          projectId={projectId}
          members={members}
          currentUserId={user?.id ?? ""}
          onClose={() => setShowTransfer(false)}
        />
      )}
      {showDelete && (
        <DeleteProjectModal
          projectId={projectId}
          projectName={project.name}
          onClose={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}
