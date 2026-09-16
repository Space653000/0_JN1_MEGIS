import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressPage } from "./ProgressPage";

describe("Progress acceptance disclosure", () => {
  it("reveals the active G0 work item and formal evidence", () => {
    render(<ProgressPage />);

    expect(screen.getByText("G0-REP-001")).toBeInTheDocument();
    expect(screen.getAllByText("基礎建設與可行性")).toHaveLength(2);
    const disclosure = screen.getByRole("button", { name: "查看驗收條件" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(disclosure);

    expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "完成條件與責任邊界" })).toBeInTheDocument();
    expect(screen.getByText("docs/UI0_ACCEPTANCE.md")).toBeInTheDocument();
    expect(screen.getAllByText("已通過")).toHaveLength(3);
    expect(screen.getByText("scripts/verify-control-plane.mjs")).toBeInTheDocument();
    expect(screen.queryByText("待施工驗證")).not.toBeInTheDocument();
    expect(screen.getByText(/G0 尚未完成/)).toBeInTheDocument();
  });
});
