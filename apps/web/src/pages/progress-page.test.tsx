import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressPage } from "./ProgressPage";

describe("Progress acceptance disclosure", () => {
  it("reveals repository evidence without claiming user acceptance", () => {
    render(<ProgressPage />);

    const disclosure = screen.getByRole("button", { name: "查看驗收條件" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(disclosure);

    expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "完成條件與責任邊界" })).toBeInTheDocument();
    expect(screen.getByText("execution/ui0/last-verification.json")).toBeInTheDocument();
    expect(screen.getByText("待使用者確認")).toBeInTheDocument();
    expect(screen.getByText(/系統不會代替使用者自動通過/)).toBeInTheDocument();
    expect(screen.getByText(/G0 尚未啟動/)).toBeInTheDocument();
  });
});
