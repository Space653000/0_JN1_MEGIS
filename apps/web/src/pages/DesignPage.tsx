import { Box, ChevronRight, CircuitBoard, Info, Ruler, Settings2, ShieldAlert, Usb } from "lucide-react";
import { useState } from "react";
import { demoCapabilityGuideAdapter } from "../adapters/capability-guide-adapter";
import type { CapabilityGuideAdapter } from "../types/guidance";
import type { PrototypeViewModel } from "../types/prototype";

interface Props { model: PrototypeViewModel; setModel: (model: PrototypeViewModel) => void; onNext: () => void; guide?: CapabilityGuideAdapter; }

const quantityLabel: Record<string, string> = { prototype: "1–5 件原型", "small-batch": "6–50 件小批量" };
const priorityLabel: Record<string, string> = { serviceability: "容易拆裝維修", machinability: "加工穩定", compactness: "體積緊湊" };
const pcbModeLabel: Record<string, string> = { reference_only: "參考案例（未驗證）", provided: "已提供外形範圍", unknown: "不知道，交由系統建議" };

export function DesignPage({ model, setModel, onNext, guide = demoCapabilityGuideAdapter }: Props) {
  const manifest = guide.loadManifest();
  const questions = guide.loadQuestions();
  const [pcbEnvelopeMode, setPcbEnvelopeMode] = useState<"reference_only" | "provided" | "unknown">("reference_only");
  const input = model.input;

  const update = (next: Partial<typeof input>) => setModel({ ...model, input: { ...input, ...next } });

  const envelope = manifest.envelope.outerDimensionsMm;
  const dimensionQuestion = Object.fromEntries(questions.map((question) => [question.id, question]));
  const pcbEnvelopeQuestion = questions.find((question) => question.id === "Q-FIXTURE-PCB-ENVELOPE");

  const draft = guide.buildIrDraft({
    widthMm: Number.isFinite(Number(input.width)) ? Number(input.width) : null,
    depthMm: Number.isFinite(Number(input.depth)) ? Number(input.depth) : null,
    heightMm: Number.isFinite(Number(input.height)) ? Number(input.height) : null,
    pcbCount: input.pcbCount,
    connector: input.connector,
    fastener: input.fastener,
    cover: input.cover,
    quantity: input.quantity,
    priority: input.priority,
    purpose: input.purpose,
    pcbEnvelopeMode,
  });
  const blocked = draft.blockReason !== null;

  return <>
    <section className="page-heading compact"><div><p className="eyebrow">引導式設計 · 第 1／3 步</p><h1>建立治具／電子外殼</h1><p>只顯示已證明的能力；未確認的關鍵項目會被標記，不會自行猜測。</p></div><span className="prototype-badge">UI-0 原型 · 合成展示</span></section>
    <section className="wizard-grid">
      <div className="form-stack">
        <article className="panel form-card"><div className="section-title"><Box size={20} /><div><h2>外形與尺寸</h2><p>支援矩形、單腔、可拆上蓋；寬高深上限取自已驗證範圍。</p></div></div><div className="dimension-grid">
          {([["width", "widthMm", "寬度 W"], ["depth", "depthMm", "深度 D"], ["height", "heightMm", "高度 H"]] as const).map(([key, envKey, label]) => <label key={key}><span>{label}</span><div className="input-with-unit"><input aria-label={label} type="number" min="0" max={envelope[envKey]} value={input[key]} onChange={(event) => { const value = Number(event.target.value); update({ [key]: Number.isFinite(value) ? value : 0 }); }} /><em>mm</em></div></label>)}
        </div><div className={`range-note ${draft.blockReason ? "danger" : ""}`}><Ruler size={16} /> 已驗證外形上限：{envelope.widthMm} × {envelope.depthMm} × {envelope.heightMm} mm</div></article>
        <article className="panel form-card"><div className="section-title"><CircuitBoard size={20} /><div><h2>內部零件</h2><p>選項只來自後端已證明的能力清單。</p></div></div><div className="choice-row">
          <button type="button" className={`choice-card ${input.pcbCount === 1 ? "selected" : ""}`} onClick={() => update({ pcbCount: 1 })}><CircuitBoard size={21} /><strong>1 片 PCB</strong><span>單板配置</span></button>
          <button type="button" className={`choice-card ${input.pcbCount === 2 ? "selected" : ""}`} onClick={() => update({ pcbCount: 2 })}><CircuitBoard size={21} /><strong>2 片 PCB</strong><span>參考案例</span></button>
          <button type="button" className="choice-card selected" onClick={() => update({ connector: "USB-C" })}><Usb size={21} /><strong>USB-C</strong><span>外部開口</span></button>
        </div></article>
        <article className="panel form-card"><div className="section-title"><Settings2 size={20} /><div><h2>使用情境</h2><p>這些答案會影響後續問題順序與建議。</p></div></div><label className="full-field"><span>{dimensionQuestion["Q-FIXTURE-PURPOSE"].label}</span><textarea value={input.purpose} onChange={(event) => update({ purpose: event.target.value })} rows={3} /></label><div className="field-grid"><label><span>預計數量</span><select value={input.quantity} onChange={(event) => update({ quantity: event.target.value as typeof input.quantity })}>{Object.entries(quantityLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label><span>優先目標</span><select value={input.priority} onChange={(event) => update({ priority: event.target.value as typeof input.priority })}>{Object.entries(priorityLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div></article>
        <article className={`panel form-card ${pcbEnvelopeMode === "unknown" ? "review-card" : ""}`}><div className="section-title"><ShieldAlert size={20} /><div><h2>PCB 外形範圍</h2><p>{pcbEnvelopeQuestion?.help}</p></div></div><label className="full-field"><span>目前狀態</span><select value={pcbEnvelopeMode} onChange={(event) => setPcbEnvelopeMode(event.target.value as typeof pcbEnvelopeMode)}>{Object.entries(pcbModeLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{pcbEnvelopeMode === "unknown" ? <div className="info-note danger"><ShieldAlert size={17} />關鍵未知項目不會消失；選擇「不知道」會阻擋建立草稿。</div> : <div className="info-note"><Info size={17} />選擇「參考案例」時，PCB 詳細尺寸會保留為待確認問題。</div>}</article>
      </div>
      <aside className="panel live-summary"><span className="panel-kicker">即時摘要</span><h2>參考治具</h2><div className="fixture-diagram" aria-label="矩形外殼示意圖"><svg viewBox="0 0 420 260" role="img"><title>矩形治具示意圖，不是 CAD</title><path d="M62 85 206 34l154 62-150 62Z"/><path d="M62 85v87l148 57 150-65V96"/><path d="m210 158 0 71M111 106l149 58 100-43"/><circle cx="101" cy="151" r="7"/><circle cx="315" cy="139" r="7"/></svg><span>示意圖 · 非 CAD</span></div><dl><div><dt>外形</dt><dd>{input.width} × {input.depth} × {input.height} mm</dd></div><div><dt>內容物</dt><dd>{input.pcbCount} 片 PCB + USB-C</dd></div><div><dt>緊固</dt><dd>M3／可拆上蓋</dd></div><div><dt>材料</dt><dd>6061 鋁合金 <small>展示預設</small></dd></div></dl>
        {blocked ? <div className="info-note danger"><ShieldAlert size={17} />{draft.blockReason}</div> : <div className="info-note"><Info size={17} />合成 IR 草稿可用 · Synthetic demo data，未產生工程製品。</div>}
        <button className="primary-action" type="button" disabled={blocked} onClick={onNext}>檢視假設 <ChevronRight size={18} /></button>
      </aside>
    </section>
  </>;
}
