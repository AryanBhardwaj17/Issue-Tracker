import { Suspense } from "react";
import ProjectActivityFeed from "@/components/projects/ProjectActivityFeed";

export default async function ActivityPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <Suspense>
      <ProjectActivityFeed projectId={projectId} />
    </Suspense>
  );
}
