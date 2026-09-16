import { Check, LoaderCircle, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";

const stages = ["整理 PrototypeViewModel", "建立 demo constraint summary", "產生 synthetic validation records", "組合結果資訊架構"];
export function RunPage({ onComplete }: { onComplete: () => void }) {
  const [active, setActive] = useState(0);
  useEffect(() => {
    if (active >= stages.length) {
      const done = window.setTimeout(onComplete, 500);
      return () => window.clearTimeout(done);
    }
    const timer = window.setTimeout(() => setActive((value) => value + 1), 550);
    return () => window.clearTimeout(timer);
  }, [active, onComplete]);
  return <section className="run-stage"><div className="simulation-orbit"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="run-core">{active < stages.length ? <LoaderCircle size={34} className="spin"/> : <Check size={38}/>}</div></div><p className="eyebrow">PROTOTYPE SIMULATION · STEP 3 OF 3</p><h1>{active < stages.length ? "正在組合展示資料" : "Simulation 完成"}</h1><p>這不是 CAD、solver 或 engineering validation job。</p><div className="run-list">{stages.map((stage, index) => <div className={index < active ? "complete" : index === active ? "active" : ""} key={stage}><span>{index < active ? <Check size={15}/> : index + 1}</span>{stage}</div>)}</div><div className="run-warning"><ShieldAlert size={18}/><span><strong>Synthetic demo data</strong>No engineering artifact generated</span></div></section>;
}

