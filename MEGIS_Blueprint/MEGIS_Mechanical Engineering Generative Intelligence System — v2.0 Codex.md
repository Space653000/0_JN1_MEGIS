# Generative Mechanical Design Factory
## v2.0 — Codex Continuous Execution Plan

**版本：v2.0**  
**日期：2026-09-16**  
**文件狀態：Executable Blueprint**  
**執行主體：ChatGPT Codex + Mechanical Engineering Reviewer**  
**前版：v1.0 Master Blueprint（保留，不覆寫）**

---

# 0. 文件目的

本文件把 v1.0 的產品願景改寫成可由 ChatGPT Codex 持續施工、可中斷恢復、可驗證、可追溯的工程計畫。

本版不使用「90 天」、「第幾週」或固定日曆作為完成依據。進度只由可觀察的 Gate 決定：

```text
前一 Gate 的驗收證據完整
↓
後一 Gate 才可開始
↓
外部依賴未就緒時走 fallback
↓
每次施工都留下可恢復狀態
```

「連續施工」的定義不是要求單一對話永不中斷，而是：

- 任一工作階段結束後，下一個 Codex 執行階段可以從 repository 中的狀態檔恢復。
- 每個工作單元都有輸入、輸出、驗收、測試、風險及回滾邊界。
- 不依賴聊天紀錄保存關鍵決策。
- 不以程式碼已寫完作為完成；必須有可重跑的驗收證據。

---

# 1. 核心決策

## 1.1 GO，但採 Gate-driven construction

產品方向維持：

> 將資深 Mechanical、Acoustic、Manufacturing Engineer 的工程判斷，轉成零工程背景使用者也能操作的 Guided Generative Engineering System。

首要建設目標不是「讓 AI 自由畫 3D」，而是建立：

```text
Engineering Data Model
→ Deterministic Rules
→ Constrained Geometry
→ Validation Evidence
→ Guided UI
→ AI Assistance
```

## 1.2 第一個完整能力只做一條 vertical slice

第一個完整、可驗收的產品路徑為：

> **CNC Fixture / Electronics Enclosure**

固定 Reference Case：

```text
外形：120 × 80 × 35 mm
內容物：2 PCB
外部介面：USB-C
緊固：M3
上蓋：可拆式
材料：Aluminum 6061
製程：3-axis CNC
最小壁厚：2 mm
```

Acoustic Module 與 Robot Car 在核心能力穩定後，以 thin slice 驗證 Product DNA、Module、Constraint Graph 能否跨領域重用；在各自 Solver、Assembly 與驗證能力完成前，不宣稱為完整工程設計。

## 1.3 MVP 最高成熟度為 PROTOTYPE

所有設計採下列成熟度狀態：

```text
DRAFT
→ CONCEPT
→ PROTOTYPE
→ ENGINEERING_REVIEWED
→ RELEASED
```

本計畫可由 Codex 自動推進至 `PROTOTYPE`。`ENGINEERING_REVIEWED` 需要合格工程師簽核；`RELEASED` 還需要適用的製造、品質、法規與組織放行程序。

任何未通過的 Gate、waiver、未知假設或人工待確認項目，都必須出現在輸出文件與 `release_manifest.json`，不得以 `RELEASED` 命名。

---

# 2. 支援邊界

## 2.1 第一條 vertical slice 的 supported envelope

初始支援範圍：

| 項目 | 支援範圍 |
|---|---|
| 產品 | 小型 CNC 電子治具／外殼 |
| 外形 | 矩形、單腔、可拆上蓋 |
| 尺寸 | 50–300 mm 主尺度 |
| 材料 | Aluminum 6061 |
| 製程 | 3-axis CNC |
| 零件 | PCB、USB-C、M3 fastener、cover、base |
| 幾何 | box、plate、shell、hole、pocket、boss、cutout、fillet、chamfer、mount |
| 組裝 | 由上方裝入、螺絲固定、無運動機構 |
| 驗證 | schema、unit、geometry、collision、clearance、wall、basic CNC DFM |
| 圖面 | 固定模板、白名單尺寸、人工 QA |
| 輸出 | STEP、STL、2D DXF section、BOM、DFM report、manifest |

## 2.2 明確不支援

下列項目不屬於第一條 vertical slice：

- 自由曲面、Class-A surface、拓樸最佳化。
- 完整 GD&T 自動決策。
- 自動安全認證或 Production Ready 宣告。
- 注塑、鈑金、壓鑄、多軸加工。
- 疲勞、衝擊、非線性結構、完整熱流耦合。
- 任意 STEP/DXF 自動推斷材料、載荷、供應商或物理屬性。
- 任意新產品只靠 YAML 即獲得新幾何或新求解能力。
- 完整 Creo 相容、完整 COMSOL 取代。

## 2.3 Product = Data 的精確定義

純資料可完成：

- 已存在 Module 的組合。
- 已存在 Constraint vocabulary 的關係。
- 已支援參數範圍內的產品變體。
- 已存在 UI component 的問題與選項。

需要程式或 plugin：

- 新幾何 generator。
- 新 constraint semantics。
- 新 solver／manufacturing adapter。
- 新檔案解析器。
- 新驗證演算法。

因此正式原則為：

> **Product composition is data; new engineering capability is code plus validated data.**

---

# 3. 系統不變量

以下不變量適用於每一階段：

1. LLM 只提出 Design Intent、問題、候選方案及解釋；不能成為幾何、物理或放行的唯一真相。
2. 所有工程數值必須有明確 unit，不接受無單位裸值。
3. 所有衍生決策必須記錄來源：`user`、`derived`、`defaulted`、`database` 或 `engineer_override`。
4. 所有未知值保持 `unknown`；不得由模型虛構。
5. 每次 Design Run 必須可以由固定輸入與固定版本重建。
6. 外部工具失敗時，系統回傳結構化 failure，不輸出看似成功的 artifact。
7. 每個規則都有來源、版本、適用範圍、測試與 owner。
8. 每個 Gate 的失敗必須阻止成熟度升級，除非有具名 waiver 與人工簽核。
9. UI 只能引導使用者進入目前已驗證的 capability envelope。
10. 任何宣稱「完成」都必須指向可重跑的測試或驗收證據。

---

# 4. Architecture contracts

## 4.1 主資料流

```text
Human Intent
↓
Requirement Model
↓
Product DNA
↓
Engineering IR
↓
Constraint Graph
↓
Rule Evaluation
↓
Geometry Generation
↓
Validation
↓
Artifacts + Evidence
↓
Prototype Package
```

## 4.2 Engineering IR 必備欄位

Engineering IR 最少包含：

```yaml
schema_version: 2.0.0
design_id: PROJECT-0001
revision: A
units: mm
coordinate_system:
  handedness: right
  x: width
  y: depth
  z: height

requirements: []
components: []
interfaces: []
relationships: []
materials: []
manufacturing: []
constraints: []
assumptions: []
unknowns: []
provenance: []
```

所有 entity 必須有穩定 ID；entity reference 必須通過 referential-integrity validation。尺寸需支援 nominal、min、max、tolerance 或 range，而不只單一數字。

## 4.3 Capability contract

每個 Adapter 必須公布：

- `capabilities`
- `supported_versions`
- `input_schema`
- `output_schema`
- `timeout_policy`
- `determinism_notes`
- `error_codes`
- `health_check`
- `fallback`

第一版固定單一 CadQuery／OpenCascade backend。build123d 與 commercial CAD adapter 只保留介面，不在沒有實際遷移需求時同步實作。

## 4.4 Job state contract

長時間工作採明確狀態：

```text
QUEUED
→ RUNNING
→ SUCCEEDED
→ FAILED
→ CANCELLED
→ NEEDS_REVIEW
```

Job 必須支援 timeout、cancel、idempotency key、structured log 與 artifact index。

---

# 5. Codex 連續施工控制面

## 5.1 Repository 必備狀態檔

Gate 0 建立下列單一真相來源：

```text
AGENTS.md
docs/
├─ PRODUCT.md
├─ ARCHITECTURE.md
├─ DECISIONS.md
├─ SUPPORTED_ENVELOPE.md
├─ ACCEPTANCE.md
├─ RISKS.md
└─ OPERATIONS.md

execution/
├─ PROJECT_STATE.md
├─ WORK_QUEUE.yaml
├─ BLOCKERS.yaml
├─ LAST_VERIFICATION.json
└─ handoffs/
```

用途：

- `PROJECT_STATE.md`：目前 Gate、已完成能力、下一工作單元、最後綠色 commit。
- `WORK_QUEUE.yaml`：有依賴邊的工作單元，不使用日曆日期排序。
- `BLOCKERS.yaml`：只記真正阻塞條件、owner、解除方法與 fallback。
- `LAST_VERIFICATION.json`：最後一次測試命令、版本、結果及 artifact hash。
- `handoffs/`：跨上下文的短期施工摘要；完成後可歸檔。

## 5.2 每次 Codex 施工循環

```text
1. Resume
   讀 AGENTS.md、PROJECT_STATE、WORK_QUEUE、最近 handoff。

2. Inspect
   檢查 repository、未提交變更、相關程式、測試與決策紀錄。

3. Select
   只選一個依賴已滿足、可在本回合形成驗收證據的工作單元。

4. Baseline
   修改前先跑該範圍現有測試，保存結果。

5. Implement
   以最小 vertical increment 完成程式、schema、tests、docs。

6. Verify
   執行單元測試、契約測試、golden regression 及必要 artifact 檢查。

7. Record
   更新 PROJECT_STATE、WORK_QUEUE、DECISIONS、RISKS 與驗收證據。

8. Commit
   只提交已通過 Gate 的一致變更，使用簡潔英文 commit message。

9. Continue
   尚有可安全執行的 ready work item 時，進入下一循環。
```

## 5.3 工作單元格式

每個 work item 必須包含：

```yaml
id: G2-CAD-001
title: Generate reference enclosure base
gate: 2
status: ready
depends_on: [G1-IR-003]
inputs: []
outputs: []
acceptance: []
verification_commands: []
rollback_boundary: commit
blocked_by: []
evidence: []
```

`done` 的唯一含義是 acceptance 全部有證據；部分完成使用 `in_progress`，不得把未驗收工作標成完成。

## 5.4 中斷與恢復

Codex 在必須停止前：

1. 保持 repository 在可理解狀態。
2. 將未完成變更、測試結果與下一步寫入 handoff。
3. 在 `PROJECT_STATE.md` 標示最後綠色 fixed point。
4. 不為了「看起來完成」降低 Gate。

下次執行先驗證 fixed point；若狀態檔與實際 repository 不一致，以程式碼、測試及 Git history 為準並修正狀態檔。

## 5.5 自動前進與停止條件

Codex 可以自動前進的條件：

- 工作單元已在核准範圍內。
- 依賴已滿足。
- 不需要新產品決策、付費採購、憑證或外部人工簽核。
- 修改可由既定測試驗證並能安全回滾。

Codex 必須停止並請求決策的條件：

- supported envelope 需要擴張。
- 需要購買 COMSOL／商業 CAD／雲端服務授權。
- 工程安全假設缺失且無安全 default。
- 需求衝突會改變產品方向。
- 需要具名工程師或法規簽核。
- 同一阻塞在 fallback 後仍無法形成可信結果。

---

# 6. Gate DAG

```text
G0 Foundation & Feasibility
↓
G1 Engineering Contracts & Golden Cases
↓
G2 Fixture Geometry Vertical Slice
↓
G3 Rules & Validation
↓
G4 Module & Constraint Composition
↓
G5 Prototype Package & Reproducibility
↓
G6 Guided UI
├───────────────┐
↓               ↓
G7 Acoustic     G8 Robot
Thin Slice      Thin Slice
└───────┬───────┘
        ↓
G9 Hardening & Expansion
```

Gate 只表示依賴順序，不表示時間。G7 與 G8 可在 G6 後平行，但各自仍需獨立 acceptance。

---

# 7. G0 — Foundation & Feasibility

## 目標

建立可持續施工的 repository、固定技術決策，並在大量開發前證明關鍵外部工具可用。

## 工作

1. 建立 repository、開發環境與鎖定依賴版本。
2. 建立第 5 章的施工控制面文件。
3. 決定並記錄：
   - local/internal prototype 或 cloud。
   - single-user 或 multi-tenant。
   - 支援 OS、Python、Node、CadQuery、OpenCascade、FreeCAD 版本。
   - LLM provider 與離線 deterministic fallback。
   - artifact retention、IP、上傳資料政策。
4. 完成 feasibility spikes：
   - CadQuery：Reference Case 可輸出合法 STEP、STL、2D DXF section。
   - FreeCAD TechDraw：headless 產生固定模板圖面；若失敗，採人工 QA 或 SVG/PDF fallback。
   - COMSOL：只驗證授權、headless、API、queue 與範例模型，不納入核心 Gate。
5. 建立 CI、lint、type check、unit test、schema test 與 artifact smoke test。

## Exit criteria

- 新環境依 README 可重建。
- 所有 dependency 都有 pinned version 或可重現 lockfile。
- CadQuery spike 有 STEP artifact 與 automated validity check。
- FreeCAD／COMSOL 各有 `pass`、`fallback` 或 `out_of_scope` 決策，沒有 undecided dependency。
- `PROJECT_STATE.md` 與 `WORK_QUEUE.yaml` 可驅動下一 Gate。
- baseline CI 全綠。

## 回滾邊界

G0 只建立 scaffold 與 spike。若外部工具不可用，保留 spike evidence，切換 fallback，不把失敗 adapter 帶入核心架構。

---

# 8. G1 — Engineering Contracts & Golden Cases

## 目標

以 schema、語意與 golden cases 固定跨模組契約。

## 工作

1. 定義 Requirement、Product DNA、Module、Engineering IR、Rule、Constraint、Validation Result schema。
2. 定義 unit system、coordinate system、tolerance、range、ID/reference、provenance、revision。
3. 建立 schema migration 介面及 semantic version policy。
4. 建立 Reference Fixture golden input、expected IR、expected graph、expected artifact metadata。
5. 建立 Acoustic 與 Robot 的 schema-only golden input，用來證明 vocabulary 可擴充，不宣稱 CAD 完成。
6. 建立 assumption review：
   - known
   - derived
   - defaulted
   - unknown
   - unsafe_to_default

## Exit criteria

- 三個 golden inputs 通過 schema validation。
- Reference Fixture 可完成 serialize／deserialize round trip。
- unit mismatch、dangling reference、duplicate ID、invalid range 都有失敗測試。
- schema migration 有至少一個前版 fixture 與 rollback test。
- downstream test consumer 能實際讀取 IR；不以「JSON 可產生」作為成功。

---

# 9. G2 — Fixture Geometry Vertical Slice

## 目標

從固定 Engineering IR 產生 Reference Fixture 的 base、cover 與 assembly artifacts。

## 工作

1. 建立 Geometry Backend capability contract。
2. 實作 primitives：box、plate、shell、hole、pocket、boss、cutout、fillet、chamfer、mount。
3. 實作 PCB envelope、USB-C cutout、M3 mounting、removable cover。
4. 建立 deterministic feature ordering 與 structured error handling。
5. 輸出 STEP、STL、glTF 或 web preview format；DXF 只輸出指定 2D section/sketch。
6. 建立 topological naming 風險隔離：內部以 semantic feature ID 對應，避免把 transient face index 當永久識別。

## Exit criteria

- 相同 IR、engine version 與 seed 重跑得到相同 semantic manifest。
- STEP 可由獨立 parser 重新開啟。
- 每個 solid 通過 kernel validity check。
- Reference Case 的主要尺寸符合 tolerance。
- 故意破壞的尺寸、boolean、fillet case 回傳明確 error code。
- golden artifact comparison 通過。

---

# 10. G3 — Rules & Validation

## 目標

用少量可信規則證明工程決策鏈，不追求規則數量。

## Rule governance

每條規則必須包含：

```yaml
rule_id: CNC_MIN_WALL_001
version: 1.0.0
status: approved
source: internal_me_standard
source_revision: 2026-A
owner: mechanical_engineering
scope: {}
condition: {}
severity: error
recommendation: increase_wall
auto_fix: false
effective_date: 2026-09-16
tests:
  positive: []
  negative: []
  boundary: []
```

## 第一批規則

優先完成 20–30 條 Reference Fixture 高價值規則：

- minimum wall。
- hole／thread depth。
- hole aspect ratio。
- internal radius／tool diameter。
- pocket depth／tool access。
- edge clearance。
- PCB clearance。
- connector opening clearance。
- fastener engagement。
- cover removal path。
- component collision。

## 衝突與 waiver

規則衝突不只靠全域 priority。系統必須記錄：

- 被哪一條規則覆蓋。
- 覆蓋理由。
- 決策者。
- 生效範圍。
- 是否需要重新驗證。

Waiver 必須有 ID、owner、理由、到期條件及受影響 artifacts。

## Exit criteria

- 每條規則具有 positive、negative、boundary tests。
- Reference Fixture benchmark 中沒有 false release。
- 報告同時呈現 precision、recall、false-positive count，不只 detection rate。
- 規則更新會觸發相關 golden regression。
- 任一 error 級規則未處置時，成熟度不得升到 PROTOTYPE。

---

# 11. G4 — Module & Constraint Composition

## 目標

證明 Module 可攜帶幾何、介面、clearance 與規則 metadata，並能組成產品。

## 第一批完整 Modules

```text
PCB
USB-C
M3 Fastener
Base
Cover
```

其他 Module 可先只有 metadata，但 capability level 必須標示：

```text
metadata_only
layout_capable
geometry_capable
validated
```

## Import policy

STEP／DXF 自動抽取只可產生可證明的資訊：

- bounding box。
- solid／shell count。
- candidate holes／planar sections。
- file unit（存在時）。
- parser warnings。

Material、loads、supplier、electrical／acoustic property、mount intent 必須來自 datasheet、使用者或工程師確認，並保存 provenance。

## Exit criteria

- 將 PCB／USB-C 拖入 fixture graph 會產生 mount、clearance、opening constraints。
- 移除 Module 會清除或明確標示所有 dependent constraints。
- 不完整 metadata 不會被自動補成虛構工程值。
- capability level 會正確限制 UI、CAD 與 validation 行為。

---

# 12. G5 — Prototype Package & Reproducibility

## 目標

產出可稽核、可重建、誠實標示成熟度的 Prototype Package。

## Package

```text
PROJECT-0001/
├─ requirement.yaml
├─ product_graph.json
├─ engineering_ir.json
├─ assumptions.json
├─ validation_results.json
├─ CAD/
│  ├─ assembly.step
│  ├─ base.step
│  ├─ cover.step
│  └─ preview.glb
├─ Drawing/
│  └─ reference_fixture_draft.pdf
├─ BOM/
│  └─ bom.csv
├─ Reports/
│  ├─ dfm_report.md
│  └─ verification_report.md
└─ release_manifest.json
```

## Manifest 必備資訊

- input hashes。
- artifact hashes。
- schema、engine、library、rule、model、solver versions。
- OS／runtime identity。
- random seed。
- executed validations。
- passed、failed、waived、skipped gates。
- assumptions、unknowns、human sign-offs。
- maturity state。

## Drawing policy

圖面由 Engineering IR／feature metadata 驅動，不從 STEP 猜 critical dimension。第一版只允許固定 Fixture template 與 dimension whitelist，且標示 `DRAFT — ENGINEERING REVIEW REQUIRED`。

## Exit criteria

- 從 clean environment 使用同一 input 可重新產生完整 package。
- manifest 能驗證所有 artifact hash。
- BOM 不從 filename 推測，且 quantity／material／revision 與 IR 一致。
- Drawing 經固定 checklist 或人工 QA，結果寫入 manifest。
- Package 明確標示 `PROTOTYPE`，不含 Production Ready 宣告。

---

# 13. G6 — Guided UI

## 目標

只對已驗證的 vertical slice 建立新人 UI；不先做空殼式通用 Wizard。

## Flow

```text
選擇 Fixture / Enclosure
↓
選擇大致外形
↓
加入 PCB 與 USB-C
↓
回答用途、數量、可拆性與優先目標
↓
檢視 assumptions 與 unknowns
↓
接受或修改有證據的建議
↓
Generate
↓
查看 CAD、規則結果與 Prototype Package
```

## Dynamic Question Engine

問題的排序以資訊價值與安全性決定：

1. `unsafe_to_default` 先問。
2. 會改變架構或製程的問題優先。
3. 可由可靠資料衍生者不問。
4. recommendation 必須附來源與適用範圍。
5. 永遠提供「不知道，交由系統建議」，但 critical unknown 不得因此消失。

## Confidence policy

MVP 不顯示未校準的 60%、85%、92% 等概率。改用：

```text
Verified
Supported
Partially supported
Unknown
Needs engineering review
```

等累積有標註資料後，再以 Brier score、ECE 或適用 calibration 方法證明百分比可信。

## Exit criteria

- 新人可在不輸入 CAD 專業詞的情況下產生 Reference Fixture。
- UI 不提供超出 capability envelope 的選項，或清楚標成 unsupported。
- 生成前必須顯示 assumption review。
- UI 與直接 API 對相同輸入產生等價 IR。
- usability test 保存題數、完成率、錯誤點及人工介入次數。

---

# 14. G7 — Acoustic Thin Slice

## 目標

驗證 Product DNA、Module 與 Constraint Graph 能描述聲學模組；solver 能力獨立分級。

## Scope

```text
Speaker Driver
Front Chamber
Rear Chamber
Outlet
Vent
Mesh
Gasket
Microphone
```

第一層 acceptance 是 graph、sealed-volume geometry 與必要關係，不要求一開始就完成高可信 COMSOL 自動化。

## Solver levels

```text
L0: geometry and parameter report
L1: validated reduced-order model
L2: template-based COMSOL run
L3: mesh-converged engineering simulation with reviewer sign-off
```

COMSOL 授權、API 或 worker 不可用時，停在 L0/L1，系統仍可繼續其他 Gate；不得以近似模型冒充 L2/L3。

## Exit criteria

- Acoustic golden case 與 Fixture 使用相同 core IR／graph infrastructure。
- sealed volume、outlet connectivity、leak assumptions 可被驗證。
- 結果標示 solver level、mesh、boundary、material、frequency range 與 limitations。
- 每個數值結果可追溯到 solver input 與版本。

---

# 15. G8 — Robot Thin Slice

## 目標

驗證 Module composition、assembly relationship 與 layout constraints 可跨到 Robot Car。

## Scope

```text
Chassis
Motor
Wheel
Battery
Controller
Camera / Sensor
Cover
```

第一層不宣稱完成 mechanism synthesis、kinematics、wiring harness 或 safety structure。

## Exit criteria

- Robot golden case 與 Fixture 共用 ID、unit、provenance、graph、rule-result 及 manifest contracts。
- motor／wheel、battery／controller、sensor／cover 關係可表達並驗證 referential integrity。
- layout collision、clearance、mounting zone 可執行。
- 缺少 kinematics、cable 或 safety validation 時，maturity 不得超過 CONCEPT。

---

# 16. G9 — Hardening & Expansion

此 Gate 沒有固定終點；每次只增加一個經核准的 capability slice。

候選擴充順序：

1. Reference Fixture 多尺寸、多 connector。
2. 更多 CNC 材料與製程規則。
3. Sheet Metal vertical slice。
4. Plastic enclosure vertical slice。
5. Acoustic solver level 提升。
6. Robot assembly／kinematics。
7. Cost、thermal、structural、optimization。

每次擴張都必須同步增加：

- supported envelope。
- golden cases。
- rules 與來源。
- negative／boundary tests。
- UI capability filtering。
- manifest evidence。
- rollback／migration path。

---

# 17. Verification strategy

## 17.1 Benchmark corpus

Benchmark 必須版本化並分成：

```text
golden
negative
boundary
regression
holdout
```

每個 case 保存 input、oracle、適用 envelope、expected validations 與 reviewer。

## 17.2 KPI 定義

不得只寫「成功率 90%」。每個 KPI 必須定義：

- numerator／denominator。
- corpus version。
- seed 與 runtime version。
- timeout。
- pass definition。
- confidence interval 或樣本量。
- false positive／false negative。

核心指標：

| 指標 | 定義 |
|---|---|
| Generation pass rate | 在固定 supported corpus 中，產生 kernel-valid、尺寸合格 artifact 的比例 |
| Validation recall | 已標註缺陷被偵測的比例 |
| Validation precision | 系統提出的缺陷中真正成立的比例 |
| False release | 存在 error 級已知缺陷卻升級成熟度的 case 數；目標為 0 |
| Deterministic replay | 相同 manifest 可重建相同 semantic outputs 的比例 |
| Manual intervention | 每個成功 design run 需要人工修正的次數 |
| Question count | 從初始 intent 到可生成 IR 的人工問題中位數 |

## 17.3 Test layers

```text
Unit tests
→ Schema / contract tests
→ Geometry property tests
→ Rule tests
→ Golden regression
→ Adapter integration tests
→ End-to-end design run
→ Artifact visual / engineering review
```

---

# 18. Safety and human responsibility

所有 design run 在生成前顯示：

- 使用者提供的事實。
- 系統衍生值。
- 使用的 defaults。
- 未知值。
- unsafe-to-default 值。
- 不在驗證範圍的能力。

下列類別不得由本系統自動升級為 Production Ready：

- Helmet、medical/hearing、human safety device。
- Underwater vehicle、pressure vessel。
- Robot safety structure。
- 法規管制、生命安全、重大財產風險產品。

安全 Gate 需要具名 reviewer、review scope、evidence、時間與 signature reference。LLM 的「看起來合理」不是簽核。

---

# 19. Security, privacy and permissions

若系統接受檔案上傳或進入多使用者環境，必須完成：

- auth 與 RBAC。
- project／tenant isolation。
- signed artifact access。
- encryption in transit／at rest。
- secrets management。
- audit log。
- file type、size、complexity、timeout limits。
- CAD parser sandbox worker。
- malware scan 與 archive bomb 防護。
- retention／deletion policy。
- prompt injection 與 untrusted metadata 隔離。

在這些能力完成前，部署範圍固定為受控的 internal single-user prototype。

---

# 20. Runtime and operations

正式環境需要：

- API health／readiness checks。
- worker queue、retry、timeout、cancel。
- job correlation ID。
- structured logs、metrics、traces。
- artifact store backup／restore。
- database migration／rollback。
- adapter circuit breaker。
- resource quota。
- incident runbook。
- software deploy rollback。

「設計 Package Release」與「軟體版本 Release」是兩套不同流程，名稱、狀態與 audit log 不得混用。

---

# 21. Definition of Done

一個 work item 只有在以下條件全部成立時才是 Done：

- 需求與 acceptance 可追溯。
- 修改前 baseline 已記錄。
- 程式、schema、tests、docs 同步更新。
- 相關自動測試通過。
- golden／negative／boundary regression 通過。
- 產出的 artifacts 已檢查，不只確認檔案存在。
- 沒有新增未記錄的 assumption 或 risk。
- migration／rollback boundary 明確。
- `PROJECT_STATE.md` 與 `WORK_QUEUE.yaml` 已更新。
- evidence 可由另一個 Codex session 重跑。
- commit scope 單一且訊息使用簡潔英文。

Gate 完成還必須額外具備：

- Gate exit criteria 全部通過。
- 未完成項目已移出 Gate 或正式登記 blocker。
- architecture／decision／risk 文件與實作一致。
- 下一 Gate 的 entry conditions 已滿足。

---

# 22. 初始 Work Queue

```text
G0-REP-001  建立 repository 與狀態檔
G0-ENV-001  鎖定 Python / Node / CAD dependencies
G0-CAD-001  CadQuery Reference Case spike
G0-DRW-001  FreeCAD TechDraw headless spike
G0-SIM-001  COMSOL license / API / batch feasibility decision
G0-CI-001   建立 baseline CI

G1-IR-001   定義 unit / coordinate / ID / provenance primitives
G1-IR-002   定義 Engineering IR schema
G1-IR-003   建立 Reference Fixture golden case
G1-MIG-001  建立 schema migration contract

G2-CAD-001  實作 geometry capability contract
G2-CAD-002  產生 fixture base
G2-CAD-003  產生 cover / fasteners / cutout
G2-CAD-004  輸出與重新載入 artifacts

G3-RUL-001  建立 rule schema / governance / waiver
G3-VAL-001  建立 geometry / collision / clearance validators
G3-VAL-002  建立 CNC DFM rule pack
G3-BEN-001  建立 benchmark metrics

G4-MOD-001  建立 Module capability levels
G4-MOD-002  PCB / USB-C / M3 composition
G4-IMP-001  建立 safe STEP / DXF metadata extraction

G5-PKG-001  建立 manifest 與 content hashes
G5-BOM-001  建立 BOM exporter
G5-DRW-001  建立 fixed-template draft drawing
G5-REP-001  Clean-environment reproducibility test

G6-UI-001   建立 capability-driven guided flow
G6-QST-001  建立 question ordering / abstention
G6-E2E-001  UI-to-IR-to-package end-to-end test

G7-ACO-001  Acoustic graph / sealed-volume thin slice
G8-ROB-001  Robot layout / assembly-relationship thin slice
```

建立 repository 後，這份清單必須轉成有正式 dependencies 與 acceptance 的 `WORK_QUEUE.yaml`；不得直接把全部項目同時標成 `in_progress`。

---

# 23. Codex 啟動指令範本

後續每次要求 Codex 繼續施工時，可使用：

```text
請依 v2.0 Codex Continuous Execution Plan 繼續施工。

先讀 AGENTS.md、execution/PROJECT_STATE.md、execution/WORK_QUEUE.yaml、
execution/BLOCKERS.yaml 與最近 handoff；檢查 Git 與現有測試。

選擇依賴已滿足的最高優先 ready work item，先跑 baseline，
再完成實作、驗證、狀態更新與 commit。只在需要新產品決策、
授權、憑證、安全假設或工程簽核時停止詢問。
```

Gate review 指令：

```text
請審查目前 Gate 的所有 exit criteria。
逐項提供程式碼、測試、artifact 或決策紀錄證據；
未通過項目不得標示完成。若全數通過，更新 PROJECT_STATE、
LAST_VERIFICATION 與下一 Gate entry conditions。
```

---

# 24. 主要風險與 contingency

| 風險 | Trigger | Contingency |
|---|---|---|
| CAD boolean／fillet 不穩定 | golden case 間歇失敗 | 縮小參數 envelope、固定 feature ordering、保留可診斷中間 shape |
| FreeCAD headless 圖面不穩定 | CI 無法重現 PDF | 固定 container／版本；降為 SVG/PDF template + manual QA |
| COMSOL 授權或 worker 不可用 | feasibility spike 失敗 | Acoustic 停在 L0/L1；核心工程繼續 |
| 規則品質不足 | precision／recall 不合格 | 減少規則範圍、補 SME review 與 test vectors |
| Product DNA 過度抽象 | 三案例需要大量例外 | 收斂 core vocabulary；以 extension SDK 處理 domain-specific capability |
| Schedule illusion | 大量工作同時 in progress | WIP limit = 1 vertical work item；以 Gate evidence 而非百分比報進度 |
| AI hallucination | unknown 被填入無來源值 | schema 強制 provenance／unknown／abstain |
| Artifact 不可重建 | replay hash 或 semantic diff 失敗 | pin versions、保存 manifest、禁止成熟度升級 |
| 安全宣稱過度 | 未簽核 artifact 被稱為 released | maturity state 強制水印與 Gate policy |

每項風險在正式 repository 中必須增加 owner、probability、impact、review cadence 及目前狀態。

---

# 25. v1.0 審查意見處置

| 審查問題 | v2.0 處置 |
|---|---|
| 90 天與三案例範圍不可成立 | 移除日曆；Fixture full slice，Acoustic／Robot thin slices |
| UI 排在工程能力之前 | UI 移至 G6，依賴 G1–G5 |
| Validation 與 RELEASED 矛盾 | 導入 maturity states；Codex 自動化上限為 PROTOTYPE |
| 外部依賴沒有 fallback | G0 feasibility gates + adapter fallback |
| 執行環境與安全邊界未決 | 加入 supported envelope、deployment、security Gate |
| JSON success 無法證明語意 | 加入 schema contract、consumer、golden、migration tests |
| Product = Data 過度承諾 | 分離 data composition 與 code capability extension |
| 150+ rules 是 vanity metric | 改為少量高價值、可追溯且有測試的規則 |
| KPI 不可重現 | 定義 corpus、分母、precision／recall、false release、replay |
| Confidence 百分比未校準 | 改用 evidence／coverage level；校準後才顯示概率 |
| STEP 無法提供完整 drawing intent | Drawing 由 IR metadata 驅動，固定模板 + QA |
| 上傳檔不能推斷完整 metadata | 限制為可證明的幾何抽取，其他資料要求來源 |
| 多 CAD backend 過度設計 | 第一版固定 CadQuery／OCC；第二 adapter 延後 |
| 缺 traceability／reproducibility | 導入 immutable manifest、hash、version、seed |
| 缺持續施工機制 | 新增 Codex control plane、work queue、handoff、fixed point |

---

# 26. 最終成功定義

第一個重大成功不是「支援 100 種產品」，而是：

> 一名不懂 CAD 的使用者，可以在明確的 supported envelope 內，透過 Guided UI 建立 CNC Fixture／Enclosure；系統能產生可重新開啟的 CAD、可追溯的規則結果、BOM、draft drawing 與完整 manifest，而且相同輸入可以由另一個 Codex session 重新建構並得到一致結果。

第二個重大成功是：

> Acoustic 與 Robot thin slices 確實重用核心 IR、Module、Graph、Validation Result 與 Manifest，而不是各自長出一套硬編碼 Wizard。

第三個重大成功才是：

> 在工程師審核、規則治理、solver fidelity 與安全 Gate 成熟後，逐步把 `PROTOTYPE` 能力提升到 `ENGINEERING_REVIEWED`，再由組織流程決定是否 `RELEASED`。

---

# 27. 版本紀錄

## v2.0 — 2026-09-16

- 保留 v1.0 願景，另建可執行版本。
- 移除 90 天與週次排程。
- 改為 Codex 可持續、可中斷恢復的 Gate DAG。
- 將 Fixture 設為完整 vertical slice；Acoustic、Robot 設為後續 thin slices。
- 新增 supported envelope、maturity states、schema contract、規則治理、benchmark、reproducibility、安全、部署、fallback 與 Definition of Done。
- 納入獨立反方審查的 blocking／high-severity findings。

