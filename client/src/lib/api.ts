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