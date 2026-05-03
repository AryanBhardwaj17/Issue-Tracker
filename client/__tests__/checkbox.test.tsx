import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Checkbox from "@/components/ui/Checkbox";

describe("Checkbox", () => {
  it("renders unchecked state", () => {
    render(<Checkbox checked={false} onChange={() => {}} />);
    const btn = screen.getByRole("checkbox");
    expect(btn).toHaveAttribute("aria-checked", "false");
    // No checkmark SVG when unchecked
    expect(btn.querySelector("svg")).toBeNull();
  });

  it("renders checked state with checkmark", () => {
    render(<Checkbox checked={true} onChange={() => {}} />);
    const btn = screen.getByRole("checkbox");
    expect(btn).toHaveAttribute("aria-checked", "true");
    expect(btn.querySelector("svg")).not.toBeNull();
  });

  it("calls onChange with toggled value on click", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Checkbox checked={false} onChange={onChange} />);

    await user.click(screen.getByRole("checkbox"));
    expect(onChange).toHaveBeenCalledOnce();
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it("calls onChange(false) when checked checkbox is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Checkbox checked={true} onChange={onChange} />);

    await user.click(screen.getByRole("checkbox"));
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it("does NOT call onChange when disabled", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Checkbox checked={false} disabled onChange={onChange} />);

    const btn = screen.getByRole("checkbox");
    expect(btn).toBeDisabled();
    await user.click(btn);
    expect(onChange).not.toHaveBeenCalled();
  });

  it("renders title attribute for tooltip", () => {
    render(
      <Checkbox
        checked={false}
        onChange={() => {}}
        title="Only the assignee or owner can toggle"
      />,
    );
    expect(screen.getByRole("checkbox")).toHaveAttribute(
      "title",
      "Only the assignee or owner can toggle",
    );
  });

  it("does not render title when not provided", () => {
    render(<Checkbox checked={false} onChange={() => {}} />);
    expect(screen.getByRole("checkbox")).not.toHaveAttribute("title");
  });

  it("applies disabled styling (opacity-50, cursor-not-allowed)", () => {
    render(<Checkbox checked={false} disabled onChange={() => {}} />);
    const btn = screen.getByRole("checkbox");
    expect(btn.className).toContain("opacity-50");
    expect(btn.className).toContain("cursor-not-allowed");
  });

  it("stopPropagation prevents parent handler from firing", async () => {
    const user = userEvent.setup();
    const parentClick = vi.fn();
    const onChange = vi.fn();

    render(
      <div onClick={parentClick}>
        <Checkbox checked={false} onChange={onChange} />
      </div>,
    );

    await user.click(screen.getByRole("checkbox"));
    expect(onChange).toHaveBeenCalledOnce();
    expect(parentClick).not.toHaveBeenCalled();
  });
});
