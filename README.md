# MEGIS

**Mechanical Engineering Generative Intelligence System（機械工程生成式智慧系統）**

MEGIS 的目標，是將機械、聲學與製造工程師的判斷轉化為可追溯、可驗證、可重現的引導式生成工程流程。系統以確定性工程資料、規則、受限幾何與驗證證據為核心；LLM 只協助整理設計意圖、提出問題與解釋結果，不取代幾何核心、物理求解器或工程簽核。

## V3.0 可執行藍圖

專案唯一主要施工依據為：

- [MEGIS Mechanical Engineering Generative Intelligence System — v3.0 Claude Code](<MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md>)
- [V2.0 可執行藍圖（封存基線）](<MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v2.0 Codex.md>)
- [V1.0 原始藍圖（封存參考）](<MEGIS_Blueprint/OLD/Generative Mechanical Design Factory — Master Blueprint & Detailed Implementation Plan.md>)

V3.0 採 Gate-driven construction，不以日期或推測百分比宣稱完成。它保留 V2.0 已完成工作與 Gate，透過 V3 Conformance（`V3C-*`）補足 control plane、決策、fingerprint、classification、artifact 與隔離審查要求；每個 Gate 必須具備可重跑證據，下一 Gate 才能接受。

## 目前施工狀態

**G0 與 G1 沿用既有驗收，G2 為 active Gate**。V3 必要工作圖共有 74 項，目前控制面為 **19 done、1 in progress、54 planned**；唯一在製項目是 `V3C-ART-001` 的完工收尾。其 artifact policy 1.0.0、Git 大小預算、`.gitattributes`、重型製品精確白名單與負向測試已在 commit `da4e61d` 通過本機及 GitHub Actions，待本段 README 與完工報告閉環後轉入隔離審查。

最近完成的 V3 補強包括：

- `V3C-DET-001`：L1 byte hash、L2 semantic fingerprint、STEP/DXF/STL 正規化及跨 process replay。
- `V3C-MAT-001`：五種 artifact classification、全庫 manifest scanner；非 `DESIGN_RUN` 的 `maturity` 必須為 `null`。
- `V3C-ART-001` 實作：tracked file 1 MiB、evidence JSON 50 KiB、golden 200 KiB／總量 5 MiB 預算；五個既有 G0 重型製品由 ADR-0011 以 path、bytes、SHA-256 鎖定，後續 spike 重型製品禁止新增入 Git。

UI-0 是本機端使用者體驗原型，用來先確認施工進度中心與治具／電子外殼引導流程。它使用有版本的 `PrototypeViewModel` 展示資料，不是藍圖中的 G6 工程能力，也不會產生 STEP、工程圖面、BOM、Prototype Package 或可供製造的工程製品。

目前已完成：

- UI-0A：最小可行基礎
- UI-0B：施工進度中心
- UI-0C：引導式使用者體驗原型
- UI-0D：自動化、瀏覽器與使用者驗收皆已通過

UI-0 已完成驗收，但仍只是使用者體驗原型；G0 不會把其合成展示資料當作工程輸出。CadQuery 可行性已通過，FreeCAD 圖面路徑採固定模板 SVG fallback，COMSOL 在本機正式決策為非阻塞的 `out_of_scope`。G1 工程契約、golden cases、migration 與 rollback 已固定；G2 已完成 geometry contract、fixture base 與 assembly geometry。V3 新增要求尚未完成者均保留為未完成工作，不會用既有 V2 證據冒充 V3 合規。

## 為什麼目前網站沒有更多產品或功能？

`http://127.0.0.1:4173/` 現在是 **UI-0 使用者體驗原型**，不是完成版 MEGIS。頁面只能用固定、版本化的合成資料示範治具／電子外殼引導流程；結果必須持續標示 `Synthetic demo data` 與 `No engineering artifact generated`。真正的 Engineering IR、CadQuery adapter、組立幾何與驗證證據目前存在 repository 與自動測試中，尚未完成 G3～G6 的規則、maturity、package、job/API 與正式 UI 串接，因此不能提前放進首頁宣稱可用。

| 使用入口／能力 | 現況 | 誠實邊界 |
|---|---|---|
| `/` 引導式設計頁 | UI-0 demo 可操作 | 合成資料；不產生 STEP、drawing、BOM 或 release package |
| `/progress` 施工進度中心 | 可操作 | 顯示控制面與驗證狀態，不是工程結果審查器 |
| Fixture／電子外殼核心 | G2 已完成 base、cover、fasteners、USB-C cutout、PCB envelope 與 clearance 核心 | 目前由 tests/CLI 驗證，尚未接上正式 UI 與 package pipeline |
| STEP/STL/DXF | G0 feasibility spike 可重建並重新載入 | classification 是 `FEASIBILITY_SPIKE`，`maturity: null`，不可當製造輸出 |
| 工程規則與 maturity | 藍圖已定義 | G3 尚未施工，現在沒有正式 evaluator |
| BOM、drawing、Prototype Package | 尚未施工 | 位於 G5，不提供假下載按鈕 |
| 正式引導式工程介面 | 尚未施工 | 位於 G6，屆時才接真實 IR、jobs、驗證與 fallback |
| Acoustic 產品線 | 僅有 schema-only golden case | G7 solver/thin slice 尚未施工 |
| Robot Car 產品線 | 僅有 schema-only golden case | G8 assembly/safety thin slice 尚未施工，maturity 上限受安全政策限制 |

也就是說，現在「產品少」不是遺漏，而是 MEGIS 的防誤導設計：只有具備 schema、negative tests、artifact 證據、review 與 Gate acceptance 的能力，才會從施工核心升級為使用者可見功能。

## 已驗證能力與尚未完成能力

| 層級 | 已驗證 | 尚未完成 |
|---|---|---|
| UI-0 | 中文進度中心、引導式 demo、桌面與窄螢幕驗收 | 真實工程資料、下載、multi-user、cloud |
| G0 | 鎖定工具鏈、CadQuery spike、FreeCAD fallback、Windows CI、fingerprint/classification/artifact policy | accepted Gate 的 V3 retrospective review/sign-off 補強 |
| G1 | Engineering primitives、IR schema、Fixture/Acoustic/Robot golden inputs、V1→V2 migration/rollback | V3 error taxonomy、supported envelope、research dossier、review/acceptance |
| G2 | Kernel-neutral geometry contract、fixture base 與 assembly | 正式 export/reload pipeline、negative geometry suite、review/acceptance |
| G3～G9 | 藍圖、工作圖與 acceptance criteria 已建立 | 規則、validators、maturity、modules、packages、正式 UI、Acoustic、Robot、hardening 均未完成 |

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
- [G2 Fixture Assembly](docs/G2_FIXTURE_ASSEMBLY.md)
- [V3 採用決策](docs/decisions/ADR-0001-adopt-v3-blueprint.md)
- [Classification 與 maturity 政策](docs/CLASSIFICATION_AND_MATURITY.md)
- [Artifact 儲存與 Git 大小預算政策](docs/ARTIFACT_POLICY.md)
- [ADR-0011：既有 G0 重型製品精確白名單](docs/decisions/ADR-0011-legacy-heavy-artifact-allowlist.md)
- [V3 最新完整進度盤點](outputs/2026-09-17-V3C-MAT-001-完工進度報告.md)
- [決策索引](docs/DECISIONS.md)

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
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

完整 baseline 會依序執行 control-plane、artifact policy 正／負向檢查、Python dependency/toolchain、103 個 Python tests、manifest maturity scan、13 筆 artifact smoke、前端 lint/typecheck、9 個 frontend tests 與 production build。

所有專案快取、暫存檔、測試輸出與建置結果都必須留在 `C:\0_JN1_MEGIS`。本專案不得修改、共用環境或依賴 `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent`。

## 本機資料與 GitHub 同步

施工以本機 repository 為工作來源，每個通過驗證的單一工作項目先建立可回滾的 commit，再同步至 [GitHub `main`](https://github.com/Space653000/0_JN1_MEGIS)。同步前先執行 `git fetch origin` 與 `git status -sb` 確認沒有遠端分歧；同步後再次抓取遠端並核對 `HEAD` 與 `origin/main` 的 commit SHA。禁止使用 `git push --force`，任何推送都必須取得使用者明確授權。

藍圖、程式、schema、tests、文件、控制面與小型驗證證據會同步；`.venv`、cache、`.temp`、`node_modules`、`dist`、`.runs` 與新的 spike 重型製品不會上傳。這些排除項是可重建或本機執行資料，不是遺漏同步。

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
