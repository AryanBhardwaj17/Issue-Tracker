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

// ─── Story Types ──────────────────────────────────────────────────────────────

export interface UserRef {
  id: string;
  name: string;
}

export interface Story {
  id: string;
  storyKey: string;
  title: string;
  description: string | null;
  epicId: string | null;
  status: string;
  priority: string;
  storyPoints: number | null;
  assignee: UserRef | null;
  reporter: UserRef;
  dueDate: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface StoryCreatePayload {
  title: string;
  description?: string | null;
  epicId?: string | null;
  status?: string;
  priority: string;
  storyPoints?: number | null;
  assigneeId?: string | null;
  dueDate?: string | null;
}

export interface StoryPatchPayload {
  title?: string;
  description?: string | null;
  epicId?: string | null;
  status?: string;
  priority?: string;
  storyPoints?: number | null;
  assigneeId?: string | null;
  dueDate?: string | null;
}

// ─── Story API ────────────────────────────────────────────────────────────────

export async function listStories(
  projectId: string,
  page = 1,
  pageSize = 25,
  filters?: { status?: string; priority?: string; epicId?: string; assigneeId?: string },
): Promise<PaginatedResult<Story>> {
  const { data } = await api.get<Envelope<Story[]>>(
    `/projects/${projectId}/stories`,
    { params: { page, pageSize, ...filters } },
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
  body: StoryCreatePayload,
): Promise<Story> {
  const { data } = await api.post<Envelope<Story>>(
    `/projects/${projectId}/stories`,
    body,
  );
  return data.data;
}

export async function updateStory(
  projectId: string,
  storyId: string,
  body: StoryPatchPayload,
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

// ─── Task Types ───────────────────────────────────────────────────────────────

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
): Promise<TaskOut | SubtaskOut> {
  const { data } = await api.patch<Envelope<TaskOut | SubtaskOut>>(
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

// ─── Comment Types ────────────────────────────────────────────────────────────

export interface CommentAuthor {
  id: string;
  name: string;
}

export interface Comment {
  id: string;
  userStoryId: string;
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

// ─── Upload API ───────────────────────────────────────────────────────────────

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<Envelope<{ url: string }>>(
    `/upload/image`,
    formData,
    { headers: { "Content-Type": undefined } },
  );
  return data.data.url;
}