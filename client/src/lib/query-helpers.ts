import { QueryClient } from "@tanstack/react-query";

/**
 * Bulk-invalidates all query keys related to a story mutation.
 * Call this in `onSuccess` / `onSettled` of any story, task, or comment mutation
 * to ensure Board, Backlog, Table, and Drawer all stay in sync.
 */
export function invalidateStoryRelated(
  qc: QueryClient,
  projectId: string,
  storyId?: string,
) {
  // Stories list (Board, Backlog, Table all use this key prefix)
  qc.invalidateQueries({ queryKey: ["stories", projectId] });
  // Epics progress bars update when story statuses change
  qc.invalidateQueries({ queryKey: ["epics", projectId] });
  if (storyId) {
    qc.invalidateQueries({ queryKey: ["story", storyId] });
    qc.invalidateQueries({ queryKey: ["tasks", storyId] });
    qc.invalidateQueries({ queryKey: ["comments", storyId] });
  }
}
