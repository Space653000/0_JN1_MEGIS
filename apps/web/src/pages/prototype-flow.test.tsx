import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { initialPrototypeModel } from "../adapters/prototype-adapter";
import type { DemoResult, PrototypeViewModel } from "../types/prototype";
import { DesignPage } from "./DesignPage";
import { ResultsPage } from "./ResultsPage";
import { ReviewPage } from "./ReviewPage";

afterEach(cleanup);

function withinEnvelope(overrides: Partial<PrototypeViewModel["input"]> = {}): PrototypeViewModel {
  return {
    ...initialPrototypeModel,
    input: { ...initialPrototypeModel.input, width: 120, depth: 80, height: 20, ...overrides },
  };
}

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
    expect(screen.getByText(/Synthetic demo data/)).toBeInTheDocument();
    expect(screen.getByText(/No engineering artifact generated/)).toBeInTheDocument();
    expect(screen.getByText(/STEP、圖面 PDF、BOM CSV/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /download/i })).not.toBeInTheDocument();
  });
});

describe("G6 guided flow (UI-001)", () => {
  it("blocks next until a key PCB unknown is resolved", () => {
    const onNext = vi.fn();
    render(<DesignPage model={withinEnvelope()} setModel={vi.fn()} onNext={onNext} />);
    const next = screen.getByRole("button", { name: /檢視假設/i });
    fireEvent.click(next);
    expect(onNext).toHaveBeenCalledOnce();
    fireEvent.change(screen.getByLabelText("目前狀態"), { target: { value: "unknown" } });
    expect(screen.getByText(/PCB 外形範圍尚未確認/)).toBeInTheDocument();
    expect(next).toBeDisabled();
    expect(screen.getByText(/關鍵未知項目不會消失/)).toBeInTheDocument();
  });

  it("blocks next when outer dimensions exceed the verified envelope", () => {
    render(<DesignPage model={withinEnvelope({ width: 121 })} setModel={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByText(/已驗證外形上限：120 × 80 × 20 mm/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /檢視假設/i })).toBeDisabled();
  });

  it("enables next for an in-range draft and keeps the synthetic label visible", () => {
    const onNext = vi.fn();
    render(<DesignPage model={withinEnvelope()} setModel={vi.fn()} onNext={onNext} />);
    const next = screen.getByRole("button", { name: /檢視假設/i });
    expect(next).toBeEnabled();
    expect(screen.getByText(/Synthetic demo data/)).toBeInTheDocument();
    fireEvent.click(next);
    expect(onNext).toHaveBeenCalledOnce();
  });
});
