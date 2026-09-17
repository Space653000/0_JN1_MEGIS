# MEGIS

**Mechanical Engineering Generative Intelligence System（機械工程生成式智慧系統）**

MEGIS 的目標，是將機械、聲學與製造工程師的判斷轉化為可追溯、可驗證、可重現的引導式生成工程流程。系統以確定性工程資料、規則、受限幾何與驗證證據為核心；LLM 只協助整理設計意圖、提出問題與解釋結果，不取代幾何核心、物理求解器或工程簽核。

## V2.0 可執行藍圖

專案唯一主要施工依據為：

- [MEGIS Mechanical Engineering Generative Intelligence System — v2.0 Codex](<MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v2.0 Codex.md>)
- [V1.0 原始藍圖（封存參考）](<MEGIS_Blueprint/OLD/Generative Mechanical Design Factory — Master Blueprint & Detailed Implementation Plan.md>)

V2.0 採 Gate-driven construction，不以日期或推測百分比宣稱完成。每個 Gate 必須具備可重跑的程式、測試、工程製品或決策證據，下一 Gate 才能開始。

## 目前施工狀態

**G0 與 G1 已完成並通過驗收**。目前位於 **G2：治具幾何垂直切片**；geometry contract 與 fixture base 已完成，唯一在製項目為 `G2-CAD-003`。

UI-0 是本機端使用者體驗原型，用來先確認施工進度中心與治具／電子外殼引導流程。它使用有版本的 `PrototypeViewModel` 展示資料，不是藍圖中的 G6 工程能力，也不會產生 STEP、工程圖面、BOM、Prototype Package 或可供製造的工程製品。

目前已完成：

- UI-0A：最小可行基礎
- UI-0B：施工進度中心
- UI-0C：引導式使用者體驗原型
- UI-0D：自動化、瀏覽器與使用者驗收皆已通過

UI-0 已完成驗收，但仍只是使用者體驗原型；G0 不會把其合成展示資料當作工程輸出。CadQuery 可行性已通過，FreeCAD 圖面路徑採固定模板 SVG fallback，COMSOL 在本機則正式決策為非阻塞的 `out_of_scope`。本機與 GitHub Actions baseline CI 均已全綠，G1 工程契約、golden cases、migration 與 rollback 已固定，目前正在建立 G2 geometry capability contract。最新狀態與驗證證據：

- [UI-0 施工計畫](docs/UI0_PLAN.md)
- [UI-0 可行性紀錄](docs/UI0_FEASIBILITY.md)
- [UI-0 驗證報告](docs/UI0_VERIFICATION.md)
- [UI-0 使用者驗收紀錄](docs/UI0_ACCEPTANCE.md)
- [正式專案狀態](execution/PROJECT_STATE.md)
- [正式工作佇列](execution/WORK_QUEUE.yaml)
- [G0 工具鏈版本決策](docs/decisions/toolchain.md)
- [G0 CadQuery 可行性驗證](docs/G0_CAD_VERIFICATION.md)
- [G0 FreeCAD TechDraw fallback 決策](docs/G0_FREECAD_DECISION.md)
- [G0 COMSOL 可行性決策](docs/G0_COMSOL_DECISION.md)
- [G0 Baseline CI](docs/G0_BASELINE_CI.md)
- [G1 Engineering Primitives](docs/G1_PRIMITIVES.md)
- [G1 Engineering IR](docs/G1_ENGINEERING_IR.md)
- [G1 Golden Cases](docs/G1_GOLDEN_CASES.md)
- [G1 Schema Migration Contract](docs/G1_SCHEMA_MIGRATION.md)
- [G2 Geometry Capability Contract](docs/G2_GEOMETRY_CONTRACT.md)
- [G2 Fixture Base](docs/G2_FIXTURE_BASE.md)

## 本機啟動

網站需求固定為 Node.js 24.17.0 與 npm 11.13.0。網站綁定於 `127.0.0.1`，不應公開至區域網路或網際網路。

```powershell
cd C:\0_JN1_MEGIS\apps\web
npm install
npm run dev
```

開啟：<http://127.0.0.1:4173/progress>

## 完整驗證

```powershell
cd C:\0_JN1_MEGIS
node scripts\verify-control-plane.mjs
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\verify_toolchain.py
.\.venv\Scripts\python.exe -m pytest

cd C:\0_JN1_MEGIS\apps\web
npm run lint
npm run typecheck
npm run test
npm run build
```

所有專案快取、暫存檔、測試輸出與建置結果都必須留在 `C:\0_JN1_MEGIS`。本專案不得修改、共用環境或依賴 `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent`。

## 本機資料與 GitHub 同步

施工以本機 repository 為工作來源，每個通過驗證的單一工作項目先建立可回滾的 commit，再同步至 GitHub `main`。同步前先執行 `git fetch origin` 與 `git status -sb` 確認沒有遠端分歧；同步後再次抓取遠端並核對 `HEAD` 與 `origin/main` 的 commit SHA。禁止使用 `git push --force`，任何推送都必須取得使用者明確授權。

## 建設路線

```text
UI-0 使用者體驗原型與驗收
↓
G0 基礎建設與可行性
↓
G1 工程契約與黃金案例
↓
G2 治具幾何垂直切片
↓
G3 規則與驗證
↓
G4 模組與限制條件組合
↓
G5 原型套件與可重現性
↓
G6 引導式工程介面
├─ G7 聲學垂直切片
└─ G8 機器人垂直切片
↓
G9 強化與擴充
```

第一條完整工程路徑固定為小型 CNC 治具／電子外殼。MEGIS 自動化施工的最高成熟度為 `PROTOTYPE`；`ENGINEERING_REVIEWED` 與 `RELEASED` 必須經過合格工程師及適用的製造、品質與法規流程。
