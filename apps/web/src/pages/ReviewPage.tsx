import { AlertOctagon, ArrowLeft, ChevronRight, CircleHelp, Database } from "lucide-react";
import { useState } from "react";
import type { IrDraftResponse } from "../types/guidance";

export function ReviewPage({ draft, onBack, onRun }: { draft: IrDraftResponse | null; onBack: () => void; onRun: () => void }) {
  const [acknowledged, setAcknowledged] = useState(false);
  if (!draft) return <section className="panel acknowledge-card"><h1>尚未建立 IR 草稿</h1><p>請先由設計工作台連線本機工程 API 並建立草稿。</p><button className="secondary-action" onClick={onBack}><ArrowLeft size={17}/>返回設計</button></section>;
  const { document, correlationId, contentSha256 } = draft;
  return <>
    <section className="page-heading compact"><div><p className="eyebrow">IR 審查 · 第 2／3 步</p><h1>確認假設與未知項目</h1><p>此內容是後端產生的版本化 IR 草稿，不代表幾何、規則或製造驗證完成。</p></div><span className="prototype-badge">{document.maturity} · {document.schemaVersion}</span></section>
    <section className="review-layout"><div className="panel review-table"><div className="panel-heading"><div><span className="panel-kicker">API 回應</span><h2>假設與未知項目</h2></div><span>{document.assumptions.length + document.unknowns.length} 個項目</span></div>
      {document.assumptions.map((item) => <div className="review-row" key={item.id}><div className="provenance-icon demo-derived"><Database size={17}/></div><div><strong>{item.field}</strong><span>{item.rationale}</span></div><em className="provenance-tag demo-derived">{item.status}</em></div>)}
      {document.unknowns.map((item) => <div className={`review-row ${item.unsafeToDefault ? "critical" : ""}`} key={item.id}><div className="provenance-icon unknown"><CircleHelp size={17}/></div><div><strong>{item.field}</strong><span>{item.question}</span></div><em className="provenance-tag unknown">未知</em></div>)}
    </div><aside className="review-side"><article className="panel critical-card"><AlertOctagon size={22}/><div><span className="panel-kicker">追蹤識別碼</span><h2>{correlationId}</h2><p>Response SHA-256：<code>{contentSha256}</code></p></div></article><article className="panel acknowledge-card"><h2>工程界線</h2><ul><li>未執行幾何核心</li><li>未執行 CNC DFM 規則</li><li>未產生 STEP、圖面或 release package</li></ul><label className="check-row"><input type="checkbox" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)}/><span>我了解這只是 DRAFT IR，不是工程製品。</span></label><div className="action-row"><button className="secondary-action" onClick={onBack}><ArrowLeft size={17}/>返回修改</button><button className="primary-action" disabled={!acknowledged} onClick={onRun}>檢視 IR 結果<ChevronRight size={17}/></button></div></article></aside></section>
  </>;
}
