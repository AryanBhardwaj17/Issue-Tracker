"use client";

import { useState } from "react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import { useCreateProject } from "@/hooks/useProjects";
import { extractErrorMessage } from "@/lib/errors";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function extractKeyPreview(name: string): string {
  const letters = name.replace(/[^A-Za-z]/g, "");
  if (!letters) return "";
  return letters.slice(0, 4).toUpperCase();
}

export default function CreateProjectModal({
  isOpen,
  onClose,
}: CreateProjectModalProps) {
  const router = useRouter();
  const createProject = useCreateProject();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);

  if (!isOpen) return null;

  function validate(): boolean {
    const trimmed = name.trim();
    if (trimmed.length === 0) {
      setNameError("Project name is required");
      return false;
    }
    if (trimmed.length > 200) {
      setNameError("Project name must be at most 200 characters");
      return false;
    }
    if (!/[A-Za-z]/.test(trimmed)) {
      setNameError("Must contain at least one letter");
      return false;
    }
    setNameError(null);
    return true;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    try {
      const project = await createProject.mutateAsync({
        name: name.trim(),
        description: description.trim() || null,
      });
      toast.success(`Project "${project.name}" created`);
      handleClose();
      router.push(`/projects/${project.id}`);
    } catch (error: unknown) {
      toast.error(extractErrorMessage(error, "Failed to create project"));
    }
  }

  function handleClose() {
    setName("");
    setDescription("");
    setNameError(null);
    onClose();
  }

  const keyPreview = extractKeyPreview(name);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      onClick={handleClose}
    >
      <div
        className="w-full max-w-md rounded-xl border border-gray-200 bg-white shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b border-gray-200 px-5 pb-3 pt-5">
          <h3 className="text-base font-semibold text-gray-900">
            Create New Project
          </h3>
          <p className="mt-0.5 text-xs text-gray-500">
            Add a new project to organize your team&apos;s work
          </p>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 px-5 py-4">
            <div>
              <Input
                label="Project Name"
                placeholder="My Awesome Project"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setNameError(null);
                }}
                error={nameError ?? undefined}
                required
                autoFocus
              />
              {keyPreview && (
                <p className="mt-1 text-xs text-gray-500">
                  Project key: <strong>{keyPreview}</strong>
                </p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
                rows={3}
                placeholder="Brief description of the project"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={createProject.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={createProject.isPending}
            >
              Create Project
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
