"use client";

import { ReactNode, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/authStore";
import { getProject } from "@/lib/api";
import { useTrash } from "@/hooks/useTrash";
import Navbar from "@/components/dashboard/Navbar";

// Project-scoped nav links shown in the sidebar when inside a project
const PROJECT_NAV = [
  { label: "Board", slug: "board" },
  { label: "Backlog", slug: "backlog" },
  { label: "Issues", slug: "issues" },
  { label: "Epics", slug: "epics" },
  { label: "Settings", slug: "settings" },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, hydrate, isHydrated } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (isHydrated && !user) {
      router.replace("/login");
    }
  }, [isHydrated, user, router]);

  // Extract projectId from the URL when inside /projects/[projectId]/*
  const projectMatch = pathname.match(/^\/projects\/([^/]+)/);
  const sidebarProjectId = projectMatch?.[1] ?? null;

  // Fetch project for sidebar name + key — reuses the cache that project pages
  // already populate, so this rarely causes a network request.
  const { data: sidebarProject } = useQuery({
    queryKey: ["project", sidebarProjectId],
    queryFn: () => getProject(sidebarProjectId!),
    enabled: !!sidebarProjectId,
    staleTime: 30_000,
  });

  const { data: trashData } = useTrash(sidebarProjectId ?? "");
  const trashCount = trashData?.pagination?.total ?? 0;

  if (!isHydrated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
      </div>
    );
  }

  function isNavActive(href: string) {
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-gray-200 bg-white md:flex md:flex-col">
        {/* Logo / home link */}
        <div className="border-b border-gray-100 px-5 py-4">
          <Link
            href="/projects"
            className="text-base font-semibold text-gray-900 hover:text-gray-700"
          >
            Issue Tracker
          </Link>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
          {sidebarProjectId && sidebarProject ? (
            <>
              {/* Back to projects list */}
              <Link
                href="/projects"
                className="mb-1 flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900"
              >
                <svg
                  className="h-3.5 w-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                All projects
              </Link>

              {/* Project identity */}
              <div className="mb-2 px-3 py-1">
                <p className="truncate text-sm font-semibold text-gray-900">
                  {sidebarProject.name}
                </p>
                <span className="mt-0.5 inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                  {sidebarProject.key}
                </span>
              </div>

              <div className="my-1 border-t border-gray-100" />

              {/* Project nav links */}
              {PROJECT_NAV.map(({ label, slug }) => {
                const href = `/projects/${sidebarProjectId}/${slug}`;
                const active = isNavActive(href);
                return (
                  <Link
                    key={slug}
                    href={href}
                    className={`flex items-center rounded-lg px-3 py-2 text-sm transition-colors ${
                      active
                        ? "bg-gray-100 font-medium text-gray-900"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}

              {/* Divider before secondary links */}
              <div className="my-1 border-t border-gray-100" />

              {/* Activity */}
              {(() => {
                const href = `/projects/${sidebarProjectId}/activity`;
                const active = isNavActive(href);
                return (
                  <Link
                    href={href}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                      active
                        ? "bg-gray-100 font-medium text-gray-900"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                  >
                    <svg
                      className="h-4 w-4 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    Activity
                  </Link>
                );
              })()}

              {/* Trash — badge hidden when count is 0 */}
              {(() => {
                const href = `/projects/${sidebarProjectId}/trash`;
                const active = isNavActive(href);
                return (
                  <Link
                    href={href}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                      active
                        ? "bg-gray-100 font-medium text-gray-900"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                  >
                    <svg
                      className="h-4 w-4 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                    Trash
                    {trashCount > 0 && (
                      <span className="ml-auto text-xs text-gray-400">
                        {trashCount}
                      </span>
                    )}
                  </Link>
                );
              })()}
            </>
          ) : (
            /* Default sidebar when not inside a project */
            <Link
              href="/projects"
              className={`flex items-center rounded-lg px-3 py-2 text-sm transition-colors ${
                isNavActive("/projects")
                  ? "bg-gray-100 font-medium text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              Projects
            </Link>
          )}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}