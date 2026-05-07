import { Suspense } from "react";
import TrashPage from "@/components/projects/TrashPage";

export default async function TrashRoute({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <Suspense>
      <TrashPage projectId={projectId} />
    </Suspense>
  );
}
