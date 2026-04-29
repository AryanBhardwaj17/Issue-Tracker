import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  getProject,
  updateProject,
  deleteProject,
  listMembers,
  addMember,
  transferOwnership,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: !!projectId,
  });
}

export function useProjectMembers(projectId: string, page = 1) {
  return useQuery({
    queryKey: ["projectMembers", projectId, page],
    queryFn: () => listMembers(projectId, page),
    enabled: !!projectId,
  });
}

export function useUpdateProject(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name?: string; description?: string }) =>
      updateProject(projectId, body),
    onSuccess: () => {
      toast.success("Project updated");
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to update project")),
  });
}

export function useDeleteProject(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => deleteProject(projectId),
    onSuccess: () => {
      toast.success("Project deleted");
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to delete project")),
  });
}

export function useAddMember(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (email: string) => addMember(projectId, email),
    onSuccess: () => {
      toast.success("Member added");
      qc.invalidateQueries({ queryKey: ["projectMembers", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to add member")),
  });
}

export function useTransferOwnership(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (newOwnerId: string) => transferOwnership(projectId, newOwnerId),
    onSuccess: () => {
      toast.success("Ownership transferred");
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["projectMembers", projectId] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (err) => toast.error(extractErrorMessage(err, "Failed to transfer ownership")),
  });
}
