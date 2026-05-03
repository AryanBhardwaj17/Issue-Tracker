import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import {
  listTasks,
  patchTask,
  patchSubtask,
  type TaskPatchBody,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import { invalidateStoryRelated } from "@/lib/query-helpers";

/**
 * Fetch tasks for a story. Pass `enabled=false` to defer until the row is expanded.
 */
export function useTasks(
  projectId: string,
  storyId: string,
  enabled = true,
) {
  return useQuery({
    queryKey: ["tasks", storyId],
    queryFn: () => listTasks(projectId, storyId),
    enabled: !!projectId && !!storyId && enabled,
    staleTime: 30_000,
  });
}

/**
 * Toggle `isDone` (or patch other fields) on a top-level task.
 */
export function useToggleTaskDone(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      taskId,
      body,
    }: {
      taskId: string;
      body: TaskPatchBody;
    }) => patchTask(projectId, storyId, taskId, body),
    onSuccess: () => {
      invalidateStoryRelated(qc, projectId, storyId);
    },
    onError: (err) =>
      toast.error(extractErrorMessage(err, "Failed to update task")),
  });
}

/**
 * Toggle `isDone` (or patch other fields) on a subtask.
 */
export function useToggleSubtaskDone(
  projectId: string,
  parentTaskId: string,
  storyId: string,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      subtaskId,
      body,
    }: {
      subtaskId: string;
      body: TaskPatchBody;
    }) => patchSubtask(projectId, parentTaskId, subtaskId, body),
    onSuccess: () => {
      invalidateStoryRelated(qc, projectId, storyId);
    },
    onError: (err) =>
      toast.error(extractErrorMessage(err, "Failed to update subtask")),
  });
}
