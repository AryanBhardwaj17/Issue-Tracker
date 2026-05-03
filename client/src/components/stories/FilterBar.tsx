"use client";

import { useEffect, useRef, useState } from "react";
import { useProjectMembers } from "@/hooks/useProject";
import { useAllEpics } from "@/hooks/useStories";
import type { ArrayFilterKey, FilterState } from "@/hooks/useFilterBar";

// ─── MultiSelect ──────────────────────────────────────────────────────────────

interface Option {
  value: string;
  label: string;
}

interface MultiSelectProps {
  label: string;
  options: Option[];
  selected: string[];
  onChange: (values: string[]) => void;
}

function MultiSelect({ label, options, selected, onChange }: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function toggle(value: string) {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  }

  const hasSelection = selected.length > 0;
  const buttonLabel = hasSelection ? `${label} (${selected.length})` : label;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1 ${
          hasSelection
            ? "border-gray-900 bg-gray-900 text-white"
            : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
        }`}
      >
        {buttonLabel}
        <svg
          className="h-3.5 w-3.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 min-w-[160px] rounded-xl border border-gray-200 bg-white py-1 shadow-lg">
          {options.map((opt) => (
            <label
              key={opt.value}
              className="flex cursor-pointer items-center gap-2.5 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <input
                type="checkbox"
                checked={selected.includes(opt.value)}
                onChange={() => toggle(opt.value)}
                className="h-3.5 w-3.5 rounded border-gray-300 accent-gray-900"
              />
              {opt.label}
            </label>
          ))}
          {options.length === 0 && (
            <p className="px-3 py-2 text-xs text-gray-400">No options</p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── FilterBar ────────────────────────────────────────────────────────────────

const PRIORITY_OPTIONS: Option[] = [
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

interface FilterBarProps {
  projectId: string;
  filters: FilterState;
  onFilterChange: (key: ArrayFilterKey, values: string[]) => void;
  /** Keys to exclude from the rendered filter controls. */
  omit?: ArrayFilterKey[];
}

export default function FilterBar({
  projectId,
  filters,
  onFilterChange,
  omit = [],
}: FilterBarProps) {
  const { data: membersData } = useProjectMembers(projectId);
  const { data: epicsData } = useAllEpics(projectId);

  const memberOptions: Option[] = (membersData ?? []).map((m) => ({
    value: m.userId,
    label: m.name,
  }));

  const epicOptions: Option[] = [
    { value: "none", label: "No Epic" },
    ...(epicsData?.items ?? []).map((e) => ({ value: e.id, label: e.name })),
  ];

  const hasActiveFilters =
    filters.priority.length > 0 ||
    filters.assigneeId.length > 0 ||
    (!omit.includes("epicId") && filters.epicId.length > 0);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {!omit.includes("priority") && (
        <MultiSelect
          label="Priority"
          options={PRIORITY_OPTIONS}
          selected={filters.priority}
          onChange={(vals) => onFilterChange("priority", vals)}
        />
      )}

      {!omit.includes("assigneeId") && (
        <MultiSelect
          label="Assignee"
          options={memberOptions}
          selected={filters.assigneeId}
          onChange={(vals) => onFilterChange("assigneeId", vals)}
        />
      )}

      {!omit.includes("epicId") && (
        <MultiSelect
          label="Epic"
          options={epicOptions}
          selected={filters.epicId}
          onChange={(vals) => onFilterChange("epicId", vals)}
        />
      )}

      {hasActiveFilters && (
        <button
          type="button"
          onClick={() => {
            onFilterChange("priority", []);
            onFilterChange("assigneeId", []);
            if (!omit.includes("epicId")) onFilterChange("epicId", []);
          }}
          className="text-xs text-gray-500 underline hover:text-gray-900"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
