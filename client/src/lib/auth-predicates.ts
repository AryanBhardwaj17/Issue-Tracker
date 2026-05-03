import type { TaskOut, SubtaskOut, Comment, Story } from "./api";

type Role = "owner" | "member";

/**
 * is_done toggle: if task has assignee → only assignee or owner.
 * If unassigned → any member can toggle.
 */
export function canToggleIsDone(
  task: TaskOut | SubtaskOut,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  if (!task.assignee) return true; // unassigned → any member
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
 * If unassigned → any member.
 */
export function canChangeStatus(
  story: Story,
  currentUserId: string,
  userRole: Role,
): boolean {
  if (userRole === "owner") return true;
  if (!story.assignee) return true;
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
