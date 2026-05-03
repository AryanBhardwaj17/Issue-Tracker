import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// ─── Mock next/navigation ────────────────────────────────────────────────────

let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useParams: () => ({ projectId: "proj-1" }),
  useSearchParams: () => mockSearchParams,
}));

// Mock next/link to render a plain anchor
vi.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode; [k: string]: unknown }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

import ViewToggle from "@/components/issues/ViewToggle";

describe("ViewToggle", () => {
  beforeEach(() => {
    mockSearchParams = new URLSearchParams();
  });

  it("renders Board and Table links", () => {
    render(<ViewToggle active="issues" />);
    expect(screen.getByText("Board")).toBeInTheDocument();
    expect(screen.getByText("Table")).toBeInTheDocument();
  });

  it("highlights Table link when active=issues", () => {
    render(<ViewToggle active="issues" />);
    const table = screen.getByText("Table");
    expect(table.className).toContain("bg-gray-900");
    expect(table.className).toContain("text-white");
  });

  it("highlights Board link when active=board", () => {
    render(<ViewToggle active="board" />);
    const board = screen.getByText("Board");
    expect(board.className).toContain("bg-gray-900");
    expect(board.className).toContain("text-white");
  });

  it("inactive link has muted styling", () => {
    render(<ViewToggle active="issues" />);
    const board = screen.getByText("Board");
    expect(board.className).toContain("text-gray-600");
    expect(board.className).not.toContain("bg-gray-900");
  });

  it("Board link points to /projects/:projectId/board", () => {
    render(<ViewToggle active="issues" />);
    const board = screen.getByText("Board").closest("a");
    expect(board).toHaveAttribute("href", "/projects/proj-1/board");
  });

  it("Table link points to /projects/:projectId/issues", () => {
    render(<ViewToggle active="issues" />);
    const table = screen.getByText("Table").closest("a");
    expect(table).toHaveAttribute("href", "/projects/proj-1/issues");
  });

  it("preserves search params in links", () => {
    mockSearchParams = new URLSearchParams("priority=high&search=bug");
    render(<ViewToggle active="issues" />);

    const board = screen.getByText("Board").closest("a");
    expect(board).toHaveAttribute(
      "href",
      "/projects/proj-1/board?priority=high&search=bug",
    );

    const table = screen.getByText("Table").closest("a");
    expect(table).toHaveAttribute(
      "href",
      "/projects/proj-1/issues?priority=high&search=bug",
    );
  });

  it("no query string when searchParams are empty", () => {
    mockSearchParams = new URLSearchParams();
    render(<ViewToggle active="board" />);
    const table = screen.getByText("Table").closest("a");
    expect(table).toHaveAttribute("href", "/projects/proj-1/issues");
  });
});
