"use client";

import { useParams, useRouter } from "next/navigation";
import { useStory, useUpdateStory, useDeleteStory } from "@/hooks/useStories";
import { useProject } from "@/hooks/useProject";
import StoryHeader from "@/components/stories/StoryHeader";
import StoryMetaSidebar from "@/components/stories/StoryMetaSidebar";
import TasksSection from "@/components/stories/TasksSection";
import CommentsSection from "@/components/stories/CommentsSection";
import ActivityTimeline from "@/components/stories/ActivityTimeline";
import { useState } from "react";
import ConfirmDialog from "@/components/ui/ConfirmDialog";

export default function StoryDetailPage() {
  const params = useParams<{ projectId: string; storyId: string }>();
  const router = useRouter();
  const { projectId, storyId } = params;

  const { data: story, isLoading, error } = useStory(projectId, storyId);
  const { data: project } = useProject(projectId);
  const updateStory = useUpdateStory(projectId, storyId);
  const deleteStoryMutation = useDeleteStory(projectId);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-gray-800" />
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4">
        <p className="text-gray-500">Story not found or you don&apos;t have access.</p>
        <button
          className="text-sm text-blue-600 hover:underline"
          onClick={() => router.back()}
        >
          Go back
        </button>
      </div>
    );
  }

  const handleDelete = () => {
    deleteStoryMutation.mutate(storyId, {
      onSuccess: () => {
        router.push(`/projects/${projectId}`);
      },
    });
  };

  const userRole = project?.role ?? "member";

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <StoryHeader
        story={story}
        projectId={projectId}
        onUpdate={(body) => updateStory.mutate(body)}
        onDeleteClick={() => setShowDeleteConfirm(true)}
        userRole={userRole}
      />

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="space-y-6 lg:col-span-2">
          <TasksSection projectId={projectId} storyId={storyId} userRole={userRole} storyAssignee={story.assignee} />
          <ActivityTimeline entityType="story" entityId={storyId} projectId={projectId} />
          <CommentsSection projectId={projectId} storyId={storyId} userRole={userRole} />
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <StoryMetaSidebar
            story={story}
            projectId={projectId}
            onUpdate={(body) => updateStory.mutate(body)}
            userRole={userRole}
          />
        </div>
      </div>

      <ConfirmDialog
        open={showDeleteConfirm}
        title="Delete Story"
        message={`Are you sure you want to delete "${story.title}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteStoryMutation.isPending}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
