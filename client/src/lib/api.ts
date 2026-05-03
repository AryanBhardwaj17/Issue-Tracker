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