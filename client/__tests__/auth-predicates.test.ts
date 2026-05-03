import { describe, it, expect } from "vitest";
import {
  canEditStory,
  canChangeStatus,
  canToggleIsDone,
  canDeleteTask,
} from "@/lib/auth-predicates";
import type { Story, Task, Subtask } from "@/lib/api";

// ─── Factories ───────────────────────────────────────────────────────────────

const OWNER_ID = "owner-1";
const REPORTER_ID = "reporter-1";
const ASSIGNEE_ID = "assignee-1";
const OTHER_ID = "other-member-1";

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
    assignee: { id: ASSIGNEE_ID, name: "Assignee" },
    reporter: { id: REPORTER_ID, name: "Reporter" },
    dueDate: null,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: "task-1",
    storyId: "story-1",
    parentId: null,
    title: "Test task",
    description: null,
    priority: "medium",
    assignee: { id: ASSIGNEE_ID, name: "Assignee" },
    reporterId: REPORTER_ID,
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
    title: "Test subtask",
    description: null,
    priority: "low",
    assignee: { id: ASSIGNEE_ID, name: "Assignee" },
    reporterId: REPORTER_ID,
    dueDate: null,
    isDone: false,
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

// ─── canEditStory ────────────────────────────────────────────────────────────

describe("canEditStory", () => {
  it("owner can always edit", () => {
    const story = makeStory();
    expect(canEditStory(story, OWNER_ID, "owner")).toBe(true);
  });

  it("reporter can edit their story", () => {
    const story = makeStory();
    expect(canEditStory(story, REPORTER_ID, "member")).toBe(true);
  });

  it("assignee can edit assigned story", () => {
    const story = makeStory();
    expect(canEditStory(story, ASSIGNEE_ID, "member")).toBe(true);
  });

  it("other member cannot edit a story they are not reporter or assignee of", () => {
    const story = makeStory();
    expect(canEditStory(story, OTHER_ID, "member")).toBe(false);
  });

  it("other member cannot edit unassigned story they did not report", () => {
    const story = makeStory({ assignee: null });
    expect(canEditStory(story, OTHER_ID, "member")).toBe(false);
  });

  it("reporter can edit unassigned story", () => {
    const story = makeStory({ assignee: null });
    expect(canEditStory(story, REPORTER_ID, "member")).toBe(true);
  });

  it("owner can edit even if not reporter or assignee", () => {
    const story = makeStory();
    expect(canEditStory(story, "random-owner-id", "owner")).toBe(true);
  });
});

// ─── canChangeStatus ─────────────────────────────────────────────────────────

describe("canChangeStatus", () => {
  describe("assigned story", () => {
    it("owner can change status", () => {
      const story = makeStory();
      expect(canChangeStatus(story, OWNER_ID, "owner")).toBe(true);
    });

    it("assignee can change status", () => {
      const story = makeStory();
      expect(canChangeStatus(story, ASSIGNEE_ID, "member")).toBe(true);
    });

    it("reporter (non-assignee) cannot change status of assigned story", () => {
      const story = makeStory();
      expect(canChangeStatus(story, REPORTER_ID, "member")).toBe(false);
    });

    it("other member cannot change status of assigned story", () => {
      const story = makeStory();
      expect(canChangeStatus(story, OTHER_ID, "member")).toBe(false);
    });
  });

  describe("unassigned story", () => {
    it("owner can change status", () => {
      const story = makeStory({ assignee: null });
      expect(canChangeStatus(story, OWNER_ID, "owner")).toBe(true);
    });

    it("reporter can change status (edit guard fallback)", () => {
      const story = makeStory({ assignee: null });
      expect(canChangeStatus(story, REPORTER_ID, "member")).toBe(true);
    });

    it("other member cannot change status of unassigned story", () => {
      const story = makeStory({ assignee: null });
      expect(canChangeStatus(story, OTHER_ID, "member")).toBe(false);
    });
  });
});

// ─── canToggleIsDone ─────────────────────────────────────────────────────────

describe("canToggleIsDone", () => {
  describe("assigned task", () => {
    it("owner can toggle", () => {
      const task = makeTask();
      expect(canToggleIsDone(task, OWNER_ID, "owner")).toBe(true);
    });

    it("assignee can toggle", () => {
      const task = makeTask();
      expect(canToggleIsDone(task, ASSIGNEE_ID, "member")).toBe(true);
    });

    it("other member cannot toggle assigned task", () => {
      const task = makeTask();
      expect(canToggleIsDone(task, OTHER_ID, "member")).toBe(false);
    });

    it("reporter (task creator) can toggle assigned task", () => {
      const task = makeTask();
      expect(canToggleIsDone(task, REPORTER_ID, "member")).toBe(true);
    });
  });

  describe("unassigned task", () => {
    it("any member can toggle unassigned task", () => {
      const task = makeTask({ assignee: null });
      expect(canToggleIsDone(task, OTHER_ID, "member")).toBe(true);
    });

    it("owner can toggle unassigned task", () => {
      const task = makeTask({ assignee: null });
      expect(canToggleIsDone(task, OWNER_ID, "owner")).toBe(true);
    });

    it("reporter can toggle unassigned task", () => {
      const task = makeTask({ assignee: null });
      expect(canToggleIsDone(task, REPORTER_ID, "member")).toBe(true);
    });
  });

  describe("assigned subtask", () => {
    it("owner can toggle", () => {
      const subtask = makeSubtask();
      expect(canToggleIsDone(subtask, OWNER_ID, "owner")).toBe(true);
    });

    it("assignee can toggle", () => {
      const subtask = makeSubtask();
      expect(canToggleIsDone(subtask, ASSIGNEE_ID, "member")).toBe(true);
    });

    it("other member cannot toggle assigned subtask", () => {
      const subtask = makeSubtask();
      expect(canToggleIsDone(subtask, OTHER_ID, "member")).toBe(false);
    });
  });

  describe("unassigned subtask", () => {
    it("any member can toggle unassigned subtask", () => {
      const subtask = makeSubtask({ assignee: null });
      expect(canToggleIsDone(subtask, OTHER_ID, "member")).toBe(true);
    });
  });
});

// ─── canDeleteTask ───────────────────────────────────────────────────────────

describe("canDeleteTask", () => {
  it("owner can always delete", () => {
    const task = makeTask();
    expect(canDeleteTask(task, OWNER_ID, "owner")).toBe(true);
  });

  it("reporter can delete their task", () => {
    const task = makeTask();
    expect(canDeleteTask(task, REPORTER_ID, "member")).toBe(true);
  });

  it("assignee (non-reporter) cannot delete task", () => {
    const task = makeTask();
    expect(canDeleteTask(task, ASSIGNEE_ID, "member")).toBe(false);
  });

  it("other member cannot delete task", () => {
    const task = makeTask();
    expect(canDeleteTask(task, OTHER_ID, "member")).toBe(false);
  });

  it("reporter can delete subtask", () => {
    const subtask = makeSubtask();
    expect(canDeleteTask(subtask, REPORTER_ID, "member")).toBe(true);
  });

  it("other member cannot delete subtask", () => {
    const subtask = makeSubtask();
    expect(canDeleteTask(subtask, OTHER_ID, "member")).toBe(false);
  });

  it("owner can delete subtask even if not reporter", () => {
    const subtask = makeSubtask();
    expect(canDeleteTask(subtask, "random-owner-id", "owner")).toBe(true);
  });
});
