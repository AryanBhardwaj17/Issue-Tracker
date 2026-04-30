"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useDeleteProject } from "@/hooks/useProject";

interface DeleteProjectModalProps {
  projectId: string;
  projectName: string;
  onClose: () => void;
}

export default function DeleteProjectModal({
  projectId,
  projectName,
  onClose,
}: DeleteProjectModalProps) {
  const [confirmation, setConfirmation] = useState("");
  const router = useRouter();
  const mutation = useDeleteProject(projectId);

  const isMatch = confirmation === projectName;

  function handleDelete() {
    if (!isMatch) return;
    mutation.mutate(undefined, {
      onSuccess: () => router.push("/projects"),
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg">
        <h3 className="text-lg font-semibold text-red-700">Delete Project</h3>
        <p className="mt-2 text-sm text-gray-600">
          This action is irreversible. Type <strong>{projectName}</strong> to confirm.
        </p>

        <div className="mt-4">
          <Input
            placeholder="Type project name to confirm"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
          />
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            disabled={!isMatch}
            isLoading={mutation.isPending}
          >
            Delete Project
          </Button>
        </div>
      </div>
    </div>
  );
}
