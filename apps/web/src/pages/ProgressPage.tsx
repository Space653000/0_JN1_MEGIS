import { Activity, AlertTriangle, ArrowRight, CheckCircle2, CircleDashed, Clock3, GitBranch, Wrench } from "lucide-react";
import { useMemo } from "react";
import { repositoryProgressAdapter } from "../adapters/progress-adapter";
import type { GateStatus, WorkStatus } from "../types/progress";

const gateLabels: Record<GateStatus, string> = { planned: "尚未開始", active: "施工中", blocked: "已阻塞", accepted: "已驗收" };
const workLabels: Record<WorkStatus, string> = { planned: "排程中", ready: "可施工", in_progress: "施工中", blocked: "已阻塞", done: "完成" };

export function ProgressPage() {
  const state = repositoryProgressAdapter.getSnapshot();
  const current = state.workItems.find((item) => item.id === state.currentWorkItem);
  const counts = useMemo(() => ({
    accepted: state.gates.filter((gate) => gate.status === "accepted").length,
    active: state.gates.filter((gate) => gate.status === "active").length,
    planned: state.gates.filter((gate) => gate.status === "planned").length,
  }), [state.gates]);
  const updated = new Intl.DateTimeFormat("zh-TW", { dateStyle: "medium", timeStyle: "short" }).format(new Date(state.updatedAt));

  return <>
    <section className="page-heading"><div><p className="eyebrow">CONSTRUCTION CONTROL</p><h1>施工進度中心</h1><p>只呈現具有 repository 證據的狀態；不以推測百分比代替 Gate 驗收。</p></div><div className="sync-meta"><Clock3 size={16} /><span>最後更新<br /><strong>{updated}</strong></span></div></section>
    <section className="truth-banner" aria-label="原型狀態提醒"><AlertTriangle size={20} /><div><strong>UI-0 是使用者體驗原型，不是工程生成能力。</strong><span>CAD、DFM、BOM 與 Prototype Package 尚未實作；G6 仍須通過真實 UI-to-IR 驗證。</span></div></section>
    <section className="summary-grid" aria-label="進度摘要">
      <article className="summary-card current-summary"><div className="summary-icon"><Wrench size={20} /></div><div><span>目前 Gate</span><strong>UI-0B</strong><small>Construction Progress Center</small></div></article>
      <article className="summary-card"><div className="summary-icon neutral"><CheckCircle2 size={20} /></div><div><span>已驗收 Gate</span><strong>{counts.accepted}</strong><small>需完整 evidence 才計入</small></div></article>
      <article className="summary-card"><div className="summary-icon amber"><Activity size={20} /></div><div><span>施工中</span><strong>{counts.active}</strong><small>WIP limit = 1</small></div></article>
      <article className="summary-card"><div className="summary-icon muted"><CircleDashed size={20} /></div><div><span>待施工</span><strong>{counts.planned}</strong><small>依賴未滿足不啟動</small></div></article>
    </section>
    <section className="content-grid">
      <article className="panel gate-panel"><div className="panel-heading"><div><span className="panel-kicker">GATE DAG</span><h2>建設路徑</h2></div><span className="schema-chip">schema {state.schemaVersion}</span></div><div className="gate-list">{state.gates.map((gate, index) => <div className={`gate-row ${gate.status}`} key={gate.id}><div className="gate-rail"><span className="gate-node">{gate.status === "accepted" ? <CheckCircle2 size={18} /> : index + 1}</span>{index < state.gates.length - 1 && <span className="gate-line" />}</div><div className="gate-copy"><strong>{gate.id}</strong><span>{gate.title}</span></div><span className={`status-pill ${gate.status}`}>{gateLabels[gate.status]}</span></div>)}</div></article>
      <div className="right-stack">
        <article className="panel current-work"><div className="panel-heading"><div><span className="panel-kicker">CURRENT WORK ITEM</span><h2>{current?.id}</h2></div><span className="status-pill active">施工中</span></div><h3>{current?.title}</h3><p>施工狀態由唯一 JSON source 與 schema 驅動；畫面不另存狀態副本。</p><div className="acceptance-list">{current?.acceptance.map((item) => <div key={item}><span className="empty-check" />{item}</div>)}</div><div className="work-footer"><span><GitBranch size={16} /> baseline {state.baselineCommit.slice(0, 7)}</span><button type="button">查看驗收條件 <ArrowRight size={16} /></button></div></article>
        <article className="panel queue-panel"><div className="panel-heading"><div><span className="panel-kicker">WORK QUEUE</span><h2>後續工作</h2></div><span>{state.workItems.length} items</span></div><div className="queue-table" role="table" aria-label="後續工作清單">{state.workItems.filter((item) => item.id !== state.currentWorkItem).map((item) => <div className="queue-row" role="row" key={item.id}><span className="queue-id">{item.id}</span><span className="queue-title">{item.title}</span><span className={`status-pill work-${item.status}`}>{workLabels[item.status]}</span></div>)}</div></article>
        <article className="panel risk-panel"><div className="panel-heading"><div><span className="panel-kicker">ACTIVE RISKS</span><h2>風險控制</h2></div><span>{state.risks.length} active</span></div><div className="risk-list">{state.risks.map((risk) => <div key={risk.id}><AlertTriangle size={17} /><span><strong>{risk.title}</strong><small>{risk.mitigation}</small></span></div>)}</div></article>
      </div>
    </section>
  </>;
}

