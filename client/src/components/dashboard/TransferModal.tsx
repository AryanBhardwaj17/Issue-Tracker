"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import { useTransferOwnership } from "@/hooks/useProject";
import type { MemberOut } from "@/lib/api";

interface TransferModalProps {
  projectId: string;
  members: MemberOut[];
  currentUserId: string;
  onClose: () => void;
}

export default function TransferModal({
  projectId,
  members,
  currentUserId,
  onClose,
}: TransferModalProps) {
  const [selectedId, setSelectedId] = useState("");
  const mutation = useTransferOwnership(projectId);

  const candidates = members.filter((m) => m.userId !== currentUserId);

  function handleConfirm() {
    if (!selectedId) return;
    mutation.mutate(selectedId, { onSuccess: onClose });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg">
        <h3 className="text-lg font-semibold text-gray-900">Transfer Ownership</h3>
        <p className="mt-2 text-sm text-gray-600">
          Select a member to transfer ownership to. This action cannot be undone easily.
        </p>

        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="mt-4 w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
        >
          <option value="">Select a member…</option>
          {candidates.map((m) => (
            <option key={m.userId} value={m.userId}>
              {m.name}
            </option>
          ))}
        </select>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleConfirm}
            disabled={!selectedId}
            isLoading={mutation.isPending}
          >
            Transfer
          </Button>
        </div>
      </div>
    </div>
  );
}
