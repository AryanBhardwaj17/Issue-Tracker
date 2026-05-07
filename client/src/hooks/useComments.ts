import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  listComments,
  createComment,
  updateComment,
  deleteComment,
  listTaskComments,
  createTaskComment,
  updateTaskComment,
  deleteTaskComment,
  listSubtaskComments,
  createSubtaskComment,
  updateSubtaskComment,
  deleteSubtaskComment,
  listEpicComments,
  createEpicComment,
  updateEpicComment,
  deleteEpicComment,
  uploadImage,
  type CommentCreatePayload,
  type CommentPatchPayload,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

// Scope resolution: epicId > subtaskId > taskId > story (default)
function resolveScope(
  projectId: string,
  storyId: string,
  taskId?: string,
  subtaskId?: string,
  epicId?: string,
) {
  if (epicId) {
    return { scope: "epic" as const, keyPrefix: ["comments", "epic", projectId, epicId] };
  }
  if (subtaskId) {
    return { scope: "subtask" as const, keyPrefix: ["comments", "subtask", projectId, subtaskId] };
  }
  if (taskId) {
    return { scope: "task" as const, keyPrefix: ["comments", "task", projectId, taskId] };
  }
  return { scope: "story" as const, keyPrefix: ["comments", projectId, storyId] };
}

export function useComments(
  projectId: string,
  storyId: string,
  page = 1,
  pageSize = 25,
  taskId?: string,
  subtaskId?: string,
  epicId?: string,
) {
  const { scope, keyPrefix } = resolveScope(projectId, storyId, taskId, subtaskId, epicId);

  const enabledId =
    scope === "epic" ? !!epicId :
    scope === "subtask" ? !!subtaskId :
    scope === "task" ? !!taskId :
    !!storyId;

  return useQuery({
    queryKey: [...keyPrefix, page, pageSize],
    queryFn: () => {
      if (scope === "epic") return listEpicComments(projectId, epicId!, page, pageSize);
      if (scope === "subtask") return listSubtaskComments(projectId, storyId, taskId!, subtaskId!, page, pageSize);
      if (scope === "task") return listTaskComments(projectId, storyId, taskId!, page, pageSize);
      return listComments(projectId, storyId, page, pageSize);
    },
    enabled: !!projectId && enabledId,
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });
}

export function useCreateComment(
  projectId: string,
  storyId: string,
  taskId?: string,
  subtaskId?: string,
  epicId?: string,
) {
  const qc = useQueryClient();
  const { scope, keyPrefix } = resolveScope(projectId, storyId, taskId, subtaskId, epicId);

  return useMutation({
    mutationFn: (body: CommentCreatePayload) => {
      if (scope === "epic") return createEpicComment(projectId, epicId!, body);
      if (scope === "subtask") return createSubtaskComment(projectId, storyId, taskId!, subtaskId!, body);
      if (scope === "task") return createTaskComment(projectId, storyId, taskId!, body);
      return createComment(projectId, storyId, body);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keyPrefix });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to post comment")),
  });
}

export function useUpdateComment(
  projectId: string,
  storyId: string,
  taskId?: string,
  subtaskId?: string,
  epicId?: string,
) {
  const qc = useQueryClient();
  const { scope, keyPrefix } = resolveScope(projectId, storyId, taskId, subtaskId, epicId);

  return useMutation({
    mutationFn: ({ commentId, body }: { commentId: string; body: CommentPatchPayload }) => {
      if (scope === "epic") return updateEpicComment(projectId, epicId!, commentId, body);
      if (scope === "subtask") return updateSubtaskComment(projectId, storyId, taskId!, subtaskId!, commentId, body);
      if (scope === "task") return updateTaskComment(projectId, storyId, taskId!, commentId, body);
      return updateComment(projectId, storyId, commentId, body);
    },
    onSuccess: () => {
      toast.success("Comment updated");
      qc.invalidateQueries({ queryKey: keyPrefix });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update comment")),
  });
}

export function useDeleteComment(
  projectId: string,
  storyId: string,
  taskId?: string,
  subtaskId?: string,
  epicId?: string,
) {
  const qc = useQueryClient();
  const { scope, keyPrefix } = resolveScope(projectId, storyId, taskId, subtaskId, epicId);

  return useMutation({
    mutationFn: (commentId: string) => {
      if (scope === "epic") return deleteEpicComment(projectId, epicId!, commentId);
      if (scope === "subtask") return deleteSubtaskComment(projectId, storyId, taskId!, subtaskId!, commentId);
      if (scope === "task") return deleteTaskComment(projectId, storyId, taskId!, commentId);
      return deleteComment(projectId, storyId, commentId);
    },
    onSuccess: () => {
      toast.success("Comment deleted");
      qc.invalidateQueries({ queryKey: keyPrefix });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete comment")),
  });
}

export function useUploadImage() {
  return useMutation({
    mutationFn: (file: File) => uploadImage(file),
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to upload image")),
  });
}
