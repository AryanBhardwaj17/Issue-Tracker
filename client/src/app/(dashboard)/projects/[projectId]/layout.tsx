import { ReactNode } from "react";

/**
 * Layout boundary for all project-scoped pages.
 * Sidebar project navigation is rendered by the parent dashboard layout
 * (which reads the projectId from usePathname).
 * This file exists as a Next.js layout boundary for future use
 * (e.g. project-level context providers, error boundaries).
 */
export default function ProjectLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
