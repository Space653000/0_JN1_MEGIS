import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressPage } from "./ProgressPage";

describe("Progress acceptance disclosure", () => {
  it("reveals passed evidence while the active G0 CAD item remains in progress", () => {
    render(<ProgressPage />);

    expect(screen.getByText("G0-CAD-001")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CadQuery Reference Case spike" })).toBeInTheDocument();
    expect(screen.getAllByText("施工中").length).toBeGreaterThan(0);
    expect(screen.getAllByText("基礎建設與可行性")).toHaveLength(2);
    const disclosure = screen.getByRole("button", { name: "查看驗收條件" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(disclosure);

    expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "完成條件與責任邊界" })).toBeInTheDocument();
    expect(screen.getByText("已通過")).toBeInTheDocument();
    expect(screen.getByText("artifacts/g0-cad/reference_case.step")).toBeInTheDocument();
    expect(screen.getByText("artifacts/g0-cad/reference_case.stl")).toBeInTheDocument();
    expect(screen.getByText("artifacts/g0-cad/reference_case_section_z10.dxf")).toBeInTheDocument();
    expect(screen.queryByText("待施工驗證")).not.toBeInTheDocument();
    expect(screen.getByText(/G0 尚未完成/)).toBeInTheDocument();
  });
});
