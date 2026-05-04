"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import type { Story, StoryPatchPayload } from "@/lib/api";
import InlineEdit from "@/components/ui/InlineEdit";
import Button from "@/components/ui/Button";
import { canModifyStory } from "@/lib/auth-predicates";
import { useAuthStore } from "@/stores/authStore";

interface StoryHeaderProps {
  story: Story;
  projectId: string;
  onUpdate: (body: StoryPatchPayload) => void;
  onDeleteClick: () => void;
  userRole: "owner" | "member";
}

const statusColors: Record<string, string> = {
  backlog: "bg-gray-100 text-gray-700",
  todo: "bg-blue-100 text-blue-700",
  in_progress: "bg-yellow-100 text-yellow-800",
  in_review: "bg-purple-100 text-purple-700",
  testing: "bg-cyan-100 text-cyan-700",
  ready_for_prod: "bg-emerald-100 text-emerald-700",
  done: "bg-green-100 text-green-700",
};

const priorityColors: Record<string, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

export default function StoryHeader({
  story,
  projectId: _projectId,
  onUpdate,
  onDeleteClick,
  userRole,
}: StoryHeaderProps) {
  void _projectId;
  const router = useRouter();
  const currentUser = useAuthStore((s) => s.user);
  const canEdit = currentUser ? canModifyStory(story, currentUser.id, userRole) : false;

  const titleRef = useRef<HTMLDivElement>(null);
  const [editingDesc, setEditingDesc] = useState(false);
  const [descDraft, setDescDraft] = useState(story.description || "");

  const handleDescSave = () => {
    const trimmed = descDraft.trim();
    if (trimmed !== (story.description || "")) {
      onUpdate({ description: trimmed || null });
    }
    setEditingDesc(false);
  };

  const handleDescCancel = () => {
    setDescDraft(story.description || "");
    setEditingDesc(false);
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-3 flex items-center gap-2 text-sm text-gray-500">
        <button
          onClick={() => {
            if (window.history.length > 1) {
              router.back();
            } else {
              router.push("/projects");
            }
          }}
          className="hover:text-gray-700"
        >
          ← Back
        </button>
        <span>/</span>
        <span className="font-mono text-xs text-gray-400">{story.storyKey}</span>
      </div>

      {/* Title */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-1 items-center gap-2" ref={titleRef}>
          <InlineEdit
            value={story.title}
            onSave={(title) => onUpdate({ title })}
            className="text-2xl font-bold text-gray-900"
            maxLength={200}
            disabled={!canEdit}
          />
          {canEdit && (
            <button
              type="button"
              onClick={() => {
                const span = titleRef.current?.querySelector("span[role='button']") as HTMLElement | null;
                span?.click();
              }}
              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              title="Edit title"
              aria-label="Edit title"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-3 w-3"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
              Edit
            </button>
          )}
        </div>
        {canEdit && (
          <button
            onClick={onDeleteClick}
            className="shrink-0 rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
            title="Delete story"
          >
            Delete
          </button>
        )}
      </div>

      {/* Status & Priority badges */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[story.status] || "bg-gray-100 text-gray-700"}`}>
          {story.status.replaceAll("_", " ")}
        </span>
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${priorityColors[story.priority] || "bg-gray-100 text-gray-600"}`}>
          {story.priority}
        </span>
        {story.storyPoints !== null && (
          <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
            {story.storyPoints} pts
          </span>
        )}
      </div>

      {/* Description */}
      <div className="mt-4">
        <div className="mb-1 flex items-center gap-2">
          <p className="text-sm font-medium text-gray-500">Description</p>
          {canEdit && !editingDesc && (
            <button
              type="button"
              onClick={() => { setDescDraft(story.description || ""); setEditingDesc(true); }}
              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
              Edit
            </button>
          )}
        </div>
        {editingDesc ? (
          <div>
            <textarea
              value={descDraft}
              onChange={(e) => setDescDraft(e.target.value)}
              rows={5}
              maxLength={10000}
              className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
              onKeyDown={(e) => { if (e.key === "Escape") handleDescCancel(); if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); handleDescSave(); } }}
            />
            <div className="mt-2 flex items-center gap-2">
              <Button variant="primary" onClick={handleDescSave} className="!px-3 !py-1 text-xs">
                Save
              </Button>
              <Button variant="secondary" onClick={handleDescCancel} className="!px-3 !py-1 text-xs">
                Cancel
              </Button>
              <span className="ml-auto text-xs text-gray-400">{descDraft.length}/10000</span>
            </div>
          </div>
        ) : (
          <div
            onClick={() => { if (canEdit) { setDescDraft(story.description || ""); setEditingDesc(true); } }}
            className={`whitespace-pre-wrap rounded px-3 py-2 text-sm text-gray-700 ${canEdit ? "cursor-pointer hover:bg-gray-100" : ""} ${!story.description ? "italic text-gray-400 border border-dashed border-gray-300 rounded-lg" : ""}`}
            role={canEdit ? "button" : undefined}
            tabIndex={canEdit ? 0 : undefined}
            onKeyDown={(e) => { if (canEdit && e.key === "Enter") { setDescDraft(story.description || ""); setEditingDesc(true); } }}
          >
            {story.description || (canEdit ? "Click to add a description..." : "No description")}
          </div>
        )}
      </div>
    </div>
  );
}
