import type { StoryUser } from "@/lib/api";

// Same hashing pattern as Navbar.tsx — first letter of name as initial,
// deterministic background colour from the name string.
const BG_CLASSES = [
  "bg-blue-500",
  "bg-green-500",
  "bg-purple-500",
  "bg-yellow-500",
  "bg-pink-500",
  "bg-indigo-500",
];

function hashColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return BG_CLASSES[Math.abs(hash) % BG_CLASSES.length];
}

function initials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

interface AssigneeAvatarProps {
  assignee: StoryUser | null;
  showName?: boolean;
  size?: "sm" | "md";
}

export default function AssigneeAvatar({
  assignee,
  showName = false,
  size = "sm",
}: AssigneeAvatarProps) {
  const sizeClass = size === "sm" ? "h-6 w-6 text-xs" : "h-8 w-8 text-sm";

  if (!assignee) {
    return (
      <div className="flex items-center gap-1.5">
        <div
          className={`${sizeClass} flex items-center justify-center rounded-full bg-gray-200 font-medium text-gray-500`}
        >
          ?
        </div>
        {showName && <span className="text-xs text-gray-400">Unassigned</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <div
        className={`${sizeClass} flex shrink-0 items-center justify-center rounded-full font-medium text-white ${hashColor(assignee.name)}`}
        title={assignee.name}
      >
        {initials(assignee.name)}
      </div>
      {showName && (
        <span className="truncate text-xs text-gray-700">{assignee.name}</span>
      )}
    </div>
  );
}
