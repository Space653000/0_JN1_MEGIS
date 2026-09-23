import { afterEach, describe, expect, it, vi } from "vitest";

import { initialPrototypeModel } from "./prototype-adapter";
import { EngineeringApiError, localEngineeringApi } from "./engineering-api-adapter";

const manifest = {
  schemaVersion: "1.0.0",
  corpusId: "megis-capability-manifest@1.0.0",
  designTypes: [{ id: "fixture-enclosure", label: "治具／電子外殼", proven: true }],
  geometry: { backendId: "cadquery", backendVersion: "2.8.0", deterministic: true, operations: [{ id: "box", proven: true }], exportFormats: ["STEP"] },
  modules: { capabilityLevels: [] },
  relationships: [],
  envelope: { envelopeId: "fixture", label: "Fixture", verified: true, outerDimensionsMm: { widthMm: 120, depthMm: 80, heightMm: 20 }, minimumWallMm: 2, materials: ["AL6061"], machining: ["3-axis CNC"], fixture: { coverCount: 1, fastenerCount: 4 }, unsupportedErrorCodes: ["MEGIS-ENV-001"] },
  confidenceLabels: ["Verified", "Supported", "Partially supported", "Unknown", "Needs engineering review"],
  maturityTiers: ["DRAFT", "CONCEPT", "PROTOTYPE", "ENGINEERING_REVIEWED", "RELEASED"],
  manifestFingerprint: "a".repeat(64),
} as const;

const questions = { schemaVersion: "1.0.0", questions: [{ id: "Q-FIXTURE-PURPOSE", irField: "/requirements/0/statement", label: "用途", help: "用途", inputKind: "text", envelopeRange: null, options: [], unsafeToDefault: false }] };
const draft = { schemaVersion: "2.0.0", designId: "FIXTURE-GUIDED-001", revision: "A", maturity: "DRAFT", assumptions: [], unknowns: [], components: [], requirements: [] } as const;

afterEach(() => vi.unstubAllGlobals());

describe("real engineering HTTP adapter", () => {
  it("loads backend capability and questions without a synthetic fallback", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(manifest), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(questions), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    const catalog = await localEngineeringApi.loadCatalog();

    expect(catalog.manifest.corpusId).toBe("megis-capability-manifest@1.0.0");
    expect(catalog.questions).toHaveLength(1);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/v1/capabilities", expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/questions", expect.any(Object));
  });

  it("posts the UI state to the canonical IR endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(draft), { status: 200, headers: { "Content-Type": "application/json", "X-Correlation-ID": "browser-1", "X-Content-SHA256": "b".repeat(64) } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await localEngineeringApi.createIrDraft(initialPrototypeModel.input, "reference_only");

    expect(result.document.maturity).toBe("DRAFT");
    expect(result.correlationId).toBe("browser-1");
    expect(result.contentSha256).toBe("b".repeat(64));
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/ir-drafts", expect.objectContaining({ method: "POST" }));
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body).toMatchObject({ width_mm: 120, pcb_count: 2, pcb_envelope_mode: "reference_only" });
  });

  it("fails closed when the API is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("connection refused")));

    await expect(localEngineeringApi.loadCatalog()).rejects.toBeInstanceOf(EngineeringApiError);
  });
});
