export interface CapabilityEnvelope {
  envelopeId: string;
  label: string;
  verified: true;
  outerDimensionsMm: { widthMm: number; depthMm: number; heightMm: number };
  minimumWallMm: number;
  materials: string[];
  machining: string[];
  fixture: { coverCount: number; fastenerCount: number };
  unsupportedErrorCodes: string[];
}

export interface CapabilityManifest {
  schemaVersion: "1.0.0";
  corpusId: string;
  designTypes: Array<{ id: string; label: string; proven: true }>;
  geometry: {
    backendId: string;
    backendVersion: string;
    deterministic: true;
    operations: Array<{ id: string; proven: true }>;
    exportFormats: string[];
  };
  modules: { capabilityLevels: Array<{ level: string; uiDisplay: string; layoutAllowed: boolean; geometryAllowed: boolean; maturityCap: string; proven: true }> };
  relationships: Array<{ type: string; meaning: string; requiredParameters: string[]; proven: true }>;
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

export interface EngineeringIrDraft {
  schemaVersion: "2.0.0";
  designId: string;
  revision: string;
  maturity: "DRAFT" | "CONCEPT" | "PROTOTYPE" | "ENGINEERING_REVIEWED" | "RELEASED";
  requirements: Array<{ id: string; statement: string; priority: string }>;
  components: Array<{ id: string; name: string; componentType: string; dimensions: Array<{ name: string; quantity: { nominal?: number; unit: string } }> }>;
  assumptions: Array<{ id: string; field: string; status: string; rationale: string }>;
  unknowns: Array<{ id: string; field: string; unsafeToDefault: boolean; question: string }>;
  [key: string]: unknown;
}

export interface EngineeringCatalog {
  manifest: CapabilityManifest;
  questions: GuidedQuestion[];
}

export interface IrDraftResponse {
  document: EngineeringIrDraft;
  correlationId: string;
  contentSha256: string;
}
