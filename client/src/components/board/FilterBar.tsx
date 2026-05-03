"use client";

import { useRef, useState } from "react";
import { useDebounce } from "@/hooks/useDebounce";
import type { MemberOut, Epic } from "@/lib/api";

// ── Typeahead ─────────────────────────────────────────────────────────────────

interface TypeaheadOption {
  id: string;
  label: string;
}

interface TypeaheadProps {
  placeholder: string;
  options: TypeaheadOption[];
  selected: TypeaheadOption | null;
  onSelect: (opt: TypeaheadOption | null) => void;
}

function Typeahead({ placeholder, options, selected, onSelect }: TypeaheadProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 200);
  const containerRef = useRef<HTMLDivElement>(null);

  const filtered = debouncedQuery
    ? options.filter((o) =>
        o.label.toLowerCase().includes(debouncedQuery.toLowerCase()),
      )
    : options;

  function handleSelect(opt: TypeaheadOption) {
    onSelect(opt);
    setQuery("");
    setOpen(false);
  }

  function handleClear() {
    onSelect(null);
    setQuery("");
  }

  return (
    <div ref={containerRef} className="relative">
      {selected ? (
        <div className="flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-2.5 py-1.5 text-xs">
          <span className="text-gray-800">{selected.label}</span>
          <button
            type="button"
            onClick={handleClear}
            className="ml-1 text-gray-400 hover:text-gray-600"
            aria-label="Clear filter"
          >
            ✕
          </button>
        </div>
      ) : (
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            placeholder={placeholder}
            className="w-36 rounded-lg border border-gray-300 px-2.5 py-1.5 text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400"
          />
          {open && filtered.length > 0 && (
            <ul className="absolute left-0 top-full z-20 mt-1 max-h-48 w-44 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
              {filtered.map((opt) => (
                <li key={opt.id}>
                  <button
                    type="button"
                    className="w-full px-3 py-2 text-left text-xs text-gray-700 hover:bg-gray-50"
                    onMouseDown={() => handleSelect(opt)}
                  >
                    {opt.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ── Multi-select chips ─────────────────────────────────────────────────────────

interface ChipSelectProps {
  label: string;
  options: { value: string; label: string }[];
  selected: string[];
  onChange: (values: string[]) => void;
}

function ChipSelect({ label, options, selected, onChange }: ChipSelectProps) {
  const [open, setOpen] = useState(false);

  function toggle(value: string) {
    onChange(
      selected.includes(value)
        ? selected.filter((v) => v !== value)
        : [...selected, value],
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        className={`flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs transition-colors ${
          selected.length > 0
            ? "border-gray-700 bg-gray-900 text-white"
            : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
        }`}
      >
        {label}
        {selected.length > 0 && (
          <span className="rounded-full bg-white/20 px-1 text-white">
            {selected.length}
          </span>
        )}
        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <ul className="absolute left-0 top-full z-20 mt-1 w-44 rounded-lg border border-gray-200 bg-white shadow-lg">
          {options.map((opt) => (
            <li key={opt.value}>
              <button
                type="button"
                onMouseDown={() => toggle(opt.value)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-gray-700 hover:bg-gray-50"
              >
                <span
                  className={`h-3.5 w-3.5 rounded border transition-colors ${
                    selected.includes(opt.value)
                      ? "border-gray-900 bg-gray-900"
                      : "border-gray-300"
                  }`}
                />
                {opt.label}
              </button>
            </li>
          ))}
          {selected.length > 0 && (
            <li className="border-t border-gray-100">
              <button
                type="button"
                onMouseDown={() => onChange([])}
                className="w-full px-3 py-2 text-left text-xs text-gray-400 hover:bg-gray-50"
              >
                Clear all
              </button>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

// ── FilterBar ─────────────────────────────────────────────────────────────────

export type BoardFilters = {
  search: string;
  assigneeId: string | null;
  assigneeName: string | null;
  epicId: string | null;
  epicName: string | null;
  priority: string[];
  status: string[];
};

interface FilterBarProps {
  filters: BoardFilters;
  onFiltersChange: (f: BoardFilters) => void;
  members: MemberOut[];
  epics: Epic[];
  onCreateStory: () => void;
}

const PRIORITY_OPTIONS = [
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const STATUS_OPTIONS = [
  { value: "todo", label: "To Do" },
  { value: "in_progress", label: "In Progress" },
  { value: "in_review", label: "In Review" },
  { value: "testing", label: "Testing" },
  { value: "ready_for_prod", label: "Ready for Prod" },
  { value: "done", label: "Done" },
];

export default function FilterBar({
  filters,
  onFiltersChange,
  members,
  epics,
  onCreateStory,
}: FilterBarProps) {
  const [searchInput, setSearchInput] = useState(filters.search);
  const debouncedSearch = useDebounce(searchInput, 300);

  // Sync debounced search into filters
  const prevDebounced = useRef(debouncedSearch);
  if (prevDebounced.current !== debouncedSearch) {
    prevDebounced.current = debouncedSearch;
    onFiltersChange({ ...filters, search: debouncedSearch });
  }

  const memberOptions: TypeaheadOption[] = members.map((m) => ({
    id: m.userId,
    label: m.name,
  }));

  const epicOptions: TypeaheadOption[] = [
    { id: "none", label: "No Epic" },
    ...epics.map((e) => ({ id: e.id, label: e.name })),
  ];

  const selectedAssignee =
    filters.assigneeId
      ? { id: filters.assigneeId, label: filters.assigneeName ?? "" }
      : null;

  const selectedEpic =
    filters.epicId
      ? { id: filters.epicId, label: filters.epicName ?? "" }
      : null;

  const hasActiveFilters =
    !!filters.search ||
    !!filters.assigneeId ||
    !!filters.epicId ||
    filters.priority.length > 0 ||
    filters.status.length > 0;

  function clearAll() {
    setSearchInput("");
    onFiltersChange({
      search: "",
      assigneeId: null,
      assigneeName: null,
      epicId: null,
      epicName: null,
      priority: [],
      status: [],
    });
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {/* Search */}
      <input
        type="text"
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        placeholder="Search stories…"
        className="w-48 rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400"
      />

      {/* Assignee typeahead */}
      <Typeahead
        placeholder="Assignee…"
        options={memberOptions}
        selected={selectedAssignee}
        onSelect={(opt) =>
          onFiltersChange({
            ...filters,
            assigneeId: opt?.id ?? null,
            assigneeName: opt?.label ?? null,
          })
        }
      />

      {/* Epic typeahead */}
      <Typeahead
        placeholder="Epic…"
        options={epicOptions}
        selected={selectedEpic}
        onSelect={(opt) =>
          onFiltersChange({
            ...filters,
            epicId: opt?.id ?? null,
            epicName: opt?.label ?? null,
          })
        }
      />

      {/* Priority multi-select */}
      <ChipSelect
        label="Priority"
        options={PRIORITY_OPTIONS}
        selected={filters.priority}
        onChange={(v) => onFiltersChange({ ...filters, priority: v })}
      />

      {/* Status multi-select */}
      <ChipSelect
        label="Status"
        options={STATUS_OPTIONS}
        selected={filters.status}
        onChange={(v) => onFiltersChange({ ...filters, status: v })}
      />

      {/* Clear all */}
      {hasActiveFilters && (
        <button
          type="button"
          onClick={clearAll}
          className="rounded-lg px-2.5 py-1.5 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700"
        >
          Clear all
        </button>
      )}

      {/* Spacer + create button */}
      <div className="ml-auto">
        <button
          type="button"
          onClick={onCreateStory}
          className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800"
        >
          + Create Story
        </button>
      </div>
    </div>
  );
}
