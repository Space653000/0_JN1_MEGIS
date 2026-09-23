import type { EngineeringCatalog, IrDraftResponse } from "./types/guidance";

export const engineeringCatalogFixture: EngineeringCatalog = {
  manifest: {
    schemaVersion: "1.0.0",
    corpusId: "megis-capability-manifest@1.0.0",
    designTypes: [{ id: "fixture-enclosure", label: "治具／電子外殼", proven: true }],
    geometry: { backendId: "cadquery", backendVersion: "2.8.0", deterministic: true, operations: [{ id: "box", proven: true }], exportFormats: ["STEP"] },
    modules: { capabilityLevels: [] }, relationships: [],
    envelope: { envelopeId: "fixture", label: "Fixture", verified: true, outerDimensionsMm: { widthMm: 120, depthMm: 80, heightMm: 20 }, minimumWallMm: 2, materials: ["AL6061"], machining: ["3-axis CNC"], fixture: { coverCount: 1, fastenerCount: 4 }, unsupportedErrorCodes: ["MEGIS-ENV-001"] },
    confidenceLabels: ["Verified", "Unknown"], maturityTiers: ["DRAFT", "CONCEPT", "PROTOTYPE", "ENGINEERING_REVIEWED", "RELEASED"], manifestFingerprint: "a".repeat(64),
  },
  questions: [
    { id: "Q-FIXTURE-PURPOSE", irField: "/requirements/0/statement", label: "設計用途", help: "說明治具用途。", inputKind: "text", envelopeRange: null, options: [], unsafeToDefault: false },
    { id: "Q-FIXTURE-PCB-ENVELOPE", irField: "/components/pcb", label: "PCB 外形", help: "提供板框、孔位及禁佈區。", inputKind: "choice", envelopeRange: null, options: ["reference_only", "provided", "unknown"], unsafeToDefault: true },
  ],
};

export const irDraftFixture: IrDraftResponse = {
  correlationId: "browser-test-1",
  contentSha256: "b".repeat(64),
  document: {
    schemaVersion: "2.0.0", designId: "FIXTURE-GUIDED-001", revision: "A", maturity: "DRAFT",
    requirements: [{ id: "REQ-001", statement: "桌上測試治具", priority: "must" }],
    components: [{ id: "fixture_base", name: "Fixture base", componentType: "fixture", dimensions: [{ name: "width", quantity: { nominal: 120, unit: "mm" } }] }],
    assumptions: [{ id: "ASM-001", field: "material", status: "proposed", rationale: "候選材料，尚未驗證" }],
    unknowns: [{ id: "UNK-001", field: "pcb_envelope", unsafeToDefault: true, question: "請提供 PCB 板框與孔位" }],
  },
};
