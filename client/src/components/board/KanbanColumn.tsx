"use client";

import { useDroppable } from "@dnd-kit/core";
import StoryCard from "./StoryCard";
import type { Story } from "@/lib/api";

interface KanbanColumnProps {
  id: string;
  label: string;
  stories: Story[];
  currentUserId: string;
  role: "owner" | "member";
}

export default function KanbanColumn({
  id,
  label,
  stories,
  currentUserId,
  role,
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div className="flex w-64 shrink-0 flex-col">
      {/* Column header */}
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          {label}
        </span>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-500">
          {stories.length}
        </span>
      </div>

      {/* Drop zone */}
      <div
        ref={setNodeRef}
        className={[
          "min-h-24 flex-1 space-y-2 rounded-xl p-2 transition-colors",
          isOver ? "bg-gray-100 ring-2 ring-gray-300" : "bg-gray-50",
        ].join(" ")}
      >
        {stories.map((story) => (
          <StoryCard
            key={story.id}
            story={story}
            currentUserId={currentUserId}
            role={role}
          />
        ))}

        {stories.length === 0 && (
          <div className="flex h-16 items-center justify-center rounded-lg border border-dashed border-gray-300">
            <span className="text-[11px] text-gray-400">Drop here</span>
          </div>
        )}
      </div>
    </div>
  );
}
