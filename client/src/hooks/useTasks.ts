import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  listTasks,
  createTask,
  updateTask,
  deleteTask,
  createSubtask,
  updateSubtask,
  deleteSubtask,
  type TaskCreatePayload,
  type TaskPatchPayload,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useTasks(projectId: string, storyId: string, page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ["tasks", projectId, storyId, page, pageSize],
    queryFn: () => listTasks(projectId, storyId, page, pageSize),
    enabled: !!projectId && !!storyId,
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });
}

export function useCreateTask(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TaskCreatePayload) => createTask(projectId, storyId, body),
    onSuccess: () => {
      toast.success("Task created");
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to create task")),
  });
}

export function useUpdateTask(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, body }: { taskId: string; body: TaskPatchPayload }) =>
      updateTask(projectId, storyId, taskId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update task")),
  });
}

export function useDeleteTask(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => deleteTask(projectId, storyId, taskId),
    onSuccess: () => {
      toast.success("Task deleted");
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete task")),
  });
}

export function useCreateSubtask(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ parentTaskId, body }: { parentTaskId: string; body: TaskCreatePayload }) =>
      createSubtask(projectId, parentTaskId, body),
    onSuccess: () => {
      toast.success("Subtask created");
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to create subtask")),
  });
}

export function useUpdateSubtask(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      parentTaskId,
      subtaskId,
      body,
    }: {
      parentTaskId: string;
      subtaskId: string;
      body: TaskPatchPayload;
    }) => updateSubtask(projectId, parentTaskId, subtaskId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update subtask")),
  });
}

export function useDeleteSubtask(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ parentTaskId, subtaskId }: { parentTaskId: string; subtaskId: string }) =>
      deleteSubtask(projectId, parentTaskId, subtaskId),
    onSuccess: () => {
      toast.success("Subtask deleted");
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete subtask")),
  });
}

// ─── Backward-compat wrappers used by TaskRows.tsx ───────────────────────────

/** @deprecated Use useUpdateTask instead */
export function useToggleTaskDone(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, body }: { taskId: string; body: TaskPatchPayload }) =>
      updateTask(projectId, storyId, taskId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update task")),
  });
}

/** @deprecated Use useUpdateSubtask instead */
export function useToggleSubtaskDone(
  projectId: string,
  parentTaskId: string,
  storyId: string,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ subtaskId, body }: { subtaskId: string; body: TaskPatchPayload }) =>
      updateSubtask(projectId, parentTaskId, subtaskId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update subtask")),
  });
}
