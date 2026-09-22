import { Activity, AlertTriangle, ArrowRight, CheckCircle2, CircleDashed, Clock3, GitBranch, Wrench } from "lucide-react";
import { useMemo, useState } from "react";
import { repositoryProgressAdapter } from "../adapters/progress-adapter";
import type { GateStatus, WorkStatus } from "../types/progress";

const gateLabels: Record<GateStatus, string> = { planned: "尚未開始", active: "施工中", blocked: "已阻塞", accepted: "已驗收" };
const workLabels: Record<WorkStatus, string> = { planned: "排程中", ready: "可施工", in_progress: "施工中", blocked: "已阻塞", done: "完成" };

export function ProgressPage() {
  const [acceptanceOpen, setAcceptanceOpen] = useState(false);
  const state = repositoryProgressAdapter.getSnapshot();
  const current = state.workItems.find((item) => item.id === state.currentWorkItem);
  const currentGate = state.gates.find((gate) => gate.id === current?.gate);
  const counts = useMemo(() => ({
    accepted: state.gates.filter((gate) => gate.status === "accepted").length,
    active: state.gates.filter((gate) => gate.status === "active").length,
    planned: state.gates.filter((gate) => gate.status === "planned").length,
  }), [state.gates]);
  const updated = new Intl.DateTimeFormat("zh-TW", { dateStyle: "medium", timeStyle: "short" }).format(new Date(state.updatedAt));

  return <>
    <section className="page-heading"><div><p className="eyebrow">施工管制</p><h1>施工進度中心</h1><p>只呈現具有儲存庫證據的狀態；不以推測百分比代替關卡驗收。</p></div><div className="sync-meta"><Clock3 size={16} /><span>最後更新<br /><strong>{updated}</strong></span></div></section>
    <section className="truth-banner" aria-label="施工狀態提醒"><AlertTriangle size={20} /><div><strong>施工進度頁只顯示控制面證據，不產生工程製品。</strong><span>G5 Prototype Package 已通過 Gate；G6 正在整合正式引導流程與可關閉的 AI 輔助，尚未完成 Gate acceptance。</span></div></section>
    <section className="summary-grid" aria-label="進度摘要">
      <article className="summary-card current-summary"><div className="summary-icon"><Wrench size={20} /></div><div><span>目前關卡</span><strong>{current?.gate}</strong><small>{currentGate?.title}</small></div></article>
      <article className="summary-card"><div className="summary-icon neutral"><CheckCircle2 size={20} /></div><div><span>已驗收關卡</span><strong>{counts.accepted}</strong><small>需完整證據才計入</small></div></article>
      <article className="summary-card"><div className="summary-icon amber"><Activity size={20} /></div><div><span>施工中</span><strong>{counts.active}</strong><small>在製工作上限：1</small></div></article>
      <article className="summary-card"><div className="summary-icon muted"><CircleDashed size={20} /></div><div><span>待施工</span><strong>{counts.planned}</strong><small>依賴未滿足不啟動</small></div></article>
    </section>
    <section className="content-grid">
      <article className="panel gate-panel"><div className="panel-heading"><div><span className="panel-kicker">關卡依賴圖</span><h2>建設路徑</h2></div><span className="schema-chip">資料結構 {state.schemaVersion}</span></div><div className="gate-list">{state.gates.map((gate, index) => <div className={`gate-row ${gate.status}`} key={gate.id}><div className="gate-rail"><span className="gate-node">{gate.status === "accepted" ? <CheckCircle2 size={18} /> : index + 1}</span>{index < state.gates.length - 1 && <span className="gate-line" />}</div><div className="gate-copy"><strong>{gate.id}</strong><span>{gate.title}</span></div><span className={`status-pill ${gate.status}`}>{gateLabels[gate.status]}</span></div>)}</div></article>
      <div className="right-stack">
        <article className="panel current-work"><div className="panel-heading"><div><span className="panel-kicker">目前工作項目</span><h2>{current?.id}</h2></div><span className={`status-pill work-${current?.status}`}>{current ? workLabels[current.status] : "未知"}</span></div><h3>{current?.title}</h3><p>施工狀態由正式 WORK_QUEUE 控制面與驗證器驅動；畫面不另存狀態副本。</p><div className="acceptance-list">{current?.acceptanceResults.map((result) => <div className={result.status} key={result.criterion}>{result.status === "passed" ? <CheckCircle2 className="acceptance-check" size={17} /> : <span className="empty-check" />}{result.criterion}</div>)}</div><div className="work-footer"><span><GitBranch size={16} /> 基準 {state.baselineCommit.slice(0, 7)}</span><button type="button" aria-expanded={acceptanceOpen} aria-controls="acceptance-evidence" onClick={() => setAcceptanceOpen((open) => !open)}>{acceptanceOpen ? "收合驗收條件" : "查看驗收條件"} <ArrowRight className={acceptanceOpen ? "disclosure-arrow open" : "disclosure-arrow"} size={16} /></button></div></article>
        {acceptanceOpen && <article className="panel acceptance-panel" id="acceptance-evidence"><div className="panel-heading"><div><span className="panel-kicker">目前工作驗收證據</span><h2>完成條件與責任邊界</h2></div><span className={`status-pill work-${current?.status}`}>{current ? workLabels[current.status] : "未知"}</span></div><div className="acceptance-evidence-list">{current?.acceptanceResults.map((result) => <section key={result.criterion}><div className={`acceptance-state ${result.status}`}>{result.status === "passed" ? <CheckCircle2 size={18} /> : <CircleDashed size={18} />}<strong>{result.criterion}</strong><span>{result.status === "passed" ? "已通過" : "待施工驗證"}</span></div>{result.evidence.length > 0 ? <ul>{result.evidence.map((path) => <li key={path}><code>{path}</code></li>)}</ul> : <p>此條件尚未形成可重跑證據，因此不會自動標記為完成。</p>}</section>)}</div><footer className="acceptance-boundary"><AlertTriangle size={18}/><p><strong>{current?.gate} 尚未完成。</strong>只有目前 Gate 的全部退出條件具有證據後，才能進入下一關卡。</p></footer></article>}
        <article className="panel queue-panel"><div className="panel-heading"><div><span className="panel-kicker">工作佇列</span><h2>後續工作</h2></div><span>{state.workItems.length} 個項目</span></div><div className="queue-table" role="table" aria-label="後續工作清單">{state.workItems.filter((item) => item.id !== state.currentWorkItem).map((item) => <div className="queue-row" role="row" key={item.id}><span className="queue-id">{item.id}</span><span className="queue-title">{item.title}</span><span className={`status-pill work-${item.status}`}>{workLabels[item.status]}</span></div>)}</div></article>
        <article className="panel risk-panel"><div className="panel-heading"><div><span className="panel-kicker">目前風險</span><h2>風險控制</h2></div><span>{state.risks.length} 項</span></div><div className="risk-list">{state.risks.map((risk) => <div key={risk.id}><AlertTriangle size={17} /><span><strong>{risk.title}</strong><small>{risk.mitigation}</small></span></div>)}</div></article>
      </div>
    </section>
  </>;
}
