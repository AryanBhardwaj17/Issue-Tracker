"use client";

import { useState } from "react";
import { useTasks, useCreateTask, useUpdateTask, useDeleteTask, useCreateSubtask, useUpdateSubtask, useDeleteSubtask } from "@/hooks/useTasks";
import type { TaskOut, SubtaskOut, UserRef } from "@/lib/api";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { canModifyTask } from "@/lib/auth-predicates";
import { useAuthStore } from "@/stores/authStore";

const PRIORITY_OPTIONS = ["low", "medium", "high", "critical"];
const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

interface TasksSectionProps {
  projectId: string;
  storyId: string;
  userRole: "owner" | "member";
  storyAssignee: UserRef | null;
}

export default function TasksSection({ projectId, storyId, userRole, storyAssignee }: TasksSectionProps) {
  const { data, isLoading } = useTasks(projectId, storyId);
  const createTask = useCreateTask(projectId, storyId);
  const updateTask = useUpdateTask(projectId, storyId);
  const deleteTask = useDeleteTask(projectId, storyId);
  const createSubtask = useCreateSubtask(projectId, storyId);
  const updateSubtask = useUpdateSubtask(projectId, storyId);
  const deleteSubtask = useDeleteSubtask(projectId, storyId);

  const currentUser = useAuthStore((s) => s.user);

  const [showAddTask, setShowAddTask] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState("medium");
  const [newTaskDueDate, setNewTaskDueDate] = useState("");
  const [addingSubtaskFor, setAddingSubtaskFor] = useState<string | null>(null);
  const [subtaskTitle, setSubtaskTitle] = useState("");
  const [subtaskDesc, setSubtaskDesc] = useState("");
  const [subtaskPriority, setSubtaskPriority] = useState("medium");
  const [subtaskDueDate, setSubtaskDueDate] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; parentId?: string; title: string } | null>(null);

  const tasks = data?.items ?? [];

  const handleCreateTask = () => {
    if (!newTaskTitle.trim()) return;
    createTask.mutate({
      title: newTaskTitle.trim(),
      description: newTaskDesc.trim() || null,
      priority: newTaskPriority,
      dueDate: newTaskDueDate || null,
      assigneeId: storyAssignee?.id ?? null,
    }, {
      onSuccess: () => {
        setNewTaskTitle("");
        setNewTaskDesc("");
        setNewTaskPriority("medium");
        setNewTaskDueDate("");
        setShowAddTask(false);
      },
    });
  };

  const handleCreateSubtask = (parentTaskId: string) => {
    if (!subtaskTitle.trim()) return;
    createSubtask.mutate({
      parentTaskId,
      body: {
        title: subtaskTitle.trim(),
        description: subtaskDesc.trim() || null,
        priority: subtaskPriority,
        dueDate: subtaskDueDate || null,
        assigneeId: storyAssignee?.id ?? null,
      },
    }, {
      onSuccess: () => {
        setSubtaskTitle("");
        setSubtaskDesc("");
        setSubtaskPriority("medium");
        setSubtaskDueDate("");
        setAddingSubtaskFor(null);
      },
    });
  };

  const handleToggle = (task: TaskOut | SubtaskOut, parentId?: string) => {
    if (parentId) {
      updateSubtask.mutate({ parentTaskId: parentId, subtaskId: task.id, body: { isDone: !task.isDone } });
    } else {
      // Block completing a parent task if it has incomplete subtasks
      const t = task as TaskOut;
      if (!t.isDone && t.subtasks?.length > 0 && t.subtasks.some((s) => !s.isDone)) {
        return;
      }
      updateTask.mutate({ taskId: task.id, body: { isDone: !task.isDone } });
    }
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    if (deleteTarget.parentId) {
      deleteSubtask.mutate({ parentTaskId: deleteTarget.parentId, subtaskId: deleteTarget.id }, {
        onSuccess: () => setDeleteTarget(null),
      });
    } else {
      deleteTask.mutate(deleteTarget.id, {
        onSuccess: () => setDeleteTarget(null),
      });
    }
  };

  const completedCount = tasks.reduce((acc, t) => {
    const taskDone = t.isDone ? 1 : 0;
    const subDone = t.subtasks.filter((s) => s.isDone).length;
    return acc + taskDone + subDone;
  }, 0);
  const totalCount = tasks.reduce((acc, t) => 1 + t.subtasks.length + acc, 0);

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-900">Tasks</h3>
          {totalCount > 0 && (
            <span className="text-xs text-gray-500">
              {completedCount}/{totalCount} done
            </span>
          )}
        </div>
        <Button variant="secondary" onClick={() => setShowAddTask(true)} className="!px-3 !py-1 text-xs">
          + Add Task
        </Button>
      </div>

      {/* Content */}
      <div className="divide-y divide-gray-50">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-gray-600" />
          </div>
        )}

        {!isLoading && tasks.length === 0 && !showAddTask && (
          <div className="px-4 py-8 text-center text-sm text-gray-400">
            No tasks yet. Add a task to break this story into smaller pieces.
          </div>
        )}

        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            currentUserId={currentUser?.id ?? ""}
            userRole={userRole}
            storyAssignee={storyAssignee}
            onToggle={(t, pid) => handleToggle(t, pid)}
            onDelete={(id, parentId, title) => setDeleteTarget({ id, parentId, title })}
            onUpdateTask={(taskId, body) => updateTask.mutate({ taskId, body })}
            onUpdateSubtask={(parentTaskId, subtaskId, body) => updateSubtask.mutate({ parentTaskId, subtaskId, body })}
            onAddSubtask={() => { setAddingSubtaskFor(task.id); setSubtaskTitle(""); setSubtaskDesc(""); setSubtaskPriority("medium"); setSubtaskDueDate(""); }}
            addingSubtask={addingSubtaskFor === task.id}
            subtaskTitle={subtaskTitle}
            subtaskDesc={subtaskDesc}
            subtaskPriority={subtaskPriority}
            subtaskDueDate={subtaskDueDate}
            onSubtaskTitleChange={setSubtaskTitle}
            onSubtaskDescChange={setSubtaskDesc}
            onSubtaskPriorityChange={setSubtaskPriority}
            onSubtaskDueDateChange={setSubtaskDueDate}
            onSubtaskSubmit={() => handleCreateSubtask(task.id)}
            onSubtaskCancel={() => setAddingSubtaskFor(null)}
            isCreatingSubtask={createSubtask.isPending}
          />
        ))}

        {/* Add task inline form */}
        {showAddTask && (
          <div className="px-4 py-3 space-y-2">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleCreateTask(); if (e.key === "Escape") setShowAddTask(false); }}
                placeholder="Task title..."
                className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
                maxLength={500}
              />
              <select
                value={newTaskPriority}
                onChange={(e) => setNewTaskPriority(e.target.value)}
                className="rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <input
                type="date"
                value={newTaskDueDate}
                onChange={(e) => setNewTaskDueDate(e.target.value)}
                className="rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
              />
            </div>
            <textarea
              value={newTaskDesc}
              onChange={(e) => setNewTaskDesc(e.target.value)}
              placeholder="Description (optional)..."
              rows={2}
              maxLength={5000}
              className="w-full resize-none rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="flex items-center gap-2">
              <Button variant="primary" onClick={handleCreateTask} isLoading={createTask.isPending} className="!px-3 !py-1.5 text-xs">
                Add
              </Button>
              <Button variant="secondary" onClick={() => setShowAddTask(false)} className="!px-3 !py-1.5 text-xs">
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Task"
        message={`Are you sure you want to delete "${deleteTarget?.title}"?`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteTask.isPending || deleteSubtask.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}

// ── Task Item ─────────────────────────────────────────────────────────────────

interface TaskItemProps {
  task: TaskOut;
  currentUserId: string;
  userRole: "owner" | "member";
  storyAssignee: UserRef | null;
  onToggle: (task: TaskOut | SubtaskOut, parentId?: string) => void;
  onDelete: (id: string, parentId: string | undefined, title: string) => void;
  onUpdateTask: (taskId: string, body: Record<string, unknown>) => void;
  onUpdateSubtask: (parentTaskId: string, subtaskId: string, body: Record<string, unknown>) => void;
  onAddSubtask: () => void;
  addingSubtask: boolean;
  subtaskTitle: string;
  subtaskDesc: string;
  subtaskPriority: string;
  subtaskDueDate: string;
  onSubtaskTitleChange: (v: string) => void;
  onSubtaskDescChange: (v: string) => void;
  onSubtaskPriorityChange: (v: string) => void;
  onSubtaskDueDateChange: (v: string) => void;
  onSubtaskSubmit: () => void;
  onSubtaskCancel: () => void;
  isCreatingSubtask: boolean;
}

function TaskItem({
  task,
  currentUserId,
  userRole,
  storyAssignee,
  onToggle,
  onDelete,
  onUpdateTask,
  onUpdateSubtask,
  onAddSubtask,
  addingSubtask,
  subtaskTitle,
  subtaskDesc,
  subtaskPriority,
  subtaskDueDate,
  onSubtaskTitleChange,
  onSubtaskDescChange,
  onSubtaskPriorityChange,
  onSubtaskDueDateChange,
  onSubtaskSubmit,
  onSubtaskCancel,
  isCreatingSubtask,
}: TaskItemProps) {
  const isStoryAssignee = storyAssignee?.id === currentUserId;
  const canToggle = userRole === "owner" || !storyAssignee || task.reporterId === currentUserId || isStoryAssignee;
  const canDelete = canModifyTask(task, currentUserId, userRole);
  const hasIncompleteSubtasks = !task.isDone && task.subtasks.length > 0 && task.subtasks.some((s) => !s.isDone);
  const toggleDisabled = !canToggle || hasIncompleteSubtasks;
  const toggleTitle = hasIncompleteSubtasks
    ? "Complete all subtasks first"
    : !canToggle
      ? "Only the assignee, reporter, or owner can toggle completion"
      : undefined;
  const [expanded, setExpanded] = useState(false);
  const [editingDesc, setEditingDesc] = useState(false);
  const [descDraft, setDescDraft] = useState(task.description || "");

  const handleDescSave = () => {
    const trimmed = descDraft.trim();
    if (trimmed !== (task.description || "")) {
      onUpdateTask(task.id, { description: trimmed || null });
    }
    setEditingDesc(false);
  };

  return (
    <div className="px-4 py-2">
      {/* Root task — title row */}
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={task.isDone}
          onChange={() => onToggle(task)}
          disabled={toggleDisabled}
          title={toggleTitle}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <span className={`flex-1 text-sm ${task.isDone ? "text-gray-400 line-through" : "text-gray-800"}`}>
          {task.title}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded((p) => !p)}
            className="rounded px-1.5 py-0.5 text-xs text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            title={expanded ? "Collapse" : "Expand details"}
          >
            {expanded ? "▾" : "▸"}
          </button>
          <button
            onClick={onAddSubtask}
            className="rounded px-1.5 py-0.5 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            title="Add subtask"
          >
            + Subtask
          </button>
          {canDelete && (
            <button
              onClick={() => onDelete(task.id, undefined, task.title)}
              className="rounded px-1.5 py-0.5 text-xs text-red-400 hover:bg-red-50 hover:text-red-600"
              title="Delete task"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      {/* Metadata row — always visible */}
      <div className="ml-7 mt-1 flex flex-wrap items-center gap-2 text-xs">
        {/* Priority — inline editable */}
        <select
          value={task.priority}
          onChange={(e) => onUpdateTask(task.id, { priority: e.target.value })}
          className={`cursor-pointer rounded-full px-2 py-0.5 text-xs font-medium border-0 ${PRIORITY_COLORS[task.priority] || "bg-gray-100 text-gray-600"}`}
        >
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        {/* Assignee — read-only */}
        <span className="text-gray-500" title="Assignee (inherited from story)">
          👤 {storyAssignee?.name || "Unassigned"}
        </span>

        {/* Due date — inline editable */}
        <span className="flex items-center gap-1 text-gray-500">
          📅
          <input
            type="date"
            value={task.dueDate ?? ""}
            onChange={(e) => onUpdateTask(task.id, { dueDate: e.target.value || null })}
            className="border-0 bg-transparent p-0 text-xs text-gray-500 focus:outline-none focus:ring-0"
          />
          {!task.dueDate && <span className="text-gray-400">No due date</span>}
        </span>
      </div>

      {/* Description — expandable */}
      {expanded && (
        <div className="ml-7 mt-2">
          {editingDesc ? (
            <div>
              <textarea
                value={descDraft}
                onChange={(e) => setDescDraft(e.target.value)}
                rows={3}
                maxLength={5000}
                className="w-full resize-y rounded border border-gray-300 px-2 py-1.5 text-xs text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
                placeholder="Add a description..."
                onKeyDown={(e) => { if (e.key === "Escape") { setDescDraft(task.description || ""); setEditingDesc(false); } if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); handleDescSave(); } }}
              />
              <div className="mt-1 flex items-center gap-2">
                <button onClick={handleDescSave} className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700">Save</button>
                <button onClick={() => { setDescDraft(task.description || ""); setEditingDesc(false); }} className="rounded px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100">Cancel</button>
              </div>
            </div>
          ) : (
            <div
              onClick={() => { setDescDraft(task.description || ""); setEditingDesc(true); }}
              className={`cursor-pointer rounded px-2 py-1 text-xs hover:bg-gray-50 ${task.description ? "text-gray-600" : "italic text-gray-400 border border-dashed border-gray-200"}`}
            >
              {task.description || "Click to add description..."}
            </div>
          )}
        </div>
      )}

      {/* Subtasks */}
      {task.subtasks.length > 0 && (
        <div className="ml-7 mt-1 space-y-1 border-l-2 border-gray-200 pl-3">
          {task.subtasks.map((subtask) => {
            const canToggleSub = userRole === "owner" || !storyAssignee || subtask.reporterId === currentUserId || isStoryAssignee;
            const canDeleteSub = canModifyTask(subtask, currentUserId, userRole);
            return (
              <SubtaskRow
                key={subtask.id}
                subtask={subtask}
                parentTaskId={task.id}
                storyAssignee={storyAssignee}
                canToggle={canToggleSub}
                canDelete={canDeleteSub}
                onToggle={onToggle}
                onDelete={onDelete}
                onUpdate={(body) => onUpdateSubtask(task.id, subtask.id, body)}
              />
            );
          })}
        </div>
      )}

      {/* Add subtask inline form */}
      {addingSubtask && (
        <div className="ml-7 mt-2 space-y-2 pl-3">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={subtaskTitle}
              onChange={(e) => onSubtaskTitleChange(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) onSubtaskSubmit(); if (e.key === "Escape") onSubtaskCancel(); }}
              placeholder="Subtask title..."
              className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
              maxLength={500}
            />
            <select
              value={subtaskPriority}
              onChange={(e) => onSubtaskPriorityChange(e.target.value)}
              className="rounded border border-gray-300 px-1.5 py-1 text-xs focus:border-blue-500 focus:outline-none"
            >
              {PRIORITY_OPTIONS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <input
              type="date"
              value={subtaskDueDate}
              onChange={(e) => onSubtaskDueDateChange(e.target.value)}
              className="rounded border border-gray-300 px-1.5 py-1 text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>
          <textarea
            value={subtaskDesc}
            onChange={(e) => onSubtaskDescChange(e.target.value)}
            placeholder="Description (optional)..."
            rows={2}
            maxLength={5000}
            className="w-full resize-none rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <div className="flex items-center gap-2">
            <button
              onClick={onSubtaskSubmit}
              disabled={isCreatingSubtask}
              className="rounded bg-gray-800 px-2 py-1 text-xs text-white hover:bg-gray-700 disabled:opacity-50"
            >
              Add
            </button>
            <button
              onClick={onSubtaskCancel}
              className="rounded px-2 py-1 text-xs text-gray-500 hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Subtask Row ───────────────────────────────────────────────────────────────

interface SubtaskRowProps {
  subtask: SubtaskOut;
  parentTaskId: string;
  storyAssignee: UserRef | null;
  canToggle: boolean;
  canDelete: boolean;
  onToggle: (task: SubtaskOut, parentId: string) => void;
  onDelete: (id: string, parentId: string, title: string) => void;
  onUpdate: (body: Record<string, unknown>) => void;
}

function SubtaskRow({ subtask, parentTaskId, storyAssignee, canToggle, canDelete, onToggle, onDelete, onUpdate }: SubtaskRowProps) {
  const [expanded, setExpanded] = useState(false);
  const [editingDesc, setEditingDesc] = useState(false);
  const [descDraft, setDescDraft] = useState(subtask.description || "");

  const handleDescSave = () => {
    const trimmed = descDraft.trim();
    if (trimmed !== (subtask.description || "")) {
      onUpdate({ description: trimmed || null });
    }
    setEditingDesc(false);
  };

  return (
    <div>
      <div className="flex items-center gap-3 rounded px-1 py-0.5 hover:bg-gray-50">
        <input
          type="checkbox"
          checked={subtask.isDone}
          onChange={() => onToggle(subtask, parentTaskId)}
          disabled={!canToggle}
          title={!canToggle ? "Only the assignee or owner can toggle completion" : undefined}
          className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <span className={`flex-1 text-xs ${subtask.isDone ? "text-gray-400 line-through" : "text-gray-700"}`}>
          {subtask.title}
        </span>
        <button
          onClick={() => setExpanded((p) => !p)}
          className="rounded px-1 py-0.5 text-xs text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          title={expanded ? "Collapse" : "Expand details"}
        >
          {expanded ? "▾" : "▸"}
        </button>
        {canDelete && (
          <button
            onClick={() => onDelete(subtask.id, parentTaskId, subtask.title)}
            className="rounded px-1.5 py-0.5 text-xs text-red-400 hover:bg-red-50 hover:text-red-600"
            title="Delete subtask"
          >
            Delete
          </button>
        )}
      </div>

      {/* Subtask metadata */}
      <div className="ml-6 mt-0.5 flex flex-wrap items-center gap-2 text-xs">
        <select
          value={subtask.priority}
          onChange={(e) => onUpdate({ priority: e.target.value })}
          className={`cursor-pointer rounded-full px-2 py-0.5 text-xs font-medium border-0 ${PRIORITY_COLORS[subtask.priority] || "bg-gray-100 text-gray-600"}`}
        >
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <span className="text-gray-500">
          👤 {storyAssignee?.name || "Unassigned"}
        </span>
        <span className="flex items-center gap-1 text-gray-500">
          📅
          <input
            type="date"
            value={subtask.dueDate ?? ""}
            onChange={(e) => onUpdate({ dueDate: e.target.value || null })}
            className="border-0 bg-transparent p-0 text-xs text-gray-500 focus:outline-none focus:ring-0"
          />
          {!subtask.dueDate && <span className="text-gray-400">No due date</span>}
        </span>
      </div>

      {/* Subtask description — expandable */}
      {expanded && (
        <div className="ml-6 mt-1">
          {editingDesc ? (
            <div>
              <textarea
                value={descDraft}
                onChange={(e) => setDescDraft(e.target.value)}
                rows={2}
                maxLength={5000}
                className="w-full resize-y rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
                placeholder="Add a description..."
                onKeyDown={(e) => { if (e.key === "Escape") { setDescDraft(subtask.description || ""); setEditingDesc(false); } if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); handleDescSave(); } }}
              />
              <div className="mt-1 flex items-center gap-2">
                <button onClick={handleDescSave} className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700">Save</button>
                <button onClick={() => { setDescDraft(subtask.description || ""); setEditingDesc(false); }} className="rounded px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100">Cancel</button>
              </div>
            </div>
          ) : (
            <div
              onClick={() => { setDescDraft(subtask.description || ""); setEditingDesc(true); }}
              className={`cursor-pointer rounded px-2 py-1 text-xs hover:bg-gray-50 ${subtask.description ? "text-gray-600" : "italic text-gray-400 border border-dashed border-gray-200"}`}
            >
              {subtask.description || "Click to add description..."}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
