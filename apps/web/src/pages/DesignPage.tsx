import { Box, ChevronRight, CircuitBoard, Info, Ruler, Settings2, ShieldAlert, Usb } from "lucide-react";
import { useState } from "react";
import { EngineeringApiError } from "../adapters/engineering-api-adapter";
import type { EngineeringCatalog } from "../types/guidance";
import type { PrototypeViewModel } from "../types/prototype";

type PcbEnvelopeMode = "reference_only" | "provided" | "unknown";
interface Props { model: PrototypeViewModel; setModel: (model: PrototypeViewModel) => void; catalog: EngineeringCatalog | null; catalogError: string | null; onNext: (mode: PcbEnvelopeMode) => Promise<void>; }
const quantityLabel: Record<string, string> = { prototype: "1–5 件原型", "small-batch": "6–50 件小批量" };
const priorityLabel: Record<string, string> = { serviceability: "容易拆裝維修", machinability: "加工穩定", compactness: "體積緊湊" };
const pcbModeLabel: Record<PcbEnvelopeMode, string> = { reference_only: "參考案例（未驗證）", provided: "已提供外形範圍", unknown: "不知道，交由系統建議" };

export function DesignPage({ model, setModel, catalog, catalogError, onNext }: Props) {
  const [pcbEnvelopeMode, setPcbEnvelopeMode] = useState<PcbEnvelopeMode>("reference_only");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const input = model.input;
  const update = (next: Partial<typeof input>) => setModel({ ...model, input: { ...input, ...next } });
  const envelope = catalog?.manifest.envelope.outerDimensionsMm;
  const purposeQuestion = catalog?.questions.find((question) => question.id === "Q-FIXTURE-PURPOSE");
  const pcbEnvelopeQuestion = catalog?.questions.find((question) => question.id === "Q-FIXTURE-PCB-ENVELOPE");
  const outsideEnvelope = Boolean(envelope && (input.width > envelope.widthMm || input.depth > envelope.depthMm || input.height > envelope.heightMm));
  const blockReason = catalogError ?? (!catalog ? "正在讀取本機工程 API 能力清單。" : null) ?? (outsideEnvelope ? `尺寸超過已驗證外形上限：${envelope?.widthMm} × ${envelope?.depthMm} × ${envelope?.heightMm} mm。` : null) ?? (pcbEnvelopeMode === "unknown" ? "PCB 外形範圍尚未確認；關鍵未知項目不可由系統猜測。" : null);
  const submit = async () => {
    if (blockReason) return;
    setSubmitting(true); setSubmitError(null);
    try { await onNext(pcbEnvelopeMode); }
    catch (error) { setSubmitError(error instanceof EngineeringApiError ? error.message : "建立 IR 草稿失敗；未產生任何工程製品。"); }
    finally { setSubmitting(false); }
  };
  return <>
    <section className="page-heading compact"><div><p className="eyebrow">引導式設計 · 第 1／3 步</p><h1>建立治具／電子外殼 IR 草稿</h1><p>能力範圍與問題由本機工程 API 提供；連線失敗時會停止，不會退回合成資料。</p></div><span className="prototype-badge">本機工程 API · DRAFT IR</span></section>
    <section className="wizard-grid"><div className="form-stack">
      <article className="panel form-card"><div className="section-title"><Box size={20}/><div><h2>外形與尺寸</h2><p>支援矩形、單腔、可拆上蓋；上限取自後端 capability manifest。</p></div></div><div className="dimension-grid">{([['width','widthMm','寬度 W'],['depth','depthMm','深度 D'],['height','heightMm','高度 H']] as const).map(([key,envKey,label]) => <label key={key}><span>{label}</span><div className="input-with-unit"><input aria-label={label} type="number" min="0" max={envelope?.[envKey]} value={input[key]} onChange={(event) => update({ [key]: Number(event.target.value) || 0 })}/><em>mm</em></div></label>)}</div><div className={`range-note ${outsideEnvelope ? "danger" : ""}`}><Ruler size={16}/>{envelope ? `已驗證外形上限：${envelope.widthMm} × ${envelope.depthMm} × ${envelope.heightMm} mm` : "等待本機 API 能力範圍"}</div></article>
      <article className="panel form-card"><div className="section-title"><CircuitBoard size={20}/><div><h2>內部零件</h2><p>目前 manifest 證明 1–2 片 PCB、USB-C、M3 與可拆上蓋。</p></div></div><div className="choice-row" role="group" aria-label="內部零件選擇"><button type="button" aria-pressed={input.pcbCount === 1} className={`choice-card ${input.pcbCount === 1 ? "selected" : ""}`} onClick={() => update({ pcbCount: 1 })}><CircuitBoard size={21}/><strong>1 片 PCB</strong><span>單板配置</span></button><button type="button" aria-pressed={input.pcbCount === 2} className={`choice-card ${input.pcbCount === 2 ? "selected" : ""}`} onClick={() => update({ pcbCount: 2 })}><CircuitBoard size={21}/><strong>2 片 PCB</strong><span>雙板配置</span></button><button type="button" aria-pressed={input.connector === "USB-C"} className="choice-card selected" onClick={() => update({ connector: "USB-C" })}><Usb size={21}/><strong>USB-C</strong><span>外部開口</span></button></div></article>
      <article className="panel form-card"><div className="section-title"><Settings2 size={20}/><div><h2>使用情境</h2><p>答案會直接送入版本化 IR 草稿契約。</p></div></div><label className="full-field"><span>{purposeQuestion?.label ?? "設計用途"}</span><textarea value={input.purpose} onChange={(event) => update({ purpose: event.target.value })} rows={3}/></label><div className="field-grid"><label><span>預計數量</span><select value={input.quantity} onChange={(event) => update({ quantity: event.target.value as typeof input.quantity })}>{Object.entries(quantityLabel).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label><label><span>優先目標</span><select value={input.priority} onChange={(event) => update({ priority: event.target.value as typeof input.priority })}>{Object.entries(priorityLabel).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label></div></article>
      <article className={`panel form-card ${pcbEnvelopeMode === "unknown" ? "review-card" : ""}`}><div className="section-title"><ShieldAlert size={20}/><div><h2>PCB 外形範圍</h2><p>{pcbEnvelopeQuestion?.help ?? "由本機 API 載入此問題。"}</p></div></div><label className="full-field"><span>目前狀態</span><select value={pcbEnvelopeMode} onChange={(event) => setPcbEnvelopeMode(event.target.value as PcbEnvelopeMode)}>{Object.entries(pcbModeLabel).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label>{pcbEnvelopeMode === "unknown" ? <div className="info-note danger"><ShieldAlert size={17}/>關鍵未知項目不會消失，也不會自動填入。</div> : <div className="info-note"><Info size={17}/>詳細板框、孔位與禁佈區仍會保留為待確認項目。</div>}</article>
    </div><aside className="panel live-summary"><span className="panel-kicker">送出摘要</span><h2>DRAFT IR</h2><div className="fixture-diagram" aria-label="矩形外殼示意圖"><svg viewBox="0 0 420 260" role="img"><title>矩形治具示意圖，不是 CAD</title><path d="M62 85 206 34l154 62-150 62Z"/><path d="M62 85v87l148 57 150-65V96"/></svg><span>示意圖 · 非 CAD</span></div><dl><div><dt>外形</dt><dd>{input.width} × {input.depth} × {input.height} mm</dd></div><div><dt>內容物</dt><dd>{input.pcbCount} 片 PCB + USB-C</dd></div><div><dt>緊固</dt><dd>M3／可拆上蓋</dd></div><div><dt>資料來源</dt><dd>{catalog ? catalog.manifest.corpusId : "尚未連線"}</dd></div></dl>{blockReason ? <div className="info-note danger" role="alert"><ShieldAlert size={17}/>{blockReason}</div> : <div className="info-note"><Info size={17}/>API 已就緒；下一步建立真實 DRAFT IR，但不執行 CAD、規則或封裝。</div>}{submitError && <div className="info-note danger" role="alert"><ShieldAlert size={17}/>{submitError}</div>}<button className="primary-action" type="button" disabled={Boolean(blockReason) || submitting} onClick={submit}>{submitting ? "建立中…" : "建立並檢視 IR 草稿"}<ChevronRight size={18}/></button></aside></section>
  </>;
}
