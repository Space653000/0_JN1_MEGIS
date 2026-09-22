import type {
  CapabilityGuideAdapter,
  CapabilityManifest,
  GuidedAnswers,
  GuidedFlowResult,
  GuidedQuestion,
} from "../types/guidance";

const ENVELOPE = {
  envelopeId: "legacy-reference-fixture",
  outerDimensionsMm: { widthMm: 120, depthMm: 80, heightMm: 20 },
  minimumWallMm: 2,
  materials: ["AL6061"],
  machining: ["3-axis CNC"],
  fixture: { coverCount: 1, fastenerCount: 4 },
};

const DEMO_MANIFEST: CapabilityManifest = {
  schemaVersion: "1.0.0",
  corpusId: "megis-capability-manifest@1.0.0",
  dataScope: "synthetic-demo",
  designTypes: [{ id: "fixture-enclosure", label: "治具／電子外殼", proven: true }],
  operations: [
    { id: "box", proven: true },
    { id: "counterbore", proven: true },
    { id: "cutout", proven: true },
    { id: "fastener", proven: true },
    { id: "hole", proven: true },
    { id: "mount", proven: true },
    { id: "pcb_envelope", proven: true },
    { id: "plate", proven: true },
    { id: "shell", proven: true },
  ],
  envelope: ENVELOPE,
  confidenceLabels: ["Verified", "Supported", "Partially supported", "Unknown", "Needs engineering review"],
  maturityTiers: ["DRAFT", "CONCEPT", "PROTOTYPE", "ENGINEERING_REVIEWED", "RELEASED"],
  manifestFingerprint: "7bfc576a849ac31998cdb1cc33a92af4b3f200e1c346482fb7adab2c2342ca25",
};

const GUIDED_QUESTIONS: GuidedQuestion[] = [
  { id: "Q-FIXTURE-WIDTH", irField: "/components[fixture_base]/dimensions/width/nominal", label: "外形的寬度 W 是多少？", help: "寬度是治具左右兩側的距離，單位公釐（mm）。", inputKind: "number", envelopeRange: { maxMm: 120 }, options: [], unsafeToDefault: false },
  { id: "Q-FIXTURE-DEPTH", irField: "/components[fixture_base]/dimensions/depth/nominal", label: "外形的深度 D 是多少？", help: "深度是治具前後兩側的距離，單位公釐（mm）。", inputKind: "number", envelopeRange: { maxMm: 80 }, options: [], unsafeToDefault: false },
  { id: "Q-FIXTURE-HEIGHT", irField: "/components[fixture_base]/dimensions/height/nominal", label: "外形的總高度 H 是多少？", help: "高度是治具底部到頂面的距離，單位公釐（mm）。", inputKind: "number", envelopeRange: { maxMm: 20 }, options: [], unsafeToDefault: false },
  { id: "Q-FIXTURE-PCB-COUNT", irField: "/components[pcb]/count", label: "內部要放幾片 PCB？", help: "PCB 是印刷電路板，參考案例支援 1 或 2 片。", inputKind: "choice", envelopeRange: { minMm: 1, maxMm: 2 }, options: ["1", "2"], unsafeToDefault: false },
  { id: "Q-FIXTURE-CONNECTOR", irField: "/interfaces[usb]/interfaceType", label: "需要哪一種外部介面開口？", help: "目前只支援 USB-C 開口。", inputKind: "choice", envelopeRange: null, options: ["USB-C"], unsafeToDefault: false },
  { id: "Q-FIXTURE-FASTENER", irField: "/relationships[fastens]/fastenerSize", label: "外殼使用哪一種緊固件？", help: "緊固件是把上蓋固定在底座上的螺絲，目前支援 M3。", inputKind: "choice", envelopeRange: null, options: ["M3"], unsafeToDefault: false },
  { id: "Q-FIXTURE-COVER", irField: "/components[cover]/removability", label: "上蓋需要可拆嗎？", help: "可拆上蓋方便維修與更換內部零件。", inputKind: "choice", envelopeRange: null, options: ["removable"], unsafeToDefault: false },
  { id: "Q-FIXTURE-QUANTITY", irField: "/requirements[quantity]/value", label: "預計製作多少件？", help: "原型數量影響製程選擇與單價。", inputKind: "choice", envelopeRange: null, options: ["prototype", "small-batch"], unsafeToDefault: false },
  { id: "Q-FIXTURE-PRIORITY", irField: "/requirements[priority]/value", label: "你最重視哪一個目標？", help: "目標會影響問題順序與建議方向。", inputKind: "choice", envelopeRange: null, options: ["serviceability", "machinability", "compactness"], unsafeToDefault: false },
  { id: "Q-FIXTURE-PURPOSE", irField: "/requirements[0]/statement", label: "用途是一句話描述這個治具要做什麼？", help: "用途會寫進工程需求。", inputKind: "text", envelopeRange: null, options: [], unsafeToDefault: false },
  { id: "Q-FIXTURE-PCB-ENVELOPE", irField: "/unknowns[pcb_envelope]/question", label: "PCB 的外形範圍已經確認了嗎？", help: "若尚未確認，系統不會自行假設尺寸。", inputKind: "choice", envelopeRange: null, options: ["reference_only", "provided", "unknown"], unsafeToDefault: true },
];

const DESIGN_ID = "FIXTURE-GUIDED-001";
const ALLOWED_CONNECTORS = new Set(["USB-C"]);
const ALLOWED_FASTENERS = new Set(["M3"]);
const ALLOWED_COVERS = new Set(["removable"]);
const ALLOWED_QUANTITIES = new Set(["prototype", "small-batch"]);
const ALLOWED_PRIORITIES = new Set(["serviceability", "machinability", "compactness"]);

function fnv1a(value: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function canonicalAnswers(answers: GuidedAnswers): string {
  return JSON.stringify({
    w: answers.widthMm,
    d: answers.depthMm,
    h: answers.heightMm,
    p: answers.pcbCount,
    c: answers.connector,
    f: answers.fastener,
    v: answers.cover,
    q: answers.quantity,
    r: answers.priority,
    u: answers.purpose.trim(),
    e: answers.pcbEnvelopeMode,
  });
}

function blockResult(reason: string, unknowns: string[] = []): GuidedFlowResult {
  return {
    kind: "synthetic-draft",
    schemaVersion: "1.0.0",
    designId: DESIGN_ID,
    dataScope: "synthetic-demo",
    syntheticDemo: true,
    engineeringArtifactGenerated: false,
    blockReason: reason,
    draftFingerprint: null,
    assumptions: [],
    unknowns,
  };
}

export const demoCapabilityGuideAdapter: CapabilityGuideAdapter = {
  manifest: DEMO_MANIFEST,
  loadManifest() {
    return DEMO_MANIFEST;
  },
  loadQuestions() {
    return GUIDED_QUESTIONS.map((question) => ({ ...question, options: [...question.options] }));
  },
  buildIrDraft(answers: GuidedAnswers): GuidedFlowResult {
    const { widthMm, depthMm, heightMm } = answers;
    if (widthMm === null || depthMm === null || heightMm === null) {
      return blockResult("缺少不安全的尺寸：系統不會自行假設。", ["/components[fixture_base]/dimensions"]);
    }
    if (widthMm > ENVELOPE.outerDimensionsMm.widthMm ||
        depthMm > ENVELOPE.outerDimensionsMm.depthMm ||
        heightMm > ENVELOPE.outerDimensionsMm.heightMm) {
      return blockResult("外形超出已驗證範圍（120 × 80 × 20 mm）。");
    }
    if (answers.pcbEnvelopeMode === "unknown") {
      return blockResult("PCB 外形範圍尚未確認；關鍵未知項目不會被自動填入。", ["/unknowns[pcb_envelope]/question"]);
    }
    if (!ALLOWED_CONNECTORS.has(answers.connector) ||
        !ALLOWED_FASTENERS.has(answers.fastener) ||
        !ALLOWED_COVERS.has(answers.cover) ||
        !ALLOWED_QUANTITIES.has(answers.quantity) ||
        !ALLOWED_PRIORITIES.has(answers.priority) ||
        (answers.pcbCount !== 1 && answers.pcbCount !== 2)) {
      return blockResult("要求的能力超出已驗證範圍。");
    }
    const fingerprint = `${fnv1a(canonicalAnswers(answers))}${fnv1a(DEMO_MANIFEST.manifestFingerprint)}`;
    return {
      kind: "synthetic-draft",
      schemaVersion: "1.0.0",
      designId: DESIGN_ID,
      dataScope: "synthetic-demo",
      syntheticDemo: true,
      engineeringArtifactGenerated: false,
      blockReason: null,
      draftFingerprint: fingerprint,
      assumptions: ["三軸 CNC 固定裝夾", "最小壁厚 2 mm", "6061 鋁合金"],
      unknowns: answers.pcbEnvelopeMode === "reference_only"
        ? ["PCB 詳細尺寸與安裝孔位"]
        : [],
    };
  },
};
