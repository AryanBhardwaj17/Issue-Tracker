"use client";

import { format } from "date-fns";
import type { Story, StoryPatchPayload } from "@/lib/api";
import { listMembers, type MemberOut } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { useEpics } from "@/hooks/useEpics";
import { canChangeStatus, canModifyStory } from "@/lib/auth-predicates";
import { useAuthStore } from "@/stores/authStore";

interface StoryMetaSidebarProps {
  story: Story;
  projectId: string;
  onUpdate: (body: StoryPatchPayload) => void;
  userRole: "owner" | "member";
}

const ALL_STATUSES = ["backlog", "todo", "in_progress", "in_review", "testing", "ready_for_prod", "done"];
const PRIORITY_OPTIONS = ["low", "medium", "high", "critical"];
const FIBONACCI_POINTS = [1, 2, 3, 5, 8, 13, 21];

/**
 * Status state machine:
 * - If current is "backlog" → can only pick backlog or todo
 * - If current is non-backlog → can pick any except backlog (cannot go back to backlog)
 */
function getAvailableStatuses(current: string): string[] {
  if (current === "backlog") return ["backlog", "todo"];
  return ALL_STATUSES.filter((s) => s !== "backlog");
}

export default function StoryMetaSidebar({
  story,
  projectId,
  onUpdate,
  userRole,
}: StoryMetaSidebarProps) {
  const currentUser = useAuthStore((s) => s.user);

  const { data: members } = useQuery({
    queryKey: ["members", projectId],
    queryFn: () => listMembers(projectId),
    staleTime: 60_000,
  });

  const { data: epicsData } = useEpics(projectId, 1);
  const epics = epicsData?.items ?? [];

  const canEdit = currentUser
    ? canModifyStory(story, currentUser.id, userRole)
    : false;
  const canStatus = currentUser
    ? canChangeStatus(story, currentUser.id, userRole)
    : false;

  const availableStatuses = getAvailableStatuses(story.status);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-4 text-sm font-semibold text-gray-900">Details</h3>

      <div className="space-y-4">
        {/* Status */}
        <Field label="Status">
          <select
            value={story.status}
            onChange={(e) => onUpdate({ status: e.target.value })}
            disabled={!canStatus}
            title={!canStatus ? "Only the assignee or owner can change status" : undefined}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            {availableStatuses.map((s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </Field>

        {/* Priority */}
        <Field label="Priority">
          <select
            value={story.priority}
            onChange={(e) => onUpdate({ priority: e.target.value })}
            disabled={!canEdit}
            title={!canEdit ? "Only the reporter or owner can edit this field" : undefined}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </Field>

        {/* Story Points */}
        <Field label="Story Points">
          <select
            value={story.storyPoints ?? ""}
            onChange={(e) =>
              onUpdate({ storyPoints: e.target.value ? Number(e.target.value) : null })
            }
            disabled={!canEdit}
            title={!canEdit ? "Only the reporter or owner can edit this field" : undefined}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="">None</option>
            {FIBONACCI_POINTS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </Field>

        {/* Epic */}
        <Field label="Epic">
          <select
            value={story.epicId ?? ""}
            onChange={(e) => onUpdate({ epicId: e.target.value || null })}
            disabled={!canEdit}
            title={!canEdit ? "Only the reporter or owner can edit this field" : undefined}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="">None</option>
            {epics.map((epic) => (
              <option key={epic.id} value={epic.id}>
                {epic.name}
              </option>
            ))}
          </select>
        </Field>

        {/* Assignee */}
        <Field label="Assignee">
          <select
            value={story.assignee?.id ?? ""}
            onChange={(e) =>
              onUpdate({ assigneeId: e.target.value || null })
            }
            disabled={!canEdit}
            title={!canEdit ? "Only the reporter or owner can edit this field" : undefined}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="">Unassigned</option>
            {members?.map((m: MemberOut) => (
              <option key={m.userId} value={m.userId}>
                {m.name}
              </option>
            ))}
          </select>
        </Field>

        {/* Due Date */}
        <Field label="Due Date">
          <input
            type="date"
            value={story.dueDate ?? ""}
            onChange={(e) =>
              onUpdate({ dueDate: e.target.value || null })
            }
            disabled={!canEdit}
            title={!canEdit ? "Only the reporter or owner can edit this field" : undefined}
            className="w-full rounded border border-gray-200 px-2 py-1 text-sm disabled:cursor-not-allowed disabled:opacity-50"
          />
        </Field>

        {/* Reporter */}
        <Field label="Reporter">
          <span className="text-sm text-gray-700">{story.reporter.name}</span>
        </Field>

        {/* Timestamps */}
        <Field label="Created">
          <span className="text-sm text-gray-500">
            {format(new Date(story.createdAt), "MMM d, yyyy")}
          </span>
        </Field>

        <Field label="Updated">
          <span className="text-sm text-gray-500">
            {format(new Date(story.updatedAt), "MMM d, yyyy")}
          </span>
        </Field>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-xs font-medium text-gray-500">{label}</span>
      <div className="flex-1 text-right">{children}</div>
    </div>
  );
}
