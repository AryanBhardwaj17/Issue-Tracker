import api from "./interceptor";
 
// ─── Types ───────────────────────────────────────────────────────────────────
 
export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}
 
export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}
 
export interface MessageResponse {
  message: string;
}
 
export async function registerUser(payload: {
  name: string;
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/signup", payload);
  return data;
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/login", payload);
  return data;
}

export async function refreshToken(): Promise<{ access_token: string }> {
  const { data } = await api.post<{ access_token: string; token_type: string }>(
    "/auth/refresh",
  );
  return data;
}
 
export async function logoutUser(): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>("/auth/logout");
  return data;
}
 
// ─── User API ────────────────────────────────────────────────────────────────
 
export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/users/me");
  return data;
}
 
 
export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<MessageResponse> {
  const { data } = await api.put<MessageResponse>(
    "/users/me/password",
    payload,
  );
  return data;
}

// ─── Envelope Types ──────────────────────────────────────────────────────────

export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface Envelope<T> {
  success: boolean;
  message: string;
  data: T;
  pagination?: PaginationMeta;
}

// ─── Project Types ───────────────────────────────────────────────────────────

export interface Project {
  id: string;
  name: string;
  key: string;
  description: string | null;
  role: "owner" | "member";
  memberCount: number;
  createdAt: string;
}

export interface ProjectOwner {
  id: string;
  name: string;
}

export interface ProjectDetail extends Project {
  owner: ProjectOwner;
  updatedAt: string;
}

export interface PaginatedResult<T> {
  items: T[];
  pagination: PaginationMeta;
}

// ─── Project API ─────────────────────────────────────────────────────────────

export async function listProjects(
  page = 1,
  pageSize = 25,
): Promise<PaginatedResult<Project>> {
  const { data } = await api.get<Envelope<Project[]>>("/projects", {
    params: { page, pageSize },
  });
  return {
    items: data.data,
    pagination: data.pagination!,
  };
}

export async function getProject(id: string): Promise<ProjectDetail> {
  const { data } = await api.get<Envelope<ProjectDetail>>(`/projects/${id}`);
  return data.data;
}

export async function createProject(body: {
  name: string;
  description?: string | null;
}): Promise<ProjectDetail> {
  const { data } = await api.post<Envelope<ProjectDetail>>("/projects", body);
  return data.data;
}

export async function updateProject(
  id: string,
  body: { name?: string; description?: string | null },
): Promise<ProjectDetail> {
  const { data } = await api.patch<Envelope<ProjectDetail>>(
    `/projects/${id}`,
    body,
  );
  return data.data;
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/projects/${id}`);
}

// ─── Member Types ─────────────────────────────────────────────────────────────

export interface MemberOut {
  id: string;
  userId: string;
  name: string;
  email: string;
  role: "owner" | "member";
  joinedAt: string;
}

// ─── Members API ─────────────────────────────────────────────────────────────

export async function listMembers(projectId: string): Promise<MemberOut[]> {
  const { data } = await api.get<Envelope<MemberOut[]>>(
    `/projects/${projectId}/members`,
  );
  return data.data;
}

export async function addMember(
  projectId: string,
  email: string,
): Promise<MemberOut> {
  const { data } = await api.post<Envelope<MemberOut>>(
    `/projects/${projectId}/members`,
    { email },
  );
  return data.data;
}

export async function transferOwnership(
  projectId: string,
  newOwnerId: string,
): Promise<void> {
  await api.post(`/projects/${projectId}/transfer-ownership`, { newOwnerId });
}

// ─── Epic Types ───────────────────────────────────────────────────────────────

export interface EpicReporter {
  id: string;
  name: string;
}

export interface EpicProgress {
  total: number;
  done: number;
}

export interface Epic {
  id: string;
  name: string;
  description: string | null;
  reporter: EpicReporter;
  progress: EpicProgress;
  createdAt: string;
  updatedAt: string;
}

// ─── Epic API ─────────────────────────────────────────────────────────────────

export async function listEpics(
  projectId: string,
  page = 1,
  pageSize = 25,
): Promise<PaginatedResult<Epic>> {
  const { data } = await api.get<Envelope<Epic[]>>(
    `/projects/${projectId}/epics`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function createEpic(
  projectId: string,
  body: { name: string; description?: string | null },
): Promise<Epic> {
  const { data } = await api.post<Envelope<Epic>>(
    `/projects/${projectId}/epics`,
    body,
  );
  return data.data;
}

export async function updateEpic(
  projectId: string,
  epicId: string,
  body: { name?: string; description?: string | null },
): Promise<Epic> {
  const { data } = await api.patch<Envelope<Epic>>(
    `/projects/${projectId}/epics/${epicId}`,
    body,
  );
  return data.data;
}

export async function deleteEpic(
  projectId: string,
  epicId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/epics/${epicId}`);
}

export async function getEpic(projectId: string, epicId: string): Promise<Epic> {
  const { data } = await api.get<Envelope<Epic>>(
    `/projects/${projectId}/epics/${epicId}`,
  );
  return data.data;
}

// ─── Story Types ──────────────────────────────────────────────────────────────

export type StoryStatus =
  | "backlog"
  | "todo"
  | "in_progress"
  | "in_review"
  | "testing"
  | "ready_for_prod"
  | "done";

export type Priority = "low" | "medium" | "high" | "critical";

export interface StoryUser {
  id: string;
  name: string;
}

export interface Story {
  id: string;
  storyKey: string;
  title: string;
  description: string | null;
  epicId: string | null;
  status: StoryStatus;
  priority: Priority;
  storyPoints: number | null;
  assignee: StoryUser | null;
  reporter: StoryUser;
  dueDate: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface StoryFilters {
  status?: StoryStatus[];
  priority?: Priority[];
  epicId?: string[];
  assigneeId?: string[];
  search?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

export interface StoryCreateBody {
  title: string;
  description?: string | null;
  epicId?: string | null;
  status?: StoryStatus;
  priority: Priority;
  storyPoints?: number | null;
  assigneeId?: string | null;
  dueDate?: string | null;
}

export interface StoryPatchBody {
  title?: string;
  description?: string | null;
  epicId?: string | null;
  status?: StoryStatus;
  priority?: Priority;
  storyPoints?: number | null;
  assigneeId?: string | null;
  dueDate?: string | null;
}

// ─── Story API ────────────────────────────────────────────────────────────────

export async function listStories(
  projectId: string,
  filters: StoryFilters = {},
): Promise<PaginatedResult<Story>> {
  // Build query string manually so arrays serialize as repeated params
  // (?status=backlog&status=todo) instead of (?status[]=backlog) which FastAPI
  // won't parse correctly with the alias Query() parameters.
  const params = new URLSearchParams();
  params.set("page", String(filters.page ?? 1));
  params.set("pageSize", String(filters.pageSize ?? 25));
  if (filters.status?.length) filters.status.forEach((s) => params.append("status", s));
  if (filters.priority?.length) filters.priority.forEach((p) => params.append("priority", p));
  if (filters.epicId?.length) filters.epicId.forEach((e) => params.append("epicId", e));
  if (filters.assigneeId?.length) filters.assigneeId.forEach((a) => params.append("assigneeId", a));
  if (filters.search) params.set("search", filters.search);
  if (filters.sortBy) params.set("sortBy", filters.sortBy);
  if (filters.sortOrder) params.set("sortOrder", filters.sortOrder);

  const { data } = await api.get<Envelope<Story[]>>(
    `/projects/${projectId}/stories?${params.toString()}`,
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function getStory(
  projectId: string,
  storyId: string,
): Promise<Story> {
  const { data } = await api.get<Envelope<Story>>(
    `/projects/${projectId}/stories/${storyId}`,
  );
  return data.data;
}

export async function createStory(
  projectId: string,
  body: StoryCreateBody,
): Promise<Story> {
  const { data } = await api.post<Envelope<Story>>(
    `/projects/${projectId}/stories`,
    body,
  );
  return data.data;
}

export async function patchStory(
  projectId: string,
  storyId: string,
  body: StoryPatchBody,
): Promise<Story> {
  const { data } = await api.patch<Envelope<Story>>(
    `/projects/${projectId}/stories/${storyId}`,
    body,
  );
  return data.data;
}

export async function deleteStory(
  projectId: string,
  storyId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/stories/${storyId}`);
}

/** Alias used by StoryHeader / StoryMetaSidebar components */
export type StoryPatchPayload = StoryPatchBody;

// ─── Task Types ───────────────────────────────────────────────────────────────

export interface UserRef {
  id: string;
  name: string;
}

export interface SubtaskOut {
  id: string;
  parentId: string;
  title: string;
  description: string | null;
  priority: string;
  assignee: UserRef | null;
  reporterId: string;
  dueDate: string | null;
  isDone: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface TaskOut {
  id: string;
  storyId: string;
  parentId: string | null;
  title: string;
  description: string | null;
  priority: string;
  assignee: UserRef | null;
  reporterId: string;
  dueDate: string | null;
  isDone: boolean;
  createdAt: string;
  updatedAt: string;
  subtasks: SubtaskOut[];
}

export interface TaskCreatePayload {
  title: string;
  description?: string | null;
  priority: string;
  assigneeId?: string | null;
  dueDate?: string | null;
}

export interface TaskPatchPayload {
  title?: string;
  description?: string | null;
  priority?: string;
  assigneeId?: string | null;
  dueDate?: string | null;
  isDone?: boolean;
}

// ─── Task API ─────────────────────────────────────────────────────────────────

export async function listTasks(
  projectId: string,
  storyId: string,
  page = 1,
  pageSize = 50,
): Promise<PaginatedResult<TaskOut>> {
  const { data } = await api.get<Envelope<TaskOut[]>>(
    `/projects/${projectId}/stories/${storyId}/tasks`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function createTask(
  projectId: string,
  storyId: string,
  body: TaskCreatePayload,
): Promise<TaskOut> {
  const { data } = await api.post<Envelope<TaskOut>>(
    `/projects/${projectId}/stories/${storyId}/tasks`,
    body,
  );
  return data.data;
}

export async function updateTask(
  projectId: string,
  storyId: string,
  taskId: string,
  body: TaskPatchPayload,
): Promise<TaskOut> {
  const { data } = await api.patch<Envelope<TaskOut>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}`,
    body,
  );
  return data.data;
}

export async function deleteTask(
  projectId: string,
  storyId: string,
  taskId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/stories/${storyId}/tasks/${taskId}`);
}

// ─── Subtask API ──────────────────────────────────────────────────────────────

export async function createSubtask(
  projectId: string,
  parentTaskId: string,
  body: TaskCreatePayload,
): Promise<SubtaskOut> {
  const { data } = await api.post<Envelope<SubtaskOut>>(
    `/projects/${projectId}/tasks/${parentTaskId}/subtasks`,
    body,
  );
  return data.data;
}

export async function updateSubtask(
  projectId: string,
  parentTaskId: string,
  subtaskId: string,
  body: TaskPatchPayload,
): Promise<TaskOut> {
  const { data } = await api.patch<Envelope<TaskOut>>(
    `/projects/${projectId}/tasks/${parentTaskId}/subtasks/${subtaskId}`,
    body,
  );
  return data.data;
}

export async function deleteSubtask(
  projectId: string,
  parentTaskId: string,
  subtaskId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/tasks/${parentTaskId}/subtasks/${subtaskId}`);
}

export async function getTask(
  projectId: string,
  storyId: string,
  taskId: string,
): Promise<TaskOut> {
  const { data } = await api.get<Envelope<TaskOut>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}`,
  );
  return data.data;
}

// ─── Comment Types ────────────────────────────────────────────────────────────

export interface CommentAuthor {
  id: string;
  name: string;
}

export interface Comment {
  id: string;
  userStoryId: string | null;
  taskId: string | null;
  epicId: string | null;
  author: CommentAuthor;
  body: string;
  imageUrl: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CommentCreatePayload {
  body: string;
  imageUrl?: string | null;
}

export interface CommentPatchPayload {
  body?: string;
  imageUrl?: string | null;
  removeImage?: boolean;
}

// ─── Comment API ──────────────────────────────────────────────────────────────

export async function listComments(
  projectId: string,
  storyId: string,
  page = 1,
  pageSize = 25,
): Promise<PaginatedResult<Comment>> {
  const { data } = await api.get<Envelope<Comment[]>>(
    `/projects/${projectId}/stories/${storyId}/comments`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function createComment(
  projectId: string,
  storyId: string,
  body: CommentCreatePayload,
): Promise<Comment> {
  const { data } = await api.post<Envelope<Comment>>(
    `/projects/${projectId}/stories/${storyId}/comments`,
    body,
  );
  return data.data;
}

export async function updateComment(
  projectId: string,
  storyId: string,
  commentId: string,
  body: CommentPatchPayload,
): Promise<Comment> {
  const { data } = await api.patch<Envelope<Comment>>(
    `/projects/${projectId}/stories/${storyId}/comments/${commentId}`,
    body,
  );
  return data.data;
}

export async function deleteComment(
  projectId: string,
  storyId: string,
  commentId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/stories/${storyId}/comments/${commentId}`);
}

// ─── Task Comment API ─────────────────────────────────────────────────────────

export async function listTaskComments(
  projectId: string,
  storyId: string,
  taskId: string,
  page = 1,
  pageSize = 25,
): Promise<PaginatedResult<Comment>> {
  const { data } = await api.get<Envelope<Comment[]>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/comments`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function createTaskComment(
  projectId: string,
  storyId: string,
  taskId: string,
  body: CommentCreatePayload,
): Promise<Comment> {
  const { data } = await api.post<Envelope<Comment>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/comments`,
    body,
  );
  return data.data;
}

export async function updateTaskComment(
  projectId: string,
  storyId: string,
  taskId: string,
  commentId: string,
  body: CommentPatchPayload,
): Promise<Comment> {
  const { data } = await api.patch<Envelope<Comment>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/comments/${commentId}`,
    body,
  );
  return data.data;
}

export async function deleteTaskComment(
  projectId: string,
  storyId: string,
  taskId: string,
  commentId: string,
): Promise<void> {
  await api.delete(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/comments/${commentId}`,
  );
}

// ─── Subtask Comment API ──────────────────────────────────────────────────────

export async function listSubtaskComments(
  projectId: string,
  storyId: string,
  taskId: string,
  subtaskId: string,
  page = 1,
  pageSize = 25,
): Promise<PaginatedResult<Comment>> {
  const { data } = await api.get<Envelope<Comment[]>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/subtasks/${subtaskId}/comments`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function createSubtaskComment(
  projectId: string,
  storyId: string,
  taskId: string,
  subtaskId: string,
  body: CommentCreatePayload,
): Promise<Comment> {
  const { data } = await api.post<Envelope<Comment>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/subtasks/${subtaskId}/comments`,
    body,
  );
  return data.data;
}

export async function updateSubtaskComment(
  projectId: string,
  storyId: string,
  taskId: string,
  subtaskId: string,
  commentId: string,
  body: CommentPatchPayload,
): Promise<Comment> {
  const { data } = await api.patch<Envelope<Comment>>(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/subtasks/${subtaskId}/comments/${commentId}`,
    body,
  );
  return data.data;
}

export async function deleteSubtaskComment(
  projectId: string,
  storyId: string,
  taskId: string,
  subtaskId: string,
  commentId: string,
): Promise<void> {
  await api.delete(
    `/projects/${projectId}/stories/${storyId}/tasks/${taskId}/subtasks/${subtaskId}/comments/${commentId}`,
  );
}

// ─── Epic Comment API ─────────────────────────────────────────────────────────

export async function listEpicComments(
  projectId: string,
  epicId: string,
  page = 1,
  pageSize = 25,
): Promise<PaginatedResult<Comment>> {
  const { data } = await api.get<Envelope<Comment[]>>(
    `/projects/${projectId}/epics/${epicId}/comments`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function createEpicComment(
  projectId: string,
  epicId: string,
  body: CommentCreatePayload,
): Promise<Comment> {
  const { data } = await api.post<Envelope<Comment>>(
    `/projects/${projectId}/epics/${epicId}/comments`,
    body,
  );
  return data.data;
}

export async function updateEpicComment(
  projectId: string,
  epicId: string,
  commentId: string,
  body: CommentPatchPayload,
): Promise<Comment> {
  const { data } = await api.patch<Envelope<Comment>>(
    `/projects/${projectId}/epics/${epicId}/comments/${commentId}`,
    body,
  );
  return data.data;
}

export async function deleteEpicComment(
  projectId: string,
  epicId: string,
  commentId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/epics/${epicId}/comments/${commentId}`);
}

// ─── Upload API ───────────────────────────────────────────────────────────────

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<Envelope<{ url: string }>>(
    "/upload/image",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data.data.url;
}

// ─── Notification Types ───────────────────────────────────────────────────────

export interface NotificationItem {
  id: string;
  user_id: string;
  event_type: string;
  title: string;
  body: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

// ─── Notification API ─────────────────────────────────────────────────────────

export async function fetchNotifications(
  page = 1,
  pageSize = 20,
): Promise<PaginatedResult<NotificationItem>> {
  const { data } = await api.get<Envelope<NotificationItem[]>>("/notifications/", {
    params: { page, pageSize },
  });
  return { items: data.data, pagination: data.pagination! };
}

export async function fetchUnreadCount(): Promise<number> {
  const { data } = await api.get<Envelope<{ unreadCount: number }>>(
    "/notifications/unread-count",
  );
  return data.data.unreadCount;
}

export async function markNotificationRead(
  notificationId: string,
): Promise<NotificationItem> {
  const { data } = await api.patch<Envelope<NotificationItem>>(
    `/notifications/${notificationId}/read`,
  );
  return data.data;
}

export async function markAllNotificationsRead(): Promise<number> {
  const { data } = await api.post<Envelope<{ updatedCount: number }>>(
    "/notifications/mark-all-read",
  );
  return data.data.updatedCount;
}

// ─── Activity Types ───────────────────────────────────────────────────────────

export interface ActivityLogOut {
  id: string;
  projectId: string;
  storyId: string | null;
  taskId: string | null;
  epicId: string | null;
  entityType: string;
  action: string;
  fieldName: string | null;
  oldValue: string | null;
  newValue: string | null;
  actorId: string;
  actorName: string;
  createdAt: string;
}

// ─── Activity API ─────────────────────────────────────────────────────────────

export async function listStoryActivity(
  projectId: string,
  storyId: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResult<ActivityLogOut>> {
  const { data } = await api.get<Envelope<ActivityLogOut[]>>(
    `/projects/${projectId}/stories/${storyId}/activity`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function listTaskActivity(
  projectId: string,
  taskId: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResult<ActivityLogOut>> {
  const { data } = await api.get<Envelope<ActivityLogOut[]>>(
    `/projects/${projectId}/tasks/${taskId}/activity`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function listEpicActivity(
  projectId: string,
  epicId: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResult<ActivityLogOut>> {
  const { data } = await api.get<Envelope<ActivityLogOut[]>>(
    `/projects/${projectId}/epics/${epicId}/activity`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function listProjectActivity(
  projectId: string,
  page = 1,
  pageSize = 20,
): Promise<PaginatedResult<ActivityLogOut>> {
  const { data } = await api.get<Envelope<ActivityLogOut[]>>(
    `/projects/${projectId}/activity`,
    { params: { page, pageSize } },
  );
  return { items: data.data, pagination: data.pagination! };
}

// ─── Trash API ────────────────────────────────────────────────────────────────

export async function listDeletedStories(
  projectId: string,
): Promise<PaginatedResult<Story>> {
  const { data } = await api.get<Envelope<Story[]>>(
    `/projects/${projectId}/trash`,
  );
  return { items: data.data, pagination: data.pagination! };
}

export async function restoreStory(
  projectId: string,
  storyId: string,
): Promise<Story> {
  const { data } = await api.post<Envelope<Story>>(
    `/projects/${projectId}/stories/${storyId}/restore`,
  );
  return data.data;
}

// ─── Backward-compat aliases (E4-S3) ─────────────────────────────────────────
// Our IssuesTable / TaskRows components were written with these names before
// the E4-S4 rename.  Keep them so we don't have to touch every import site.
export type Task = TaskOut;
export type Subtask = SubtaskOut;
export type TaskAssignee = { id: string; name: string };
export type TaskPatchBody = TaskPatchPayload;

export const patchTask = updateTask;
export const patchSubtask = updateSubtask;
