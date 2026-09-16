import type { DemoResult, PrototypeViewModel } from "../types/prototype";

export interface PrototypeAdapter {
  load(): PrototypeViewModel;
  save(model: PrototypeViewModel): void;
  createDemoResult(model: PrototypeViewModel): DemoResult;
}

const storageKey = "megis:ui0:prototype-view-model:0.1.0";

export const initialPrototypeModel: PrototypeViewModel = {
  schemaVersion: "0.1.0",
  designType: "fixture-enclosure",
  input: {
    width: 120,
    depth: 80,
    height: 35,
    pcbCount: 2,
    connector: "USB-C",
    fastener: "M3",
    cover: "removable",
    purpose: "固定兩片 PCB，供桌上測試與 USB-C 連接",
    quantity: "prototype",
    priority: "serviceability",
  },
  review: [],
};

function buildReview(model: PrototypeViewModel): PrototypeViewModel {
  const { input } = model;
  return {
    ...model,
    review: [
      { id: "outer-size", label: "外形尺寸", value: `${input.width} × ${input.depth} × ${input.height} mm`, provenance: "user" },
      { id: "pcb-count", label: "PCB 數量", value: `${input.pcbCount} 片`, provenance: "user" },
      { id: "interface", label: "外部介面", value: input.connector, provenance: "user" },
      { id: "material", label: "材料", value: "Aluminum 6061", provenance: "demo-default" },
      { id: "process", label: "製程", value: "3-axis CNC", provenance: "demo-default" },
      { id: "wall", label: "最小壁厚", value: "2 mm", provenance: "demo-default" },
      { id: "pcb-envelope", label: "PCB 詳細尺寸與安裝孔位", value: "Unknown — 進入真實生成前必須提供", provenance: "unknown", critical: true },
    ],
  };
}

export const browserPrototypeAdapter: PrototypeAdapter = {
  load() {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw) as PrototypeViewModel;
        if (parsed.schemaVersion === "0.1.0") return buildReview(parsed);
      }
    } catch {
      // Corrupt device-local prototype state falls back to a known fixture.
    }
    return buildReview(initialPrototypeModel);
  },
  save(model) {
    window.localStorage.setItem(storageKey, JSON.stringify(buildReview(model)));
  },
  createDemoResult(model) {
    const { input } = model;
    return {
      maturity: "UX PROTOTYPE",
      dimensions: `${input.width} × ${input.depth} × ${input.height} mm`,
      material: "Aluminum 6061",
      process: "3-axis CNC",
      checks: [
        { name: "Supported envelope", state: "demo-pass", note: "尺寸位於 50–300 mm demo 範圍內" },
        { name: "Minimum wall", state: "demo-pass", note: "展示值 2 mm；未執行 geometry validation" },
        { name: "PCB clearance", state: "needs-review", note: "缺少 PCB envelope 與安裝孔位" },
      ],
      bom: [
        { item: "Base — demo record", quantity: 1, note: "No CAD artifact" },
        { item: "Removable cover — demo record", quantity: 1, note: "No CAD artifact" },
        { item: "M3 fastener — demo record", quantity: 4, note: "Quantity is synthetic" },
      ],
    };
  },
};

