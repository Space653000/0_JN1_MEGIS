import { Box, ChevronRight, CircuitBoard, Info, Ruler, Settings2, Usb } from "lucide-react";
import type { PrototypeViewModel } from "../types/prototype";

interface Props { model: PrototypeViewModel; setModel: (model: PrototypeViewModel) => void; onNext: () => void; }

export function DesignPage({ model, setModel, onNext }: Props) {
  const input = model.input;
  const update = (next: Partial<typeof input>) => setModel({ ...model, input: { ...input, ...next } });
  return <>
    <section className="page-heading compact"><div><p className="eyebrow">引導式設計 · 第 1／3 步</p><h1>建立治具／電子外殼</h1><p>用日常語言描述需求；這個流程目前只會建立原型展示資料。</p></div><span className="prototype-badge">使用者體驗原型</span></section>
    <section className="wizard-grid">
      <div className="form-stack">
        <article className="panel form-card"><div className="section-title"><Box size={20} /><div><h2>外形與尺寸</h2><p>支援矩形、單腔、可拆上蓋的 UI 原型。</p></div></div><div className="dimension-grid">
          {(["width", "depth", "height"] as const).map((key) => <label key={key}><span>{key === "width" ? "寬度 W" : key === "depth" ? "深度 D" : "高度 H"}</span><div className="input-with-unit"><input type="number" min="50" max="300" value={input[key]} onChange={(event) => update({ [key]: Number(event.target.value) })} /><em>mm</em></div></label>)}
        </div><div className="range-note"><Ruler size={16} /> UI-0 支援的展示範圍：50–300 mm</div></article>
        <article className="panel form-card"><div className="section-title"><CircuitBoard size={20} /><div><h2>內部零件</h2><p>先決定零件種類；詳細外形範圍在真實生成前仍須提供。</p></div></div><div className="choice-row"><button className={`choice-card ${input.pcbCount === 1 ? "selected" : ""}`} onClick={() => update({ pcbCount: 1 })}><CircuitBoard size={21} /><strong>1 片 PCB</strong><span>單板配置</span></button><button className={`choice-card ${input.pcbCount === 2 ? "selected" : ""}`} onClick={() => update({ pcbCount: 2 })}><CircuitBoard size={21} /><strong>2 片 PCB</strong><span>參考案例</span></button><button className="choice-card selected"><Usb size={21} /><strong>USB-C</strong><span>外部開口</span></button></div></article>
        <article className="panel form-card"><div className="section-title"><Settings2 size={20} /><div><h2>使用情境</h2><p>這些答案會影響後續問題順序與建議。</p></div></div><label className="full-field"><span>用途</span><textarea value={input.purpose} onChange={(event) => update({ purpose: event.target.value })} rows={3} /></label><div className="field-grid"><label><span>預計數量</span><select value={input.quantity} onChange={(event) => update({ quantity: event.target.value as typeof input.quantity })}><option value="prototype">1–5 件原型</option><option value="small-batch">6–50 件小批量</option></select></label><label><span>優先目標</span><select value={input.priority} onChange={(event) => update({ priority: event.target.value as typeof input.priority })}><option value="serviceability">容易拆裝維修</option><option value="machinability">加工穩定</option><option value="compactness">體積緊湊</option></select></label></div></article>
      </div>
      <aside className="panel live-summary"><span className="panel-kicker">即時摘要</span><h2>參考治具</h2><div className="fixture-diagram" aria-label="矩形外殼示意圖"><svg viewBox="0 0 420 260" role="img"><title>矩形治具示意圖，不是 CAD</title><path d="M62 85 206 34l154 62-150 62Z"/><path d="M62 85v87l148 57 150-65V96"/><path d="m210 158 0 71M111 106l149 58 100-43"/><circle cx="101" cy="151" r="7"/><circle cx="315" cy="139" r="7"/></svg><span>示意圖 · 非 CAD</span></div><dl><div><dt>外形</dt><dd>{input.width} × {input.depth} × {input.height} mm</dd></div><div><dt>內容物</dt><dd>{input.pcbCount} 片 PCB + USB-C</dd></div><div><dt>緊固</dt><dd>M3／可拆上蓋</dd></div><div><dt>材料</dt><dd>6061 鋁合金 <small>展示預設</small></dd></div></dl><div className="info-note"><Info size={17} />尚未建立工程 IR 或幾何。</div><button className="primary-action" type="button" onClick={onNext}>檢視假設 <ChevronRight size={18} /></button></aside>
    </section>
  </>;
}
