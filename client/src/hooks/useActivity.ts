import { useQuery } from "@tanstack/react-query";
import {
  listStoryActivity,
  listTaskActivity,
  listEpicActivity,
  listProjectActivity,
} from "@/lib/api";

export type ActivityEntityType = "story" | "task" | "subtask" | "project" | "epic";

export function useActivity(
  entityType: ActivityEntityType,
  entityId: string,
  projectId: string,
  page = 1,
  pageSize = 20,
) {
  return useQuery({
    queryKey: ["activity", entityType, entityId, page, pageSize],
    queryFn: () => {
      switch (entityType) {
        case "story":
          return listStoryActivity(projectId, entityId, page, pageSize);
        case "task":
          return listTaskActivity(projectId, entityId, page, pageSize);
        case "subtask":
          // Subtasks are tasks — use the same task activity endpoint
          return listTaskActivity(projectId, entityId, page, pageSize);
        case "epic":
          return listEpicActivity(projectId, entityId, page, pageSize);
        case "project":
          return listProjectActivity(projectId, page, pageSize);
      }
    },
    enabled: !!entityType && !!entityId && !!projectId,
    staleTime: entityType === "project" ? 60_000 : 30_000,
  });
}
