import type { StoryStatus } from "@/lib/api";

const styles: Record<StoryStatus, string> = {
  backlog: "bg-gray-100 text-gray-600",
  todo: "bg-blue-100 text-blue-700",
  in_progress: "bg-indigo-100 text-indigo-700",
  in_review: "bg-purple-100 text-purple-700",
  testing: "bg-yellow-100 text-yellow-700",
  ready_for_prod: "bg-teal-100 text-teal-700",
  done: "bg-green-100 text-green-700",
};

const labels: Record<StoryStatus, string> = {
  backlog: "Backlog",
  todo: "Todo",
  in_progress: "In Progress",
  in_review: "In Review",
  testing: "Testing",
  ready_for_prod: "Ready for Prod",
  done: "Done",
};

export default function StatusBadge({ status }: { status: StoryStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {labels[status]}
    </span>
  );
}
