import { Check, LoaderCircle, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
const stages = ["確認 IR schema 版本", "整理 assumptions", "整理 unknowns", "準備唯讀結果畫面"];
export function RunPage({ onComplete }: { onComplete: () => void }) {
  const [active, setActive] = useState(0);
  useEffect(() => { const timer = window.setTimeout(active >= stages.length ? onComplete : () => setActive((value) => value + 1), active >= stages.length ? 250 : 300); return () => window.clearTimeout(timer); }, [active, onComplete]);
  return <section className="run-stage" aria-live="polite" aria-busy={active < stages.length}><div className="simulation-orbit" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="run-core">{active < stages.length ? <LoaderCircle size={34} className="spin"/> : <Check size={38}/>}</div></div><p className="eyebrow">IR 整理 · 第 3／3 步</p><h1>{active < stages.length ? "正在整理 API 草稿" : "整理完成"}</h1><p>不執行 CAD、求解器、規則引擎或工程驗證。</p><div className="run-list">{stages.map((stage,index) => <div className={index < active ? "complete" : index === active ? "active" : ""} key={stage}><span aria-hidden="true">{index < active ? <Check size={15}/> : index + 1}</span>{stage}</div>)}</div><div className="run-warning"><ShieldAlert size={18}/><span><strong>DRAFT IR only</strong>No engineering artifact generated</span></div></section>;
}
