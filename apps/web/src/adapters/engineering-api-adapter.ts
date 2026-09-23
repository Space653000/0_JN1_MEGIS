import type { FixtureInput } from "../types/prototype";
import type { CapabilityManifest, EngineeringCatalog, EngineeringIrDraft, GuidedQuestion, IrDraftResponse } from "../types/guidance";

const REQUEST_TIMEOUT_MS = 5_000;

interface ErrorPayload {
  error?: { code?: string; user_message_zh_tw?: string; correlation_id?: string };
}

export class EngineeringApiError extends Error {
  constructor(message: string, readonly code = "MEGIS-SYS-002", readonly correlationId = "") {
    super(message);
    this.name = "EngineeringApiError";
  }
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(path, {
      cache: "no-store",
      ...init,
      signal: controller.signal,
      headers: { Accept: "application/json", ...init.headers },
    });
    if (!response.ok) {
      let payload: ErrorPayload = {};
      try { payload = await response.json() as ErrorPayload; } catch { /* fail closed below */ }
      throw new EngineeringApiError(
        payload.error?.user_message_zh_tw ?? `本機工程 API 回應失敗（HTTP ${response.status}）。`,
        payload.error?.code,
        payload.error?.correlation_id,
      );
    }
    return response;
  } catch (error) {
    if (error instanceof EngineeringApiError) throw error;
    throw new EngineeringApiError("無法連線至本機工程 API；未建立 IR，也不會退回合成資料。", "MEGIS-SYS-002");
  } finally {
    window.clearTimeout(timer);
  }
}

export const localEngineeringApi = {
  async loadCatalog(): Promise<EngineeringCatalog> {
    const [manifestResponse, questionsResponse] = await Promise.all([
      request("/api/v1/capabilities"),
      request("/api/v1/questions"),
    ]);
    const manifest = await manifestResponse.json() as CapabilityManifest;
    const questionDocument = await questionsResponse.json() as { questions: GuidedQuestion[] };
    return { manifest, questions: questionDocument.questions };
  },

  async createIrDraft(input: FixtureInput, pcbEnvelopeMode: "reference_only" | "provided" | "unknown"): Promise<IrDraftResponse> {
    const correlationId = `g6ui2-browser-${Date.now().toString(36)}`;
    const response = await request("/api/v1/ir-drafts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Correlation-ID": correlationId,
      },
      body: JSON.stringify({
        width_mm: input.width,
        depth_mm: input.depth,
        height_mm: input.height,
        pcb_count: input.pcbCount,
        connector: input.connector,
        fastener: input.fastener,
        cover: input.cover,
        quantity: input.quantity,
        priority: input.priority,
        purpose: input.purpose,
        pcb_envelope_mode: pcbEnvelopeMode,
        pcb_required: false,
      }),
    });
    return {
      document: await response.json() as EngineeringIrDraft,
      correlationId: response.headers.get("X-Correlation-ID") ?? correlationId,
      contentSha256: response.headers.get("X-Content-SHA256") ?? "unavailable",
    };
  },
};
