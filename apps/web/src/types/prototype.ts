export type Provenance = "user" | "demo-derived" | "demo-default" | "unknown";

export interface FixtureInput {
  width: number;
  depth: number;
  height: number;
  pcbCount: 1 | 2;
  connector: "USB-C";
  fastener: "M3";
  cover: "removable";
  purpose: string;
  quantity: "prototype" | "small-batch";
  priority: "machinability" | "compactness" | "serviceability";
}

export interface ReviewItem {
  id: string;
  label: string;
  value: string;
  provenance: Provenance;
  critical?: boolean;
}

export interface PrototypeViewModel {
  schemaVersion: "0.1.0";
  designType: "fixture-enclosure";
  input: FixtureInput;
  review: ReviewItem[];
}

