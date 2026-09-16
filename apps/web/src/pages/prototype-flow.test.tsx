import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { initialPrototypeModel } from "../adapters/prototype-adapter";
import type { DemoResult, PrototypeViewModel } from "../types/prototype";
import { DesignPage } from "./DesignPage";
import { ResultsPage } from "./ResultsPage";
import { ReviewPage } from "./ReviewPage";

describe("Fixture prototype flow", () => {
  it("renders data supplied by a replaceable model seam", () => {
    const alternate: PrototypeViewModel = { ...initialPrototypeModel, input: { ...initialPrototypeModel.input, width: 240, pcbCount: 1 } };
    render(<DesignPage model={alternate} setModel={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByText("240 × 80 × 35 mm")).toBeInTheDocument();
    expect(screen.getByText("1 片 PCB + USB-C")).toBeInTheDocument();
  });

  it("requires explicit acknowledgement before prototype simulation", () => {
    const onRun = vi.fn();
    const model = { ...initialPrototypeModel, review: [{ id: "unknown", label: "PCB envelope", value: "Unknown", provenance: "unknown" as const, critical: true }] };
    render(<ReviewPage model={model} onBack={vi.fn()} onRun={onRun} />);
    const run = screen.getByRole("button", { name: /執行原型模擬/i });
    expect(run).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(run);
    expect(onRun).toHaveBeenCalledOnce();
  });

  it("permanently labels synthetic results and exposes no artifact download", () => {
    const result: DemoResult = { maturity: "使用者體驗原型", dimensions: "120 × 80 × 35 mm", material: "6061 鋁合金", process: "三軸 CNC", checks: [], bom: [] };
    render(<ResultsPage result={result} onRestart={vi.fn()} />);
    expect(screen.getByText("未產生任何工程製品")).toBeInTheDocument();
    expect(screen.getByText(/STEP、圖面 PDF、BOM CSV/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /download/i })).not.toBeInTheDocument();
  });
});
