"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import type { Priority, StoryStatus } from "@/lib/api";

export interface FilterState {
  priority: Priority[];
  epicId: string[];
  assigneeId: string[];
  search: string;
  status: StoryStatus[];
}

export type ArrayFilterKey = keyof Omit<FilterState, "search">;

/**
 * URL-synced filter state for Backlog, Board, and Table views.
 * All multi-value filters are stored as repeated search params:
 *   ?priority=high&priority=critical&assigneeId=uuid1
 * Search is a single string param: ?search=foo
 *
 * Switching Board ↔ Table preserves params because they live in the URL.
 */
export function useFilterBar() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const filters: FilterState = {
    priority: searchParams.getAll("priority") as Priority[],
    epicId: searchParams.getAll("epicId"),
    assigneeId: searchParams.getAll("assigneeId"),
    search: searchParams.get("search") ?? "",
    status: searchParams.getAll("status") as StoryStatus[],
  };

  /** Replace a multi-value filter with a new array of values. */
  const setFilter = useCallback(
    (key: ArrayFilterKey, values: string[]) => {
      const params = new URLSearchParams(searchParams.toString());
      params.delete(key);
      values.forEach((v) => params.append(key, v));
      params.delete("page"); // reset pagination on filter change
      router.replace(`${pathname}?${params.toString()}`);
    },
    [searchParams, router, pathname],
  );

  /** Update the debounced search string. Pass "" to clear. */
  const setSearch = useCallback(
    (value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set("search", value);
      } else {
        params.delete("search");
      }
      params.delete("page");
      router.replace(`${pathname}?${params.toString()}`);
    },
    [searchParams, router, pathname],
  );

  const resetFilters = useCallback(() => {
    router.replace(pathname);
  }, [router, pathname]);

  return { filters, setFilter, setSearch, resetFilters };
}
