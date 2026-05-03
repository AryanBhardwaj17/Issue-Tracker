"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";

type View = "board" | "issues";

/**
 * Board ↔ Table toggle shown at the top of the issues/board pages.
 * Preserves all current search params when switching routes.
 */
export default function ViewToggle({ active }: { active: View }) {
  const { projectId } = useParams<{ projectId: string }>();
  const searchParams = useSearchParams();

  const qs = searchParams.toString();
  const suffix = qs ? `?${qs}` : "";

  const links: { view: View; label: string; href: string }[] = [
    { view: "board", label: "Board", href: `/projects/${projectId}/board${suffix}` },
    { view: "issues", label: "Table", href: `/projects/${projectId}/issues${suffix}` },
  ];

  return (
    <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
      {links.map(({ view, label, href }) => (
        <Link
          key={view}
          href={href}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            active === view
              ? "bg-gray-900 text-white"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          }`}
        >
          {label}
        </Link>
      ))}
    </div>
  );
}
