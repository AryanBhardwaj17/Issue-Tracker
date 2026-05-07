import { Suspense } from "react";
import EpicDetailPage from "@/components/stories/EpicDetailPage";

export default function EpicDetailRoute() {
  return (
    <Suspense>
      <EpicDetailPage />
    </Suspense>
  );
}
