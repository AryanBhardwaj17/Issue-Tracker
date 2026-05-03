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
  uploadImage,
  type CommentCreatePayload,
  type CommentPatchPayload,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useComments(projectId: string, storyId: string, page = 1, pageSize = 25) {
  return useQuery({
    queryKey: ["comments", projectId, storyId, page, pageSize],
    queryFn: () => listComments(projectId, storyId, page, pageSize),
    enabled: !!projectId && !!storyId,
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });
}

export function useCreateComment(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CommentCreatePayload) => createComment(projectId, storyId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comments", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to post comment")),
  });
}

export function useUpdateComment(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ commentId, body }: { commentId: string; body: CommentPatchPayload }) =>
      updateComment(projectId, storyId, commentId, body),
    onSuccess: () => {
      toast.success("Comment updated");
      qc.invalidateQueries({ queryKey: ["comments", projectId, storyId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update comment")),
  });
}

export function useDeleteComment(projectId: string, storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (commentId: string) => deleteComment(projectId, storyId, commentId),
    onSuccess: () => {
      toast.success("Comment deleted");
      qc.invalidateQueries({ queryKey: ["comments", projectId, storyId] });
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
