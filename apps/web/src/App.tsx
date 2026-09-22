import { Activity, Boxes, FileCheck2, FlaskConical, LayoutDashboard, Menu, RadioTower, ShieldCheck, Wrench, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
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
  const mainRef = useRef<HTMLElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const [model, setModelState] = useState<PrototypeViewModel>(() => browserPrototypeAdapter.load());
  const result = useMemo(() => browserPrototypeAdapter.createDemoResult(model), [model]);
  const setModel = (next: PrototypeViewModel) => { setModelState(next); browserPrototypeAdapter.save(next); };
  const closeMobileNav = () => {
    setMobileNavOpen(false);
    menuButtonRef.current?.focus();
  };
  const go = (next: string) => { setMobileNavOpen(false); navigate(next); };
  const designFlowActive = ["/", "/design", "/review", "/run"].includes(path);

  useEffect(() => { mainRef.current?.focus(); }, [path]);
  useEffect(() => {
    if (!mobileNavOpen) return;
    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeMobileNav();
      if (event.key === "Tab") {
        const controls = Array.from(sidebarRef.current?.querySelectorAll<HTMLElement>("button:not([disabled])") ?? []);
        const first = controls[0];
        const last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [mobileNavOpen]);

  let page = <ProgressPage />;
  if (path === "/design" || path === "/") page = <DesignPage model={model} setModel={setModel} onNext={() => go("/review")} />;
  if (path === "/review") page = <ReviewPage model={browserPrototypeAdapter.load()} onBack={() => go("/design")} onRun={() => go("/run")} />;
  if (path === "/run") page = <RunPage onComplete={() => go("/results")} />;
  if (path === "/results") page = <ResultsPage result={result} onRestart={() => go("/design")} />;
  if (path === "/roadmap") page = <RoadmapPage />;

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">跳至主要內容</a>
    <header className="topbar"><button type="button" className="brand brand-button" onClick={() => go("/progress")} aria-label="MEGIS 施工進度中心"><LogoMark /><span><strong>MEGIS</strong><small>機械工程生成式智慧系統</small></span></button><div className="topbar-actions"><span className="environment-badge"><ShieldCheck size={15}/> 僅限本機</span><button ref={menuButtonRef} className="icon-button mobile-menu" type="button" aria-label="開啟導覽" aria-expanded={mobileNavOpen} aria-controls="primary-sidebar" onClick={() => setMobileNavOpen(true)}><Menu size={21}/></button><div className="avatar" role="img" aria-label="目前使用者 JN">JN</div></div></header>
    <aside ref={sidebarRef} id="primary-sidebar" className={`sidebar ${mobileNavOpen ? "is-open" : ""}`}><button ref={closeButtonRef} className="icon-button close-menu" type="button" aria-label="關閉導覽" onClick={closeMobileNav}><X size={21}/></button><nav aria-label="主要導覽"><p className="nav-label">控制中心</p><button type="button" aria-current={path === "/progress" ? "page" : undefined} className={`nav-item ${path === "/progress" ? "active" : ""}`} onClick={() => go("/progress")}><LayoutDashboard size={18}/>施工進度</button><button type="button" aria-current={designFlowActive ? "page" : undefined} className={`nav-item ${designFlowActive ? "active" : ""}`} onClick={() => go("/design")}><Wrench size={18}/>設計工作台<span>UI-0</span></button><button type="button" aria-current={path === "/results" ? "page" : undefined} className={`nav-item ${path === "/results" ? "active" : ""}`} onClick={() => go("/results")}><Activity size={18}/>展示結果<span>合成</span></button><p className="nav-label nav-label-spaced">工程系統</p><button type="button" className="nav-item disabled" disabled><Boxes size={18}/>模組<span>G4</span></button><button type="button" className="nav-item disabled" disabled><FileCheck2 size={18}/>證據<span>G5</span></button><button type="button" aria-current={path === "/roadmap" ? "page" : undefined} className={`nav-item ${path === "/roadmap" ? "active" : ""}`} onClick={() => go("/roadmap")}><RadioTower size={18}/>建設路線圖</button></nav><div className="sidebar-note"><FlaskConical size={18}/><div><strong>使用者體驗原型</strong><span>目前尚未產生任何工程製品</span></div></div></aside>
    {mobileNavOpen && <button type="button" tabIndex={-1} className="scrim" aria-label="關閉導覽遮罩" onClick={closeMobileNav}/>}<main ref={mainRef} id="main-content" tabIndex={-1} aria-label="主要內容" className={`main-content ${path === "/run" ? "run-main" : ""}`}>{page}</main>
  </div>;
}
