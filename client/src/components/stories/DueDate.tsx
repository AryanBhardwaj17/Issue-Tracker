import { format, isPast, isToday, parseISO } from "date-fns";

interface DueDateProps {
  dueDate: string | null;
  isDone?: boolean;
}

/**
 * Renders a formatted due date with overdue/today highlighting.
 * Null → em-dash.
 * Overdue (past + not done) → red with warning icon.
 * Due today (not done) → yellow.
 * Future → gray.
 */
export default function DueDate({ dueDate, isDone = false }: DueDateProps) {
  if (!dueDate) {
    return <span className="text-xs text-gray-400">—</span>;
  }

  const date = parseISO(dueDate);
  const formatted = format(date, "MMM d");

  const overdue = !isDone && isPast(date) && !isToday(date);
  const dueToday = !isDone && isToday(date);

  if (overdue) {
    return (
      <span className="text-xs text-red-600" title="Overdue">
        ⚠ {formatted}
      </span>
    );
  }

  if (dueToday) {
    return (
      <span className="text-xs font-medium text-yellow-600" title="Due today">
        {formatted}
      </span>
    );
  }

  return <span className="text-xs text-gray-500">{formatted}</span>;
}
