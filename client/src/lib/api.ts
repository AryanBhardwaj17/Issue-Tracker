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

// ─── Project Types ───────────────────────────────────────────────────────────

export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface Envelope<T> {
  success: boolean;
  message?: string;
  data: T;
  pagination?: Pagination;
}

export interface OwnerOut {
  id: string;
  name: string;
}

export interface ProjectOut {
  id: string;
  name: string;
  key: string;
  description: string | null;
  owner: OwnerOut;
  role: "owner" | "member";
  memberCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
  key: string;
  description: string | null;
  role: "owner" | "member";
  memberCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectMember {
  id: string;
  userId: string;
  name: string;
  role: "owner" | "member";
  joinedAt: string;
}

// ─── Project API ─────────────────────────────────────────────────────────────

export async function getProject(projectId: string): Promise<ProjectOut> {
  const { data } = await api.get<Envelope<ProjectOut>>(`/core/projects/${projectId}`);
  return data.data;
}

export async function updateProject(
  projectId: string,
  body: { name?: string; description?: string },
): Promise<ProjectOut> {
  const { data } = await api.patch<Envelope<ProjectOut>>(`/core/projects/${projectId}`, body);
  return data.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/core/projects/${projectId}`);
}

// ─── Members API (mocked until backend ready) ────────────────────────────────

const MOCK_MEMBERS = true;

const MOCK_MEMBERS_DATA: ProjectMember[] = [
  { id: "m1", userId: "u1", name: "Alice Johnson", role: "owner", joinedAt: "2025-12-01T10:00:00Z" },
  { id: "m2", userId: "u2", name: "Bob Smith", role: "member", joinedAt: "2026-01-15T08:30:00Z" },
  { id: "m3", userId: "u3", name: "Carol White", role: "member", joinedAt: "2026-02-20T14:00:00Z" },
];

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function listMembers(
  projectId: string,
  page = 1,
  pageSize = 10,
): Promise<{ data: ProjectMember[]; pagination: Pagination }> {
  if (MOCK_MEMBERS) {
    await delay(300);
    return {
      data: MOCK_MEMBERS_DATA,
      pagination: { page, pageSize, total: MOCK_MEMBERS_DATA.length, totalPages: 1 },
    };
  }
  const { data } = await api.get<Envelope<ProjectMember[]>>(
    `/core/projects/${projectId}/members?page=${page}&pageSize=${pageSize}`,
  );
  return { data: data.data, pagination: data.pagination! };
}

export async function addMember(
  projectId: string,
  email: string,
): Promise<ProjectMember> {
  if (MOCK_MEMBERS) {
    await delay(400);
    if (email === "notfound@test.com") throw { response: { status: 404, data: { message: "No user with that email" } } };
    if (email === "existing@test.com") throw { response: { status: 409, data: { message: "Already a member" } } };
    const newMember: ProjectMember = {
      id: `m${Date.now()}`,
      userId: `u${Date.now()}`,
      name: email.split("@")[0],
      role: "member",
      joinedAt: new Date().toISOString(),
    };
    MOCK_MEMBERS_DATA.push(newMember);
    return newMember;
  }
  const { data } = await api.post<Envelope<ProjectMember>>(
    `/core/projects/${projectId}/members`,
    { email },
  );
  return data.data;
}

export async function transferOwnership(
  projectId: string,
  newOwnerId: string,
): Promise<void> {
  if (MOCK_MEMBERS) {
    await delay(400);
    return;
  }
  await api.patch(`/core/projects/${projectId}/transfer-ownership`, { newOwnerId });
}
 
 