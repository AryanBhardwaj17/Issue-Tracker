"use client";

import { use, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = use(params);
  const router = useRouter();

  useEffect(() => {
    router.replace(`/projects/${projectId}/backlog`);
  }, [projectId, router]);

  return null;
}
