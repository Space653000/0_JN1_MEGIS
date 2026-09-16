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
      { id: "material", label: "材料", value: "6061 鋁合金", provenance: "demo-default" },
      { id: "process", label: "製程", value: "三軸 CNC", provenance: "demo-default" },
      { id: "wall", label: "最小壁厚", value: "2 mm", provenance: "demo-default" },
      { id: "pcb-envelope", label: "PCB 詳細尺寸與安裝孔位", value: "未知——進入真實生成前必須提供", provenance: "unknown", critical: true },
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
      maturity: "使用者體驗原型",
      dimensions: `${input.width} × ${input.depth} × ${input.height} mm`,
      material: "6061 鋁合金",
      process: "三軸 CNC",
      checks: [
        { name: "支援的外形範圍", state: "demo-pass", note: "尺寸位於 50–300 mm 展示範圍內" },
        { name: "最小壁厚", state: "demo-pass", note: "展示值 2 mm；未執行幾何驗證" },
        { name: "PCB 間隙", state: "needs-review", note: "缺少 PCB 外形範圍與安裝孔位" },
      ],
      bom: [
        { item: "底座——展示記錄", quantity: 1, note: "未產生 CAD 製品" },
        { item: "可拆上蓋——展示記錄", quantity: 1, note: "未產生 CAD 製品" },
        { item: "M3 緊固件——展示記錄", quantity: 4, note: "數量為合成資料" },
      ],
    };
  },
};
