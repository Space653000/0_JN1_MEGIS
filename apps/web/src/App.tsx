import { Activity, Boxes, FileCheck2, FlaskConical, LayoutDashboard, Menu, RadioTower, ShieldCheck, Wrench, X } from "lucide-react";
import { useMemo, useState } from "react";
import { browserPrototypeAdapter } from "./adapters/prototype-adapter";
import { useRoute } from "./hooks/use-route";
import { DesignPage } from "./pages/DesignPage";
import { ProgressPage } from "./pages/ProgressPage";
import { ResultsPage } from "./pages/ResultsPage";
import { ReviewPage } from "./pages/ReviewPage";
import { RoadmapPage } from "./pages/RoadmapPage";
import { RunPage } from "./pages/RunPage";
import type { PrototypeViewModel } from "./types/prototype";

function LogoMark() { return <span className="logo-mark" aria-hidden="true"><span>M</span></span>; }

export function App() {
  const { path, navigate } = useRoute();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [model, setModelState] = useState<PrototypeViewModel>(() => browserPrototypeAdapter.load());
  const result = useMemo(() => browserPrototypeAdapter.createDemoResult(model), [model]);
  const setModel = (next: PrototypeViewModel) => { setModelState(next); browserPrototypeAdapter.save(next); };
  const go = (next: string) => { setMobileNavOpen(false); navigate(next); };
  const designFlowActive = ["/", "/design", "/review", "/run"].includes(path);

  let page = <ProgressPage />;
  if (path === "/design" || path === "/") page = <DesignPage model={model} setModel={setModel} onNext={() => go("/review")} />;
  if (path === "/review") page = <ReviewPage model={browserPrototypeAdapter.load()} onBack={() => go("/design")} onRun={() => go("/run")} />;
  if (path === "/run") page = <RunPage onComplete={() => go("/results")} />;
  if (path === "/results") page = <ResultsPage result={result} onRestart={() => go("/design")} />;
  if (path === "/roadmap") page = <RoadmapPage />;

  return <div className="app-shell">
    <header className="topbar"><button type="button" className="brand brand-button" onClick={() => go("/progress")} aria-label="MEGIS 施工進度中心"><LogoMark /><span><strong>MEGIS</strong><small>Mechanical Engineering Intelligence</small></span></button><div className="topbar-actions"><span className="environment-badge"><ShieldCheck size={15}/> Local-only</span><button className="icon-button mobile-menu" type="button" aria-label="開啟導覽" onClick={() => setMobileNavOpen(true)}><Menu size={21}/></button><div className="avatar" aria-label="目前使用者">JN</div></div></header>
    <aside className={`sidebar ${mobileNavOpen ? "is-open" : ""}`}><button className="icon-button close-menu" type="button" aria-label="關閉導覽" onClick={() => setMobileNavOpen(false)}><X size={21}/></button><nav aria-label="主要導覽"><p className="nav-label">控制中心</p><button className={`nav-item ${path === "/progress" ? "active" : ""}`} onClick={() => go("/progress")}><LayoutDashboard size={18}/>施工進度</button><button className={`nav-item ${designFlowActive ? "active" : ""}`} onClick={() => go("/design")}><Wrench size={18}/>設計工作台<span>UI-0</span></button><button className={`nav-item ${path === "/results" ? "active" : ""}`} onClick={() => go("/results")}><Activity size={18}/>Demo Results<span>合成</span></button><p className="nav-label nav-label-spaced">工程系統</p><button className="nav-item disabled" disabled><Boxes size={18}/>Modules<span>G4</span></button><button className="nav-item disabled" disabled><FileCheck2 size={18}/>Evidence<span>G5</span></button><button className={`nav-item ${path === "/roadmap" ? "active" : ""}`} onClick={() => go("/roadmap")}><RadioTower size={18}/>Roadmap</button></nav><div className="sidebar-note"><FlaskConical size={18}/><div><strong>UX Prototype</strong><span>目前尚未產生任何工程 artifact</span></div></div></aside>
    {mobileNavOpen && <button className="scrim" aria-label="關閉導覽" onClick={() => setMobileNavOpen(false)}/>}<main className={`main-content ${path === "/run" ? "run-main" : ""}`}>{page}</main>
  </div>;
}
