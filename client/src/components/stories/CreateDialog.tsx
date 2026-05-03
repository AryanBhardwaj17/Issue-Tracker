"use client";

import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateEpic } from "@/hooks/useEpics";
import { useAllEpics, useCreateStory } from "@/hooks/useStories";
import { useProjectMembers } from "@/hooks/useProject";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import type { StoryStatus } from "@/lib/api";

// ─── Constants ────────────────────────────────────────────────────────────────

const FIBONACCI = [1, 2, 3, 5, 8, 13, 21] as const;

const SELECT_CLASS =
  "w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 transition-colors hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1";

const TEXTAREA_CLASS =
  "w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1";

// ─── Story form schema (react-hook-form + zod) ────────────────────────────────

const storySchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .max(500, "Max 500 characters")
    .refine((v) => v.trim().length > 0, "Title must not be blank"),
  description: z.string().max(10_000, "Max 10,000 characters").optional(),
  priority: z.enum(["low", "medium", "high", "critical"]),
  storyPoints: z.string().optional(),
  epicId: z.string().optional(),
  assigneeId: z.string().optional(),
  dueDate: z.string().optional(),
});

type StoryFormData = z.infer<typeof storySchema>;

// ─── Epic tab (simple controlled form — same pattern as epics page) ───────────

function EpicTab({
  projectId,
  onClose,
}: {
  projectId: string;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const createEpic = useCreateEpic(projectId);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    createEpic.mutate(
      { name: name.trim(), description: description.trim() || null },
      { onSuccess: onClose },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Epic name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="e.g. Checkout flow"
        required
        autoFocus
      />
      <div>
        <label className="mb-1.5 block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description"
          rows={3}
          className={TEXTAREA_CLASS}
        />
      </div>
      <div className="flex justify-end gap-2 pt-1">
        <Button
          type="button"
          variant="secondary"
          onClick={onClose}
          disabled={createEpic.isPending}
        >
          Cancel
        </Button>
        <Button type="submit" isLoading={createEpic.isPending}>
          Create Epic
        </Button>
      </div>
    </form>
  );
}

// ─── Story tab (react-hook-form) ──────────────────────────────────────────────

function StoryTab({
  projectId,
  defaultStatus,
  onClose,
}: {
  projectId: string;
  defaultStatus: StoryStatus;
  onClose: () => void;
}) {
  const createStory = useCreateStory(projectId);
  const { data: epicsData } = useAllEpics(projectId);
  const { data: membersData } = useProjectMembers(projectId);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<StoryFormData>({
    resolver: zodResolver(storySchema),
    defaultValues: { priority: "medium" },
  });

  function onSubmit(data: StoryFormData) {
    createStory.mutate(
      {
        title: data.title.trim(),
        description: data.description?.trim() || null,
        priority: data.priority,
        storyPoints: data.storyPoints ? Number(data.storyPoints) : null,
        epicId: data.epicId || null,
        assigneeId: data.assigneeId || null,
        dueDate: data.dueDate || null,
        status: defaultStatus,
      },
      { onSuccess: onClose },
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Title */}
      <Input
        label="Title"
        placeholder="e.g. User can reset password"
        error={errors.title?.message}
        autoFocus
        {...register("title")}
      />

      {/* Description */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          {...register("description")}
          placeholder="Optional description (markdown supported)"
          rows={3}
          className={TEXTAREA_CLASS}
        />
        {errors.description && (
          <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>
        )}
      </div>

      {/* Priority + Story Points */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-700">
            Priority <span className="text-red-500">*</span>
          </label>
          <select {...register("priority")} className={SELECT_CLASS}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          {errors.priority && (
            <p className="mt-1 text-xs text-red-600">{errors.priority.message}</p>
          )}
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-700">
            Story Points
          </label>
          <select {...register("storyPoints")} className={SELECT_CLASS}>
            <option value="">—</option>
            {FIBONACCI.map((n) => (
              <option key={n} value={String(n)}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Epic + Assignee */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-700">
            Epic
          </label>
          <select {...register("epicId")} className={SELECT_CLASS}>
            <option value="">No Epic</option>
            {(epicsData?.items ?? []).map((e) => (
              <option key={e.id} value={e.id}>
                {e.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-700">
            Assignee
          </label>
          <select {...register("assigneeId")} className={SELECT_CLASS}>
            <option value="">Unassigned</option>
            {(membersData ?? []).map((m) => (
              <option key={m.userId} value={m.userId}>
                {m.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Due Date */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-gray-700">
          Due Date
        </label>
        <input type="date" {...register("dueDate")} className={SELECT_CLASS} />
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <Button
          type="button"
          variant="secondary"
          onClick={onClose}
          disabled={createStory.isPending}
        >
          Cancel
        </Button>
        <Button type="submit" isLoading={createStory.isPending}>
          Create Story
        </Button>
      </div>
    </form>
  );
}

// ─── Dialog wrapper ───────────────────────────────────────────────────────────

interface CreateDialogProps {
  projectId: string;
  /** Status assigned to newly created stories. "backlog" from Backlog page, "todo" from Board. */
  defaultStatus?: StoryStatus;
  /** Which tab to open first. */
  defaultTab?: "epic" | "story";
  onClose: () => void;
}

export default function CreateDialog({
  projectId,
  defaultStatus = "backlog",
  defaultTab = "story",
  onClose,
}: CreateDialogProps) {
  const [tab, setTab] = useState<"epic" | "story">(defaultTab);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  function handleOverlayClick(e: React.MouseEvent) {
    // Only close when clicking the backdrop itself, not the modal card
    if (e.target === overlayRef.current) onClose();
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
        {/* Header — tab toggle + close button */}
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <div className="flex gap-0.5 rounded-lg border border-gray-200 bg-gray-50 p-0.5">
            {(["story", "epic"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors ${
                  tab === t
                    ? "bg-gray-900 text-white shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {t === "story" ? "User Story" : "Epic"}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
            aria-label="Close dialog"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          {tab === "story" ? (
            <StoryTab
              projectId={projectId}
              defaultStatus={defaultStatus}
              onClose={onClose}
            />
          ) : (
            <EpicTab projectId={projectId} onClose={onClose} />
          )}
        </div>
      </div>
    </div>
  );
}
