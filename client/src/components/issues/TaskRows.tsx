"use client";

import { useState } from "react";
import { useTasks, useToggleTaskDone, useToggleSubtaskDone } from "@/hooks/useTasks";
import { canToggleIsDone } from "@/lib/auth-predicates";
import Checkbox from "@/components/ui/Checkbox";
import PriorityBadge from "@/components/stories/PriorityBadge";
import AssigneeAvatar from "@/components/stories/AssigneeAvatar";
import type { Task, Subtask, Priority } from "@/lib/api";

// ─── Column count must match IssuesTable (9 columns) ─────────────────────────
const COL_SPAN = 9;

interface TaskRowsProps {
  projectId: string;
  storyId: string;
  userId: string;
  role: "owner" | "member";
}

export default function TaskRows({ projectId, storyId, userId, role }: TaskRowsProps) {
  const { data, isLoading, isError } = useTasks(projectId, storyId);
  const toggleTask = useToggleTaskDone(projectId, storyId);

  if (isLoading) {
    return (
      <tr>
        <td colSpan={COL_SPAN} className="bg-gray-50/50 px-10 py-4">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-700" />
            <span className="text-xs text-gray-400">Loading tasks…</span>
          </div>
        </td>
      </tr>
    );
  }

  if (isError) {
    return (
      <tr>
        <td colSpan={COL_SPAN} className="bg-red-50/30 px-10 py-3">
          <span className="text-xs text-red-500">Failed to load tasks</span>
        </td>
      </tr>
    );
  }

  const tasks = data?.items ?? [];

  if (tasks.length === 0) {
    return (
      <tr>
        <td colSpan={COL_SPAN} className="bg-gray-50/50 px-10 py-3">
          <span className="text-xs text-gray-400">No tasks</span>
        </td>
      </tr>
    );
  }

  return (
    <>
      {tasks.map((task) => (
        <TaskRow
          key={task.id}
          task={task}
          projectId={projectId}
          storyId={storyId}
          userId={userId}
          role={role}
          onToggleDone={(checked) =>
            toggleTask.mutate({ taskId: task.id, body: { isDone: checked } })
          }
        />
      ))}
    </>
  );
}

// ─── Single task row ──────────────────────────────────────────────────────────

interface TaskRowProps {
  task: Task;
  projectId: string;
  storyId: string;
  userId: string;
  role: "owner" | "member";
  onToggleDone: (checked: boolean) => void;
}

function TaskRow({ task, projectId, storyId, userId, role, onToggleDone }: TaskRowProps) {
  const [expanded, setExpanded] = useState(false);
  const canToggle = canToggleIsDone(task, userId, role);
  const hasSubtasks = task.subtasks.length > 0;

  return (
    <>
      <tr className="border-t border-gray-100 bg-gray-50/50 transition-colors hover:bg-gray-100/60">
        {/* Expand / indent */}
        <td className="px-4 py-2.5">
          {hasSubtasks ? (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded((v) => !v);
              }}
              className="ml-3 flex h-4 w-4 items-center justify-center rounded text-xs text-gray-400 hover:text-gray-700"
            >
              {expanded ? "▼" : "▶"}
            </button>
          ) : (
            <span className="ml-3 inline-block w-4" />
          )}
        </td>

        {/* Title */}
        <td className="px-4 py-2.5">
          <div className="flex items-center gap-2 pl-4">
            <Checkbox
              checked={task.isDone}
              disabled={!canToggle}
              onChange={onToggleDone}
              title={canToggle ? undefined : "Only the assignee or owner can toggle"}
            />
            <span className={`text-sm ${task.isDone ? "text-gray-400 line-through" : "text-gray-700"}`}>
              {task.title}
            </span>
          </div>
        </td>

        {/* Status — empty for tasks */}
        <td className="px-4 py-2.5" />

        {/* Priority */}
        <td className="px-4 py-2.5">
          <PriorityBadge priority={task.priority as Priority} />
        </td>

        {/* Points — N/A for tasks */}
        <td className="px-4 py-2.5" />

        {/* Assignee */}
        <td className="px-4 py-2.5">
          <AssigneeAvatar
            assignee={task.assignee ? { id: task.assignee.id, name: task.assignee.name } : null}
            showName
          />
        </td>

        {/* Epic — N/A */}
        <td className="px-4 py-2.5" />

        {/* Due Date — N/A */}
        <td className="px-4 py-2.5" />

        {/* Created — N/A */}
        <td className="px-4 py-2.5" />
      </tr>

      {/* Subtask rows */}
      {expanded &&
        task.subtasks.map((subtask) => (
          <SubtaskRow
            key={subtask.id}
            subtask={subtask}
            projectId={projectId}
            storyId={storyId}
            parentTaskId={task.id}
            userId={userId}
            role={role}
          />
        ))}
    </>
  );
}

// ─── Single subtask row ───────────────────────────────────────────────────────

interface SubtaskRowProps {
  subtask: Subtask;
  projectId: string;
  storyId: string;
  parentTaskId: string;
  userId: string;
  role: "owner" | "member";
}

function SubtaskRow({ subtask, projectId, storyId, parentTaskId, userId, role }: SubtaskRowProps) {
  const toggleSubtask = useToggleSubtaskDone(projectId, parentTaskId, storyId);
  const canToggle = canToggleIsDone(subtask, userId, role);

  return (
    <tr className="border-t border-gray-100 bg-gray-50/30 transition-colors hover:bg-gray-100/40">
      {/* Indent */}
      <td className="px-4 py-2" />

      {/* Title */}
      <td className="px-4 py-2">
        <div className="flex items-center gap-2 pl-12">
          <Checkbox
            checked={subtask.isDone}
            disabled={!canToggle}
            onChange={(checked) =>
              toggleSubtask.mutate({ subtaskId: subtask.id, body: { isDone: checked } })
            }
            title={canToggle ? undefined : "Only the assignee or owner can toggle"}
          />
          <span className={`text-xs ${subtask.isDone ? "text-gray-400 line-through" : "text-gray-600"}`}>
            {subtask.title}
          </span>
        </div>
      </td>

      {/* Remaining columns empty */}
      <td className="px-4 py-2" />
      <td className="px-4 py-2" />
      <td className="px-4 py-2" />
      <td className="px-4 py-2" />
      <td className="px-4 py-2" />
      <td className="px-4 py-2" />
      <td className="px-4 py-2" />
    </tr>
  );
}
