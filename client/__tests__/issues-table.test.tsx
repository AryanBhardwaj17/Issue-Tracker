import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import IssuesTable from "@/components/issues/IssuesTable";
import type { Story } from "@/lib/api";
import type { SortField, SortOrder } from "@/components/issues/IssuesTable";

// ─── Mock child components to keep tests focused ─────────────────────────────

vi.mock("@/components/stories/StatusBadge", () => ({
  __esModule: true,
  default: ({ status }: { status: string }) => (
    <span data-testid="status-badge">{status}</span>
  ),
}));

vi.mock("@/components/stories/PriorityBadge", () => ({
  __esModule: true,
  default: ({ priority }: { priority: string }) => (
    <span data-testid="priority-badge">{priority}</span>
  ),
}));

vi.mock("@/components/stories/DueDate", () => ({
  __esModule: true,
  default: ({ dueDate, isDone }: { dueDate: string | null; isDone: boolean }) => (
    <span data-testid="due-date">{dueDate ?? "—"}</span>
  ),
}));

vi.mock("@/components/stories/AssigneeAvatar", () => ({
  __esModule: true,
  default: ({ assignee }: { assignee: { id: string; name: string } | null }) => (
    <span data-testid="assignee-avatar">{assignee?.name ?? "Unassigned"}</span>
  ),
}));

vi.mock("@/components/issues/TaskRows", () => ({
  __esModule: true,
  default: ({ storyId }: { storyId: string }) => (
    <tr data-testid={`task-rows-${storyId}`}>
      <td colSpan={9}>Tasks for {storyId}</td>
    </tr>
  ),
}));

// ─── Factories ───────────────────────────────────────────────────────────────

function makeStory(overrides: Partial<Story> = {}): Story {
  return {
    id: "story-1",
    storyKey: "PROJ-1",
    title: "Test story",
    description: null,
    epicId: null,
    status: "todo",
    priority: "medium",
    storyPoints: null,
    assignee: { id: "user-1", name: "Alice" },
    reporter: { id: "user-2", name: "Bob" },
    dueDate: null,
    createdAt: "2025-06-15T10:00:00Z",
    updatedAt: "2025-06-15T10:00:00Z",
    ...overrides,
  };
}

const defaultProps = () => ({
  projectId: "proj-1",
  userId: "user-1",
  role: "member" as const,
  expandedStories: new Set<string>(),
  onToggleExpand: vi.fn(),
  sort: { sortBy: "priority" as SortField, sortOrder: "desc" as SortOrder },
  onSortChange: vi.fn(),
  epicMap: new Map<string, string>(),
});

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("IssuesTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Rendering ────────────────────────────────────────────────────────────

  it("returns null when stories array is empty", () => {
    const { container } = render(
      <IssuesTable stories={[]} {...defaultProps()} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders table with correct column headers", () => {
    const stories = [makeStory()];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Priority")).toBeInTheDocument();
    expect(screen.getByText("Points")).toBeInTheDocument();
    expect(screen.getByText("Assignee")).toBeInTheDocument();
    expect(screen.getByText("Epic")).toBeInTheDocument();
    expect(screen.getByText("Due Date")).toBeInTheDocument();
    expect(screen.getByText("Created")).toBeInTheDocument();
  });

  it("renders story key and title", () => {
    const stories = [makeStory({ storyKey: "SHOP-42", title: "Fix login" })];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByText("SHOP-42")).toBeInTheDocument();
    expect(screen.getByText("Fix login")).toBeInTheDocument();
  });

  it("renders status badge for each story", () => {
    const stories = [makeStory({ status: "in_progress" })];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByTestId("status-badge")).toHaveTextContent("in_progress");
  });

  it("renders priority badge for each story", () => {
    const stories = [makeStory({ priority: "critical" })];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByTestId("priority-badge")).toHaveTextContent("critical");
  });

  it("renders story points or em-dash when null", () => {
    const stories = [
      makeStory({ id: "s1", storyPoints: 5 }),
      makeStory({ id: "s2", storyPoints: null }),
    ];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByText("5")).toBeInTheDocument();
    // em-dash for null points
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(1);
  });

  it("renders assignee avatar", () => {
    const stories = [makeStory({ assignee: { id: "u1", name: "Alice" } })];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByTestId("assignee-avatar")).toHaveTextContent("Alice");
  });

  it("renders epic name in purple badge when epicId is in epicMap", () => {
    const epicMap = new Map([["epic-1", "Authentication"]]);
    const stories = [makeStory({ epicId: "epic-1" })];
    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        epicMap={epicMap}
      />,
    );

    expect(screen.getByText("Authentication")).toBeInTheDocument();
  });

  it("renders em-dash when story has no epic", () => {
    const stories = [makeStory({ epicId: null })];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    // at least one em-dash from epic cell (could also be from points)
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it("renders multiple stories", () => {
    const stories = [
      makeStory({ id: "s1", storyKey: "PROJ-1", title: "Story A" }),
      makeStory({ id: "s2", storyKey: "PROJ-2", title: "Story B" }),
      makeStory({ id: "s3", storyKey: "PROJ-3", title: "Story C" }),
    ];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByText("Story A")).toBeInTheDocument();
    expect(screen.getByText("Story B")).toBeInTheDocument();
    expect(screen.getByText("Story C")).toBeInTheDocument();
  });

  // ── Expand / Collapse ──────────────────────────────────────────────────

  it("shows collapsed chevron (▶) by default", () => {
    const stories = [makeStory()];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByText("▶")).toBeInTheDocument();
  });

  it("shows expanded chevron (▼) when story is expanded", () => {
    const stories = [makeStory()];
    const expanded = new Set(["story-1"]);
    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        expandedStories={expanded}
      />,
    );

    expect(screen.getByText("▼")).toBeInTheDocument();
  });

  it("calls onToggleExpand when chevron button is clicked", async () => {
    const user = userEvent.setup();
    const onToggleExpand = vi.fn();
    const stories = [makeStory()];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        onToggleExpand={onToggleExpand}
      />,
    );

    await user.click(screen.getByText("▶"));
    expect(onToggleExpand).toHaveBeenCalledWith("story-1");
  });

  it("calls onToggleExpand when row is clicked", async () => {
    const user = userEvent.setup();
    const onToggleExpand = vi.fn();
    const stories = [makeStory({ title: "Click me" })];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        onToggleExpand={onToggleExpand}
      />,
    );

    await user.click(screen.getByText("Click me"));
    expect(onToggleExpand).toHaveBeenCalledWith("story-1");
  });

  it("renders TaskRows when story is expanded", () => {
    const stories = [makeStory()];
    const expanded = new Set(["story-1"]);
    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        expandedStories={expanded}
      />,
    );

    expect(screen.getByTestId("task-rows-story-1")).toBeInTheDocument();
  });

  it("does NOT render TaskRows when story is collapsed", () => {
    const stories = [makeStory()];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.queryByTestId("task-rows-story-1")).not.toBeInTheDocument();
  });

  // ── Sorting ────────────────────────────────────────────────────────────

  it("calls onSortChange with asc when clicking an unsorted column", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const stories = [makeStory()];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        sort={{ sortBy: "priority", sortOrder: "desc" }}
        onSortChange={onSortChange}
      />,
    );

    await user.click(screen.getByText("Created"));
    expect(onSortChange).toHaveBeenCalledWith({
      sortBy: "created_at",
      sortOrder: "asc",
    });
  });

  it("cycles asc → desc on already sorted column", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const stories = [makeStory()];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        sort={{ sortBy: "created_at", sortOrder: "asc" }}
        onSortChange={onSortChange}
      />,
    );

    await user.click(screen.getByText("Created"));
    expect(onSortChange).toHaveBeenCalledWith({
      sortBy: "created_at",
      sortOrder: "desc",
    });
  });

  it("cycles desc → default (priority desc) on already sorted column", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const stories = [makeStory()];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        sort={{ sortBy: "created_at", sortOrder: "desc" }}
        onSortChange={onSortChange}
      />,
    );

    await user.click(screen.getByText("Created"));
    expect(onSortChange).toHaveBeenCalledWith({
      sortBy: "priority",
      sortOrder: "desc",
    });
  });

  it("non-sortable columns (Status, Points, Assignee, Epic) do not trigger sort", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const stories = [makeStory()];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        onSortChange={onSortChange}
      />,
    );

    await user.click(screen.getByText("Status"));
    await user.click(screen.getByText("Points"));
    await user.click(screen.getByText("Assignee"));
    await user.click(screen.getByText("Epic"));
    expect(onSortChange).not.toHaveBeenCalled();
  });

  it("Title header triggers sort on story_key", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const stories = [makeStory()];

    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        onSortChange={onSortChange}
      />,
    );

    await user.click(screen.getByText("Title"));
    expect(onSortChange).toHaveBeenCalledWith({
      sortBy: "story_key",
      sortOrder: "asc",
    });
  });

  // ── Overdue highlighting ───────────────────────────────────────────────

  it("applies bg-red-50/40 to overdue stories", () => {
    const pastDate = "2020-01-01T00:00:00Z";
    const stories = [makeStory({ dueDate: pastDate, status: "todo" })];
    const { container } = render(
      <IssuesTable stories={stories} {...defaultProps()} />,
    );

    // The tr element should have the overdue class
    const rows = container.querySelectorAll("tbody tr");
    const storyRow = rows[0];
    expect(storyRow.className).toContain("bg-red-50/40");
  });

  it("does NOT highlight overdue story when status is done", () => {
    const pastDate = "2020-01-01T00:00:00Z";
    const stories = [makeStory({ dueDate: pastDate, status: "done" })];
    const { container } = render(
      <IssuesTable stories={stories} {...defaultProps()} />,
    );

    const rows = container.querySelectorAll("tbody tr");
    const storyRow = rows[0];
    expect(storyRow.className).not.toContain("bg-red-50/40");
  });

  it("does NOT highlight story with no due date", () => {
    const stories = [makeStory({ dueDate: null, status: "todo" })];
    const { container } = render(
      <IssuesTable stories={stories} {...defaultProps()} />,
    );

    const rows = container.querySelectorAll("tbody tr");
    const storyRow = rows[0];
    expect(storyRow.className).not.toContain("bg-red-50/40");
  });

  it("does NOT highlight story with future due date", () => {
    const futureDate = "2099-12-31T00:00:00Z";
    const stories = [makeStory({ dueDate: futureDate, status: "todo" })];
    const { container } = render(
      <IssuesTable stories={stories} {...defaultProps()} />,
    );

    const rows = container.querySelectorAll("tbody tr");
    const storyRow = rows[0];
    expect(storyRow.className).not.toContain("bg-red-50/40");
  });

  // ── Edge cases ─────────────────────────────────────────────────────────

  it("renders formatted created date", () => {
    const stories = [makeStory({ createdAt: "2025-06-15T10:00:00Z" })];
    render(<IssuesTable stories={stories} {...defaultProps()} />);

    expect(screen.getByText("Jun 15")).toBeInTheDocument();
  });

  it("only expanded stories show TaskRows (multiple stories)", () => {
    const stories = [
      makeStory({ id: "s1" }),
      makeStory({ id: "s2" }),
    ];
    const expanded = new Set(["s1"]);
    render(
      <IssuesTable
        stories={stories}
        {...defaultProps()}
        expandedStories={expanded}
      />,
    );

    expect(screen.getByTestId("task-rows-s1")).toBeInTheDocument();
    expect(screen.queryByTestId("task-rows-s2")).not.toBeInTheDocument();
  });
});
