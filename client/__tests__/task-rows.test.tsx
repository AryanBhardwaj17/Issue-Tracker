import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Task, Subtask, Priority } from "@/lib/api";

// ─── Mock hooks ──────────────────────────────────────────────────────────────

const mockMutateTask = vi.fn();
const mockMutateSubtask = vi.fn();

let mockTasksReturn: {
  data: { items: Task[] } | undefined;
  isLoading: boolean;
  isError: boolean;
} = {
  data: { items: [] },
  isLoading: false,
  isError: false,
};

vi.mock("@/hooks/useTasks", () => ({
  useTasks: () => mockTasksReturn,
  useToggleTaskDone: () => ({ mutate: mockMutateTask }),
  useToggleSubtaskDone: () => ({ mutate: mockMutateSubtask }),
}));

vi.mock("@/components/stories/PriorityBadge", () => ({
  __esModule: true,
  default: ({ priority }: { priority: string }) => (
    <span data-testid="priority-badge">{priority}</span>
  ),
}));

vi.mock("@/components/stories/AssigneeAvatar", () => ({
  __esModule: true,
  default: ({ assignee }: { assignee: { id: string; name: string } | null }) => (
    <span data-testid="assignee-avatar">{assignee?.name ?? "Unassigned"}</span>
  ),
}));

import TaskRows from "@/components/issues/TaskRows";

// ─── Factories ───────────────────────────────────────────────────────────────

const USER_ID = "user-1";
const ASSIGNEE_ID = "assignee-1";
const OTHER_ID = "other-1";

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: "task-1",
    storyId: "story-1",
    parentId: null,
    title: "Implement login",
    description: null,
    priority: "medium" as Priority,
    assignee: { id: ASSIGNEE_ID, name: "Assignee User" },
    reporterId: "reporter-1",
    dueDate: null,
    isDone: false,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
    subtasks: [],
    ...overrides,
  };
}

function makeSubtask(overrides: Partial<Subtask> = {}): Subtask {
  return {
    id: "subtask-1",
    parentId: "task-1",
    title: "Write unit tests",
    description: null,
    priority: "low" as Priority,
    assignee: { id: ASSIGNEE_ID, name: "Assignee User" },
    reporterId: "reporter-1",
    dueDate: null,
    isDone: false,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderTaskRows(props: Partial<Parameters<typeof TaskRows>[0]> = {}) {
  return render(
    <table>
      <tbody>
        <TaskRows
          projectId="proj-1"
          storyId="story-1"
          userId={USER_ID}
          role="member"
          {...props}
        />
      </tbody>
    </table>,
  );
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("TaskRows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTasksReturn = {
      data: { items: [] },
      isLoading: false,
      isError: false,
    };
  });

  // ── Loading state ──────────────────────────────────────────────────────

  it("shows loading spinner while fetching", () => {
    mockTasksReturn = { data: undefined, isLoading: true, isError: false };
    renderTaskRows();

    expect(screen.getByText("Loading tasks…")).toBeInTheDocument();
  });

  // ── Error state ────────────────────────────────────────────────────────

  it("shows error message on fetch failure", () => {
    mockTasksReturn = { data: undefined, isLoading: false, isError: true };
    renderTaskRows();

    expect(screen.getByText("Failed to load tasks")).toBeInTheDocument();
  });

  // ── Empty state ────────────────────────────────────────────────────────

  it("shows 'No tasks' when tasks array is empty", () => {
    mockTasksReturn = { data: { items: [] }, isLoading: false, isError: false };
    renderTaskRows();

    expect(screen.getByText("No tasks")).toBeInTheDocument();
  });

  // ── Task rendering ────────────────────────────────────────────────────

  it("renders task title", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ title: "Implement login" })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.getByText("Implement login")).toBeInTheDocument();
  });

  it("renders priority badge for task", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ priority: "high" })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.getByTestId("priority-badge")).toHaveTextContent("high");
  });

  it("renders assignee avatar for task", () => {
    mockTasksReturn = {
      data: {
        items: [
          makeTask({ assignee: { id: "u1", name: "Alice" } }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.getByTestId("assignee-avatar")).toHaveTextContent("Alice");
  });

  it("renders Unassigned when task has no assignee", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ assignee: null })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.getByTestId("assignee-avatar")).toHaveTextContent("Unassigned");
  });

  it("renders multiple tasks", () => {
    mockTasksReturn = {
      data: {
        items: [
          makeTask({ id: "t1", title: "Task A" }),
          makeTask({ id: "t2", title: "Task B" }),
          makeTask({ id: "t3", title: "Task C" }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.getByText("Task A")).toBeInTheDocument();
    expect(screen.getByText("Task B")).toBeInTheDocument();
    expect(screen.getByText("Task C")).toBeInTheDocument();
  });

  // ── Checkbox / isDone ─────────────────────────────────────────────────

  it("renders unchecked checkbox for not-done task", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ isDone: false })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("aria-checked", "false");
  });

  it("renders checked checkbox for done task", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ isDone: true })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("aria-checked", "true");
  });

  it("applies line-through to done task title", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ isDone: true, title: "Done task" })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    const title = screen.getByText("Done task");
    expect(title.className).toContain("line-through");
  });

  // ── Permission: checkbox disabled for non-assignee non-owner ──────────

  it("checkbox enabled for assignee", () => {
    mockTasksReturn = {
      data: {
        items: [makeTask({ assignee: { id: USER_ID, name: "Me" } })],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: USER_ID, role: "member" });

    expect(screen.getByRole("checkbox")).not.toBeDisabled();
  });

  it("checkbox enabled for owner", () => {
    mockTasksReturn = {
      data: { items: [makeTask()] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: "owner-id", role: "owner" });

    expect(screen.getByRole("checkbox")).not.toBeDisabled();
  });

  it("checkbox disabled for non-assignee member on assigned task", () => {
    mockTasksReturn = {
      data: {
        items: [
          makeTask({ assignee: { id: ASSIGNEE_ID, name: "Someone else" } }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: OTHER_ID, role: "member" });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeDisabled();
    expect(checkbox).toHaveAttribute(
      "title",
      "Only the assignee or owner can toggle",
    );
  });

  it("checkbox enabled for any member on unassigned task", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ assignee: null })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: OTHER_ID, role: "member" });

    expect(screen.getByRole("checkbox")).not.toBeDisabled();
  });

  // ── Toggle mutation ───────────────────────────────────────────────────

  it("calls toggle mutation when checkbox is clicked", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            id: "task-99",
            isDone: false,
            assignee: { id: USER_ID, name: "Me" },
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: USER_ID });

    await user.click(screen.getByRole("checkbox"));
    expect(mockMutateTask).toHaveBeenCalledWith({
      taskId: "task-99",
      body: { isDone: true },
    });
  });

  // ── Subtask expand ────────────────────────────────────────────────────

  it("does NOT show expand chevron when task has no subtasks", () => {
    mockTasksReturn = {
      data: { items: [makeTask({ subtasks: [] })] },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.queryByText("▶")).not.toBeInTheDocument();
    expect(screen.queryByText("▼")).not.toBeInTheDocument();
  });

  it("shows expand chevron (▶) when task has subtasks", () => {
    mockTasksReturn = {
      data: {
        items: [makeTask({ subtasks: [makeSubtask()] })],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    expect(screen.getByText("▶")).toBeInTheDocument();
  });

  it("expands subtasks when chevron is clicked", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            subtasks: [
              makeSubtask({ title: "Write unit tests" }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    // Subtask not visible initially
    expect(screen.queryByText("Write unit tests")).not.toBeInTheDocument();

    // Click expand
    await user.click(screen.getByText("▶"));

    // Now visible
    expect(screen.getByText("Write unit tests")).toBeInTheDocument();
    // Chevron flips
    expect(screen.getByText("▼")).toBeInTheDocument();
  });

  it("collapses subtasks when expanded chevron is clicked", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            subtasks: [makeSubtask({ title: "Subtask A" })],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    // Expand
    await user.click(screen.getByText("▶"));
    expect(screen.getByText("Subtask A")).toBeInTheDocument();

    // Collapse
    await user.click(screen.getByText("▼"));
    expect(screen.queryByText("Subtask A")).not.toBeInTheDocument();
  });

  // ── Subtask rendering & permissions ───────────────────────────────────

  it("subtask checkbox disabled for non-assignee member", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            subtasks: [
              makeSubtask({
                assignee: { id: ASSIGNEE_ID, name: "Someone" },
              }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: OTHER_ID, role: "member" });

    // Expand to show subtask
    await user.click(screen.getByText("▶"));

    // Task checkbox (first) + subtask checkbox (second)
    const checkboxes = screen.getAllByRole("checkbox");
    // The subtask one (second) should be disabled
    expect(checkboxes[1]).toBeDisabled();
    expect(checkboxes[1]).toHaveAttribute(
      "title",
      "Only the assignee or owner can toggle",
    );
  });

  it("subtask checkbox enabled for assignee", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            assignee: { id: USER_ID, name: "Me" },
            subtasks: [
              makeSubtask({
                assignee: { id: USER_ID, name: "Me" },
              }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: USER_ID, role: "member" });

    await user.click(screen.getByText("▶"));

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes[1]).not.toBeDisabled();
  });

  it("subtask checkbox enabled for owner regardless of assignee", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            subtasks: [
              makeSubtask({
                assignee: { id: "someone-else", name: "Other" },
              }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: "owner-id", role: "owner" });

    await user.click(screen.getByText("▶"));

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes[1]).not.toBeDisabled();
  });

  it("subtask checkbox enabled for any member when unassigned", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            assignee: null,
            subtasks: [makeSubtask({ assignee: null })],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: OTHER_ID, role: "member" });

    await user.click(screen.getByText("▶"));

    const checkboxes = screen.getAllByRole("checkbox");
    // Both task and subtask should be enabled
    expect(checkboxes[0]).not.toBeDisabled();
    expect(checkboxes[1]).not.toBeDisabled();
  });

  it("toggling subtask checkbox calls subtask mutation", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            assignee: { id: USER_ID, name: "Me" },
            subtasks: [
              makeSubtask({
                id: "st-42",
                isDone: false,
                assignee: { id: USER_ID, name: "Me" },
              }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: USER_ID, role: "member" });

    await user.click(screen.getByText("▶"));
    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[1]); // subtask checkbox

    expect(mockMutateSubtask).toHaveBeenCalledWith({
      subtaskId: "st-42",
      body: { isDone: true },
    });
  });

  it("subtask line-through when isDone", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            assignee: { id: USER_ID, name: "Me" },
            subtasks: [
              makeSubtask({ title: "Done subtask", isDone: true }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows({ userId: USER_ID, role: "member" });

    await user.click(screen.getByText("▶"));

    const title = screen.getByText("Done subtask");
    expect(title.className).toContain("line-through");
  });

  // ── Multiple subtasks ─────────────────────────────────────────────────

  it("renders all subtasks when expanded", async () => {
    const user = userEvent.setup();
    mockTasksReturn = {
      data: {
        items: [
          makeTask({
            assignee: null,
            subtasks: [
              makeSubtask({ id: "s1", title: "Sub A", assignee: null }),
              makeSubtask({ id: "s2", title: "Sub B", assignee: null }),
              makeSubtask({ id: "s3", title: "Sub C", assignee: null }),
            ],
          }),
        ],
      },
      isLoading: false,
      isError: false,
    };
    renderTaskRows();

    await user.click(screen.getByText("▶"));

    expect(screen.getByText("Sub A")).toBeInTheDocument();
    expect(screen.getByText("Sub B")).toBeInTheDocument();
    expect(screen.getByText("Sub C")).toBeInTheDocument();
  });
});
