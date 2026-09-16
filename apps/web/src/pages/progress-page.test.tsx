import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressPage } from "./ProgressPage";

describe("Progress acceptance disclosure", () => {
  it("reveals the active G0 environment work item without claiming completion", () => {
    render(<ProgressPage />);

    expect(screen.getByText("G0-ENV-001")).toBeInTheDocument();
    expect(screen.getAllByText("基礎建設與可行性")).toHaveLength(2);
    const disclosure = screen.getByRole("button", { name: "查看驗收條件" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(disclosure);

    expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "完成條件與責任邊界" })).toBeInTheDocument();
    expect(screen.getByText("待施工驗證")).toBeInTheDocument();
    expect(screen.getByText(/尚未形成可重跑證據/)).toBeInTheDocument();
    expect(screen.queryByText("已通過")).not.toBeInTheDocument();
    expect(screen.getByText(/G0 尚未完成/)).toBeInTheDocument();
  });
});
