import { create } from "zustand";
import {
  registerUser,
  loginUser,
  type User,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isHydrated: boolean;
  error: string | null;

  register: (name: string, email: string, password: string) => Promise<boolean>;
  login: (email: string, password: string) => Promise<Boolean>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isHydrated: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await loginUser({ email, password });
      sessionStorage.setItem("access_token", data.access_token);
      sessionStorage.setItem("user", JSON.stringify(data.user));
      set({ user: data.user, isLoading: false });
      return true;
    } catch (error: unknown) {
      set({ isLoading: false, error: extractErrorMessage(error, "Invalid credentials") });
      return false;
    }
  },

  register: async (name, email, password) => {
    set({ isLoading: true, error: null });
    try {
      await registerUser({ name, email, password });
      set({ isLoading: false });
      return true;
    } catch (error: unknown) {
      set({ isLoading: false, error: extractErrorMessage(error, "Registration failed") });
      return false;
    }
  },


  logout: async () => {
    try {
      await logoutUser();
    } catch {
      // Proceed even if server logout fails
    } finally {
      sessionStorage.removeItem("access_token");
      set({ user: null, error: null });
    }
  },

  hydrate: async () => {
    const token = sessionStorage.getItem("access_token");
    const userRaw = sessionStorage.getItem("user");
    if (!token || !userRaw) {
      set({ isHydrated: true });
      return;
    }
    try {
      const user: User = JSON.parse(userRaw);
      set({ user, isHydrated: true });
    } catch {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("user");
      set({ isHydrated: true });
    }
  },

  clearError: () => set({ error: null }),
}));
