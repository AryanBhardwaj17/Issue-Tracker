import { create } from "zustand";
import {
  registerUser,
  type User,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isHydrated: boolean;
  error: string | null;

  register: (name: string, email: string, password: string) => Promise<boolean>;
  hydrate: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isHydrated: false,
  error: null,



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


  hydrate: async () => {
    const token = sessionStorage.getItem("access_token");
    if (!token) {
      set({ isHydrated: true });
      return;
    }

  },

  clearError: () => set({ error: null }),
}));
