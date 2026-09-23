import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { initialPrototypeModel } from "../adapters/prototype-adapter";
import { engineeringCatalogFixture, irDraftFixture } from "../test-fixtures";
import type { PrototypeViewModel } from "../types/prototype";
import { DesignPage } from "./DesignPage";
import { ResultsPage } from "./ResultsPage";
import { ReviewPage } from "./ReviewPage";

afterEach(cleanup);
function model(overrides: Partial<PrototypeViewModel["input"]> = {}): PrototypeViewModel { return { ...initialPrototypeModel, input: { ...initialPrototypeModel.input, ...overrides } }; }

describe("G6 real local API flow", () => {
  it("renders the capability envelope supplied by the backend catalog", () => {
    render(<DesignPage model={model()} setModel={vi.fn()} catalog={engineeringCatalogFixture} catalogError={null} onNext={vi.fn()}/>);
    expect(screen.getByText(/已驗證外形上限：120 × 80 × 20 mm/)).toBeInTheDocument();
    expect(screen.getByText("megis-capability-manifest@1.0.0")).toBeInTheDocument();
    expect(screen.queryByText(/Synthetic demo data/)).not.toBeInTheDocument();
  });

  it("fails closed without a catalog and never invokes the submit handler", () => {
    const onNext = vi.fn();
    render(<DesignPage model={model()} setModel={vi.fn()} catalog={null} catalogError="無法連線至本機工程 API" onNext={onNext}/>);
    const next = screen.getByRole("button", { name: /建立並檢視 IR 草稿/i });
    expect(next).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent(/無法連線/);
    expect(onNext).not.toHaveBeenCalled();
  });

  it("posts an in-range request with the selected PCB envelope mode", async () => {
    const onNext = vi.fn().mockResolvedValue(undefined);
    render(<DesignPage model={model()} setModel={vi.fn()} catalog={engineeringCatalogFixture} catalogError={null} onNext={onNext}/>);
    fireEvent.click(screen.getByRole("button", { name: /建立並檢視 IR 草稿/i }));
    await waitFor(() => expect(onNext).toHaveBeenCalledWith("reference_only"));
  });

  it("blocks dimensions outside the verified envelope", () => {
    render(<DesignPage model={model({ width: 121 })} setModel={vi.fn()} catalog={engineeringCatalogFixture} catalogError={null} onNext={vi.fn()}/>);
    expect(screen.getByRole("button", { name: /建立並檢視 IR 草稿/i })).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent(/尺寸超過/);
  });

  it("requires acknowledgement and displays API correlation and unknowns", () => {
    const onRun = vi.fn();
    render(<ReviewPage draft={irDraftFixture} onBack={vi.fn()} onRun={onRun}/>);
    expect(screen.getByText("browser-test-1")).toBeInTheDocument();
    expect(screen.getByText("請提供 PCB 板框與孔位")).toBeInTheDocument();
    const run = screen.getByRole("button", { name: /檢視 IR 結果/i });
    expect(run).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox")); fireEvent.click(run);
    expect(onRun).toHaveBeenCalledOnce();
  });

  it("renders DRAFT IR without artifact downloads", () => {
    render(<ResultsPage draft={irDraftFixture} onRestart={vi.fn()}/>);
    expect(screen.getAllByText("DRAFT").length).toBeGreaterThan(0);
    expect(screen.getByText(/No engineering artifact generated/)).toBeInTheDocument();
    expect(screen.getByText(/沒有 STEP、圖面、BOM CSV/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /download/i })).not.toBeInTheDocument();
  });
});
