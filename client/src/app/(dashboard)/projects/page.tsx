"use client";

import { useState } from "react";
import { useProjects } from "@/hooks/useProjects";
import ProjectCard from "@/components/projects/ProjectCard";
import CreateProjectModal from "@/components/projects/CreateProjectModal";
import Pagination from "@/components/projects/Pagination";
import Button from "@/components/ui/Button";

export default function ProjectsPage() {
  const [page, setPage] = useState(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data, isLoading, isError, refetch } = useProjects(page);

  const items = data?.items ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Your Projects
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and organize your work
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>+ Create New Project</Button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex flex-col items-center justify-center py-20">
          <p className="mb-4 text-sm text-gray-600">
            Failed to load projects.
          </p>
          <Button variant="secondary" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && items.length === 0 && page === 1 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 py-16">
          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-gray-200 text-2xl">
            📂
          </div>
          <h2 className="mb-1 text-base font-semibold text-gray-900">
            No projects yet
          </h2>
          <p className="mb-4 max-w-xs text-center text-xs text-gray-500">
            Get started by creating your first project to track issues and
            manage your team&apos;s work
          </p>
          <Button onClick={() => setIsModalOpen(true)}>
            + Create New Project
          </Button>
        </div>
      )}

      {/* Project grid */}
      {!isLoading && !isError && items.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>

          {pagination && (
            <Pagination
              page={pagination.page}
              totalPages={pagination.totalPages}
              onPageChange={setPage}
            />
          )}
        </>
      )}

      {/* Create modal */}
      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}