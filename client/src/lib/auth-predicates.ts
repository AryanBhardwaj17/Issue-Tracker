import type { TaskOut, SubtaskOut, Comment, Story } from "./api";

// Backward-compat aliases so existing tests and TaskRows still compile
export type Task = TaskOut;
export type Subtask = SubtaskOut;

type Role = "owner" | "member";

/**
 * is_done toggle: if task has assignee → only assignee, reporter, or owner.
 * If unassigned → any member can toggle.
 */
export function canToggleIsDone(
  task: TaskOut | SubtaskOut,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  if (!task.assignee) return true; // unassigned → any member
  if (task.reporterId === currentUserId) return true; // task creator
  return task.assignee.id === currentUserId;
}

/**
 * Edit/delete task/subtask: only reporter (creator) or owner.
 */
export function canModifyTask(
  task: TaskOut | SubtaskOut,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  return task.reporterId === currentUserId;
}

/**
 * Edit comment: only author.
 */
export function canEditComment(
  comment: Comment,
  currentUserId: string,
): boolean {
  return comment.author.id === currentUserId;
}

/**
 * Delete comment: author OR owner.
 */
export function canDeleteComment(
  comment: Comment,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  return comment.author.id === currentUserId;
}

/**
 * Story status change: if story has assignee → only assignee or owner.
 * If unassigned → reporter or owner (edit guard alignment with backend).
 */
export function canChangeStatus(
  story: Story,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  if (!story.assignee) return story.reporter.id === currentUserId;
  return story.assignee.id === currentUserId;
}

/**
 * Edit/delete story: only reporter (creator) or owner.
 */
export function canModifyStory(
  story: Story,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  return story.reporter.id === currentUserId;
}

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
 * Whether the current user can delete a task or subtask.
 * Only the reporter or project owner.
 */
export function canDeleteTask(
  item: TaskOut | SubtaskOut,
  userId: string,
  role: Role,
): boolean {
  if (role === "owner") return true;
  return item.reporterId === userId;
}
