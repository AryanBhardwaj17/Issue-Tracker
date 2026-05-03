"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStory, useUpdateStory } from "@/hooks/useStories";
import { useProject } from "@/hooks/useProject";
import StoryMetaSidebar from "./StoryMetaSidebar";
import TasksSection from "./TasksSection";
import CommentsSection from "./CommentsSection";

interface StoryDrawerProps {
  projectId: string;
  storyId: string;
  open: boolean;
  onClose: () => void;
}

export default function StoryDrawer({ projectId, storyId, open, onClose }: StoryDrawerProps) {
  const router = useRouter();
  const { data: story, isLoading, error } = useStory(projectId, storyId);
  const { data: project } = useProject(projectId);
  const updateStory = useUpdateStory(projectId, storyId);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  const userRole = project?.role ?? "member";

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      {/* Drawer panel */}
      <div className="relative z-10 flex h-full w-full max-w-2xl flex-col overflow-y-auto bg-white shadow-xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
          <div className="flex items-center gap-3">
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Close">
              ✕
            </button>
            {story && (
              <span className="font-mono text-xs text-gray-400">{story.storyKey}</span>
            )}
          </div>
          <button
            onClick={() => router.push(`/projects/${projectId}/stories/${storyId}`)}
            className="text-xs text-blue-600 hover:underline"
          >
            Open full page →
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && (
            <div className="flex h-32 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-gray-700" />
            </div>
          )}

          {error && (
            <div className="py-8 text-center text-sm text-gray-500">
              Story not found or you don&apos;t have access.
            </div>
          )}

          {story && (
            <div className="space-y-6">
              {/* Title */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{story.title}</h2>
                {story.description && (
                  <p className="mt-2 text-sm text-gray-600 whitespace-pre-wrap">{story.description}</p>
                )}
              </div>

              {/* Meta */}
              <StoryMetaSidebar
                story={story}
                projectId={projectId}
                onUpdate={(body) => updateStory.mutate(body)}
                userRole={userRole}
              />

              {/* Tasks */}
              <TasksSection projectId={projectId} storyId={storyId} userRole={userRole} />

              {/* Comments */}
              <CommentsSection projectId={projectId} storyId={storyId} userRole={userRole} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
