import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { repositoryProgressAdapter } from "../adapters/progress-adapter";
import { ProgressPage } from "./ProgressPage";

describe("Progress acceptance disclosure", () => {
  it("tracks the active repository work item and its evidence without claiming Gate completion", () => {
    const state = repositoryProgressAdapter.getSnapshot();
    const current = state.workItems.find((item) => item.id === state.currentWorkItem);
    const activeGate = state.gates.find((gate) => gate.status === "active");
    if (!current) throw new Error(`Missing current work item: ${state.currentWorkItem}`);
    if (!activeGate) throw new Error("Missing active Gate");
    render(<ProgressPage />);

    expect(screen.getByText(current.id)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: current.title })).toBeInTheDocument();
    expect(screen.getAllByText("施工中").length).toBeGreaterThan(0);
    expect(screen.getAllByText(activeGate.title)).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "等待真人驗收" })).toBeInTheDocument();
    expect(screen.getByText("具名真人完成鍵盤與螢幕閱讀器抽查")).toBeInTheDocument();
    expect(screen.getByText(/實際無障礙抽查者/)).toBeInTheDocument();
    expect(screen.getByText(/write-once 紀錄器/)).toBeInTheDocument();
    const disclosure = screen.getByRole("button", { name: "查看驗收條件" });
    expect(disclosure).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(disclosure);

    expect(disclosure).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "完成條件與責任邊界" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "已備妥的支援證據" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "下一步驗證指令" })).toBeInTheDocument();
    for (const path of current.evidence) expect(screen.getAllByText(path).length).toBeGreaterThan(0);
    for (const command of current.verificationCommands ?? []) expect(screen.getByText(command)).toBeInTheDocument();
    for (const result of current.acceptanceResults) {
      expect(screen.getAllByText(result.criterion).length).toBeGreaterThan(0);
      if (result.status === "passed") {
        expect(screen.getAllByText("已通過").length).toBeGreaterThan(0);
        for (const path of result.evidence) expect(screen.getAllByText(path).length).toBeGreaterThan(0);
      } else {
        expect(screen.getAllByText("待施工驗證").length).toBeGreaterThan(0);
        expect(screen.getAllByText(/支援材料已備妥，但完整人工驗收證據尚未形成/).length).toBeGreaterThan(0);
      }
    }
    expect(screen.getByText(new RegExp(`${current.gate} 尚未完成`))).toBeInTheDocument();
  });
});
