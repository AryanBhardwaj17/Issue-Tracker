"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { Story } from "@/lib/api";

// ── Helpers ───────────────────────────────────────────────────────────────────

const PRIORITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-gray-100 text-gray-600 border-gray-200",
};

const PRIORITY_LABELS: Record<string, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

function isOverdue(dueDate: string | null): boolean {
  if (!dueDate) return false;
  return new Date(dueDate) < new Date(new Date().toDateString());
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// ── canDrag predicate ─────────────────────────────────────────────────────────
// Draggable if: no assignee, OR caller is the assignee, OR caller is owner.
export function canDragStory(
  story: Story,
  currentUserId: string,
  role: "owner" | "member",
): boolean {
  if (!story.assignee) return true;
  if (role === "owner") return true;
  return story.assignee.id === currentUserId;
}

// ── StoryCard ─────────────────────────────────────────────────────────────────

interface StoryCardProps {
  story: Story;
  currentUserId: string;
  role: "owner" | "member";
}

export default function StoryCard({ story, currentUserId, role }: StoryCardProps) {
  const draggable = canDragStory(story, currentUserId, role);

  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: story.id,
      data: { story },
      disabled: !draggable,
    });

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  const overdue = isOverdue(story.dueDate);

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...(draggable ? { ...attributes, ...listeners } : {})}
      className={[
        "rounded-lg border border-gray-200 bg-white p-3 shadow-sm select-none",
        draggable ? "cursor-grab active:cursor-grabbing hover:shadow-md" : "cursor-not-allowed opacity-50",
        isDragging ? "opacity-30 shadow-lg ring-2 ring-gray-300" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* Title */}
      <p className="mb-2 text-xs font-medium leading-snug text-gray-900 line-clamp-2">
        {story.title}
      </p>

      {/* Priority badge */}
      <div className="mb-2 flex flex-wrap items-center gap-1.5">
        <span
          className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold ${PRIORITY_STYLES[story.priority] ?? PRIORITY_STYLES.low}`}
        >
          {PRIORITY_LABELS[story.priority] ?? story.priority}
        </span>

        {story.storyPoints !== null && (
          <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-gray-100 text-[10px] font-semibold text-gray-600">
            {story.storyPoints}
          </span>
        )}
      </div>

      {/* Footer: assignee avatar + due date */}
      <div className="flex items-center justify-between">
        {story.assignee ? (
          <div
            className="flex h-5 w-5 items-center justify-center rounded-full bg-gray-800 text-[9px] font-bold text-white"
            title={story.assignee.name}
          >
            {initials(story.assignee.name)}
          </div>
        ) : (
          <div className="h-5 w-5" />
        )}

        {story.dueDate && (
          <span
            className={`text-[10px] ${overdue ? "font-semibold text-red-600" : "text-gray-400"}`}
          >
            {overdue ? "⚠ " : ""}
            {new Date(story.dueDate).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </span>
        )}
      </div>

      {/* Story key */}
      <p className="mt-1.5 text-[10px] text-gray-400">{story.storyKey}</p>
    </div>
  );
}
