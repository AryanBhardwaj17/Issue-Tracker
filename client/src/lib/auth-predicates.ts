import type { Story, Task, Subtask } from "./api";

type Role = "owner" | "member";

/**
 * Whether the current user can edit a story's fields.
 * Only the reporter, assignee, or project owner may edit.
 */
export function canEditStory(
  story: Story,
  userId: string,
  role: Role,
): boolean {
  if (role === "owner") return true;
  if (story.reporter.id === userId) return true;
  if (story.assignee?.id === userId) return true;
  return false;
}

/**
 * Whether the current user can change a story's status.
 * Assigned story: only assignee or owner.
 * Unassigned story: only reporter or owner (edit guard).
 */
export function canChangeStatus(
  story: Story,
  userId: string,
  role: Role,
): boolean {
  if (role === "owner") return true;
  if (story.assignee) {
    return story.assignee.id === userId;
  }
  // Unassigned — falls back to edit guard (reporter or owner)
  return story.reporter.id === userId;
}

/**
 * Whether the current user can toggle isDone on a task or subtask.
 * Assigned: only assignee or owner.
 * Unassigned: any member.
 */
export function canToggleIsDone(
  item: Task | Subtask,
  userId: string,
  role: Role,
): boolean {
  if (role === "owner") return true;
  if (!item.assignee) return true; // unassigned — any member
  return item.assignee.id === userId;
}

/**
 * Whether the current user can delete a task or subtask.
 * Only the reporter or project owner.
 */
export function canDeleteTask(
  item: Task | Subtask,
  userId: string,
  role: Role,
): boolean {
  if (role === "owner") return true;
  return item.reporterId === userId;
}
