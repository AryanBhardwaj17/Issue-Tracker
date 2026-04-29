"use client";

import { use } from "react";
import Link from "next/link";
import { useProject } from "@/hooks/useProjects";
import Button from "@/components/ui/Button";

export default function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const { data: project, isLoading, isError } = useProject(projectId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-900" />
      </div>
    );
  }

  if (isError || !project) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-sm text-gray-600">Project not found.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            {project.name}
          </h1>
          <p className="mt-1 text-sm text-gray-500">{project.key}</p>
        </div>
        <Link href={`/projects/${projectId}/settings`}>
          <Button variant="secondary">⚙ Settings</Button>
        </Link>
      </div>
    </div>
  );
}
