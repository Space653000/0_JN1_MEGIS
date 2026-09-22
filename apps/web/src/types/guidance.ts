export type DemoScope = "synthetic-demo";

export interface CapabilityEnvelope {
  envelopeId: string;
  outerDimensionsMm: { widthMm: number; depthMm: number; heightMm: number };
  minimumWallMm: number;
  materials: string[];
  machining: string[];
  fixture: { coverCount: number; fastenerCount: number };
}

export interface CapabilityManifest {
  schemaVersion: "1.0.0";
  corpusId: string;
  dataScope: DemoScope;
  designTypes: Array<{ id: string; label: string; proven: true }>;
  operations: Array<{ id: string; proven: true }>;
  envelope: CapabilityEnvelope;
  confidenceLabels: string[];
  maturityTiers: string[];
  manifestFingerprint: string;
}

export interface GuidedQuestion {
  id: string;
  irField: string;
  label: string;
  help: string;
  inputKind: "number" | "choice" | "text";
  envelopeRange: { maxMm?: number; minMm?: number } | null;
  options: string[];
  unsafeToDefault: boolean;
}

export interface GuidedAnswers {
  widthMm: number | null;
  depthMm: number | null;
  heightMm: number | null;
  pcbCount: 1 | 2;
  connector: string;
  fastener: string;
  cover: string;
  quantity: string;
  priority: string;
  purpose: string;
  pcbEnvelopeMode: "reference_only" | "provided" | "unknown";
}

export interface GuidedFlowResult {
  kind: "synthetic-draft";
  schemaVersion: "1.0.0";
  designId: string;
  dataScope: DemoScope;
  syntheticDemo: true;
  engineeringArtifactGenerated: false;
  blockReason: string | null;
  draftFingerprint: string | null;
  assumptions: string[];
  unknowns: string[];
}

export interface CapabilityGuideAdapter {
  readonly manifest: CapabilityManifest;
  loadManifest(): CapabilityManifest;
  loadQuestions(): GuidedQuestion[];
  buildIrDraft(answers: GuidedAnswers): GuidedFlowResult;
}
