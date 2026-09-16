# MEGIS — 機械工程生成式智慧系統（Mechanical Engineering Generative Intelligence System）
## v3.0 — 嚴謹版連續施工藍圖

**版本：v3.0-claude-code**  
**日期：2026-09-17**  
**文件狀態：可執行藍圖 — 主要施工依據（規範性文件）**  
**執行主體：施工 Agent（ChatGPT Codex 或 Claude Code；依 D6 決策，誰施工誰負責自我審查）＋ 使用者（產品決策與否決權）**  
**前版：v2.0 Codex 連續施工計畫（保留，不覆寫）；v1.0 總體藍圖（封存於 `MEGIS_Blueprint/OLD/`）**  
**繼承原則：v2.0 的所有決策、Gate、work item ID、不變量與限制在 v3.0 中全部保留；v3.0 只做「擴充、精確化、補齊可驗證機制」，任何收斂或推翻均在第 29 章逐條說明理由。**

---

# 目錄

- 0. 文件目的、規範用語與導入規則
- 1. 核心決策
- 2. 支援邊界
- 3. 系統不變量與強制機制
- 4. 架構契約
- 5. Agent 連續施工控制面
- 6. Gate 依賴圖與通用規則
- 7. UX-0 — 誠實的使用者體驗原型
- 8. G0 — 基礎建設與可行性
- 9. G1 — 工程契約與黃金案例
- 10. G2 — 治具幾何垂直切片
- 11. G3 — 規則與驗證
- 12. G4 — 模組與限制條件組合
- 13. G5 — 原型套件與可重現性
- 14. G6 — 引導式介面與 AI 輔助
- 15. G7 — 聲學薄切片
- 16. G8 — 機器人薄切片
- 17. G9 — 強化與擴充
- 18. 驗證策略
- 19. 工程知識治理
- 20. AI 治理
- 21. 安全與人的責任
- 22. 資訊安全、隱私與供應鏈
- 23. 使用者體驗原則
- 24. 執行環境、營運與資料管理
- 25. 開工條件與完成定義
- 26. 完整工作佇列
- 27. Agent 指令範本
- 28. 風險登錄表
- 29. 審查意見處置與追溯（v1 → v2 → v3）
- 30. 最終成功定義
- 附錄 A. 範本（工作項目、交接、審查、ADR、決策紀錄、豁免、清單、寫入鎖、阻塞）
- 附錄 B. 參考案例參數檔（機器可讀）
- 附錄 C. 版本紀錄

---

# 0. 文件目的、規範用語與導入規則

## 0.1 文件目的

本文件把 v1.0 的產品願景，經 v2.0 的 Gate 化，進一步精確化為**可由 AI Agent 持續施工、由獨立 Agent 與具名工程師驗證、可中斷恢復、可稽核追溯**的工程計畫。

本版不使用「90 天」、「第幾週」或固定日曆作為完成依據。進度只由可觀察的 Gate 決定：

```text
前一 Gate 的驗收證據完整
↓
施工者以全新 session 自我審查、重跑證據並判定 passed
↓
記錄 Gate 決策（使用者可隨時否決）
↓
後一 Gate 才可開始
↓
外部依賴未就緒時走已決策的 fallback
↓
每次施工都留下可恢復狀態
```

## 0.2 「連續施工」的定義

「連續施工」不是要求單一對話永不中斷，而是：

- 任一工作階段結束後，下一個 Agent 執行階段可以只從 repository 中的狀態檔恢復。
- 每個工作單元都有輸入、輸出、驗收、測試、風險及回滾邊界。
- 不依賴聊天紀錄保存關鍵決策；所有決策以 ADR 或 sign-off 形式存在於 repository。
- 不以程式碼已寫完作為完成；必須有可重跑的驗收證據。
- 「可重跑」的判定標準是 **semantic fingerprint 一致**，不是檔案 byte 一致（§4.12）。
- 【D6】誰施工誰審查；但審查必須在全新 session、乾淨 checkout 中重跑，不得沿用施工時的上下文或暫存結果（§5.7）。

## 0.3 規範用語

| 用語 | 意義 |
|---|---|
| **必須／不得** | 強制要求；違反即視為 Gate 失敗或 work item 未完成 |
| **應／不應** | 強烈建議；偏離時必須在 ADR 中記錄理由 |
| **可** | 允許，不需記錄 |
| **【v3】** | 標示 v3.0 相對 v2.0 新增或修改的內容 |

## 0.4 文件與規則優先順序

發生衝突時，依下列順序決定（上者優先）：

1. 法規、安全與使用者明確指示。
2. `AGENTS.md`（repository 邊界、工作區、網路、push 規則）。
3. 本藍圖的系統不變量（第 3 章）與安全章節（第 21 章）。
4. 已核准的 ADR（`docs/DECISIONS.md`）與 sign-off（`execution/signoffs/`）。
5. 本藍圖其他章節。
6. `execution/` 狀態檔。
7. Handoff、review 報告與其他說明文件。

若狀態檔與 Git history／可重跑測試結果矛盾，**以 Git history 與重跑結果為準**，並修正狀態檔。

## 0.5 名詞定義

| 名詞 | 定義 |
|---|---|
| Gate | 一組有 entry criteria、exit criteria 與自我審查（全新 session）的能力里程碑 |
| Work item | Gate 內可在單一施工循環產生驗收證據的最小工作單元 |
| Evidence | 可由第三方重跑或查驗的測試結果、製品、決策紀錄或簽核（§5.12） |
| Fixed point | 最後一個所有驗證皆綠的 commit |
| Supported envelope | 系統宣稱已驗證的產品、參數、製程與輸出範圍 |
| Maturity | 單一 Design Run 的工程成熟度；**只能由 evaluator 計算** |
| Classification | 製品用途類別：`DESIGN_RUN`、`FEASIBILITY_SPIKE`、`UX_DEMO`、`BENCHMARK_CASE`、`TEST_FIXTURE` |
| Golden case | 輸入、預期輸出與 oracle 均經核准並版本化的基準案例 |
| Byte hash | 檔案原始 bytes 的 SHA-256，用於完整性 |
| Semantic fingerprint | 正規化工程語意內容的 SHA-256，用於可重現性 |
| Waiver | 對特定規則失敗的具名、限範圍、有到期條件的豁免 |
| Sign-off（決策紀錄） | 對特定範圍與證據所做的決定紀錄；依 D6 由施工 Agent 自我審查後記錄，使用者保有否決權；`engineering_review` 類型仍限具名工程師 |
| Builder（施工者） | 修改程式與狀態檔的 Agent |
| Reviewer（審查者） | 依 D6 即為該項目的施工者本身，但必須以全新 session 執行審查 |
| Claim | Builder 對 work item 的寫入鎖 |
| ADR | Architecture/Any Decision Record，決策紀錄 |
| BCR | Blueprint Change Request，藍圖變更流程 |
| SME | Subject Matter Expert，領域工程專家；依 D6 目前不設置，由施工者以可查證的公開資料替代 |
| IR | Engineering Intermediate Representation |

## 0.6 【v3】對既有 repository 的導入規則

本藍圖與施工進度無關，適用於從零開始的 repository，也適用於已依 v2.0 施工中的 repository。導入既有 repository 時：

1. **已 `done` 的 work item 與已 `accepted` 的 Gate 不重開。**
2. v3.0 在已 accepted Gate 中新增的要求，以 **V3 Conformance lane（`V3C-*` work items，§26.1）** 補足；V3C 項目掛在當前 active Gate 之下執行，避免違反「accepted Gate 不得含未完成項目」的控制面規則。
3. V3C 項目完成前，下一個 Gate 不得 accepted。
4. 導入本身是一個 BCR（§5.10），以 `V3C-BCR-001` 執行。
5. 在全新 repository 中，V3C 項目的內容直接視為所屬 Gate 的一般 work item（對應關係見 §26.1）。

---

# 1. 核心決策

## 1.1 GO：採 Gate 驅動施工

產品方向維持：

> 將資深 Mechanical、Acoustic、Manufacturing Engineer 的工程判斷，轉成零工程背景使用者也能操作的 Guided Generative Engineering System。

首要建設目標不是「讓 AI 自由畫 3D」，而是建立：

```text
Engineering Data Model
→ Deterministic Rules
→ Constrained Geometry
→ Validation Evidence
→ Guided UI
→ AI Assistance（受 schema 約束、可棄權、可離線降級）
```

AI 在此順序中位於最後，原因是：前五層決定「什麼是正確的」，AI 只負責「讓人更容易表達意圖與理解結果」。沒有前五層，AI 的輸出無法被驗證。

## 1.2 【v3】使用者與角色

| 角色 | 描述 | 系統對其承諾 | 系統不承諾 |
|---|---|---|---|
| 新手設計者（Novice Designer） | 無 CAD／機構背景，需要一個可加工的外殼或治具 | 以非專業語言完成設計；清楚看到假設、未知與限制 | 不承諾產出可直接量產的設計 |
| 具名工程師（Mechanical Engineering Reviewer） | 【D6】目前不設置；日後指定才啟用 | 可追溯的規則結果、假設、來源、manifest；可簽核或退回 | 未指定前，系統不得產出 `ENGINEERING_REVIEWED` |
| 規則作者（Rule Author） | 【D6】由施工 Agent 擔任 | 規則 schema、測試框架、影響分析 | 不得在無可查證來源下核准規則 |
| 維運者（Operator） | 在本機維護環境 | 可重建環境、健康檢查、備份還原 | 不提供多租戶管理 |
| 施工 Agent（Builder） | 施工，並依 D6 以全新 session 自我審查 | 清楚的 work queue、驗收條件、停止條件 | 不授權 push、購買、`engineering_review` 簽核 |
| 使用者 | 產品決策與最終否決 | 決策包、審查報告、成熟度與限制說明 | 不要求使用者做工程審查 |

## 1.3 第一條垂直切片：CNC 治具／電子外殼（CNC Fixture / Electronics Enclosure）

第一個完整、可驗收的產品路徑為：

> **CNC Fixture / Electronics Enclosure**

v2.0 固定的 Reference Case 保留不變：

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

【v3】上述 8 項不足以成為可機器驗證的 golden case。v3.0 以附錄 B 的完整參數檔補齊，規則如下：

- 每個參數必須帶來源（provenance）：`user`、`derived`、`defaulted`、`researched`、`database`、`engineer_override`、`llm_proposed`、`unknown`。
- `defaulted` 值是**提議預設**，必須在 `G1-REQ-001` 由施工 Agent 依 §9.1 查證並記錄來源後核准；`approved_by` 填入施工 Agent 身分與決策紀錄 ID。
- 【D8】`unknown` 值（PCB 尺寸、擺放方式、USB-C 位置等）由施工 Agent 上網研究，選擇最適合且有公開機械圖面或 datasheet 支撐的方案，來源記為 `researched`，附 URL 與取用日期（§9.1）。
- 任一 `unknown` 未解決前，參考治具 golden case 不得標為 `done`。
- Agent 不得把提議值或研究值改標為 `user`。

【v3】Reference Case 完整參數摘要（詳細見附錄 B）：

| 分類 | 參數 | 提議值 | 來源 | 待確認重點 |
|---|---|---|---|---|
| 外形 | 外尺寸 L × W × H | 120 × 80 × 35 mm（base + cover 合計） | user | — |
| 外形 | Base 高 / Cover 厚 | 29 mm / 6 mm | defaulted | 分割面位置 |
| 外形 | 外部垂直稜角 | R3 mm | defaulted | 外觀需求 |
| 外形 | 內腔垂直角 | R ≥ 3.2 mm | derived | 由 Ø6 mm 端銑刀 + 0.2 mm 餘量推導 |
| 材料 | 材料／回火 | Aluminum 6061-T6 | user / defaulted | 回火狀態 |
| 製程 | 製程／裝夾 | 3-axis CNC，≤ 2 次裝夾 | user / defaulted | 加工廠能力 |
| 壁厚 | 側壁／底厚／上蓋厚 | 2.0 / 2.0 / 2.0 mm | user / defaulted / defaulted | 剛性需求 |
| 公差 | 一般公差 | ISO 2768-mK | defaulted | 客戶慣例 |
| PCB | PCB-A 外形 | unknown（提議 100 × 60 × 1.6 mm） | unknown → researched | **施工者上網研究決定（§9.1）** |
| PCB | PCB-B 外形 | unknown（提議 60 × 40 × 1.6 mm） | unknown → researched | **施工者上網研究決定（§9.1）** |
| PCB | 堆疊方式 | unknown（提議上下疊層） | unknown → researched | **改變架構，最先研究決定（§9.1）** |
| PCB | 零件最大高度 top／bottom | unknown（提議 12 / 2 mm） | unknown → researched | **施工者上網研究決定（§9.1）** |
| PCB | 安裝 | M3 standoff；孔位依 PCB 檔 | defaulted | 孔位座標 |
| PCB | PCB 邊至內壁 | ≥ 1.0 mm | defaulted | 組裝公差 |
| USB-C | 所屬 PCB／所在面／高度 | unknown（提議 PCB-A／−X 面） | unknown → researched | **施工者上網研究決定（§9.1）** |
| USB-C | 面板開口 | 依 receptacle 內縮距離決定（§11.2 規則 `CON_USBC_OPEN_001`） | derived | 必須以實際零件 datasheet 確認 |
| 緊固 | 上蓋螺絲 | 4 × M3 × 8 內六角圓柱頭（ISO 4762） | defaulted | 長度 |
| 緊固 | Base 內螺紋 | 角落 boss 內直接攻牙 M3 × 0.5，嚙合長 ≥ 2.0 D（6 mm） | defaulted | 鋁材攻牙 vs 螺紋襯套 |
| 緊固 | 角落 boss | Ø7 mm，與側壁一體 | defaulted | 2 mm 側壁不足以直接攻 M3 |
| 緊固 | Cover 通孔 | Ø3.4 mm（ISO 273 medium） | defaulted | — |
| 緊固 | Cover 沉頭孔 | Ø6.5 × 3.3 mm | defaulted | 頭部齊平需求 |
| 組裝 | 方向 | 由上方裝入，無運動機構 | user | — |
| 輸出 | 製品 | assembly/base/cover STEP、STL、DXF section、BOM、DFM report、drawing draft、manifest | user | — |

Acoustic Module 與 Robot Car 在核心能力穩定後，以 thin slice 驗證 Product DNA、Module、Constraint Graph 能否跨領域重用；在各自 Solver、Assembly 與驗證能力完成前，不宣稱為完整工程設計。

## 1.4 成熟度狀態（Maturity）

```text
DRAFT
→ CONCEPT
→ PROTOTYPE
→ ENGINEERING_REVIEWED
→ RELEASED
```

本計畫可由 Agent 自動推進至 `PROTOTYPE`。`ENGINEERING_REVIEWED` 需要合格工程師簽核；`RELEASED` 還需要適用的製造、品質、法規與組織放行程序。

任何未通過的 Gate、waiver、未知假設或人工待確認項目，都必須出現在輸出文件與 `release_manifest.json`，不得以 `RELEASED` 命名。

【v3】各狀態的**必要且充分**條件（由 `megis.maturity` evaluator 計算，table-driven tests 覆蓋每一列）：

| 狀態 | 必要條件（全部成立） |
|---|---|
| `DRAFT` | Requirement 通過 schema validation |
| `CONCEPT` | DRAFT ＋ Engineering IR 通過 schema 與 referential integrity ＋ 無未解決 `unsafe_to_default` ＋ layout／collision 檢查已執行且無 error |
| `PROTOTYPE` | CONCEPT ＋ geometry kernel-valid ＋ 所有適用 rule packs 已執行 ＋ 0 個未處置 error（處置 = 修正或有效 waiver） ＋ 所有 warning 已 disposition ＋ 無 critical unknown ＋ package semantic fingerprint 可重現 ＋ drawing QA 結果已記錄 ＋ 所有 capability 均在 supported envelope 內 |
| `ENGINEERING_REVIEWED` | PROTOTYPE ＋ 具名 Mechanical Engineering Reviewer 的 `engineering_review` sign-off，範圍涵蓋所有 artifacts |
| `RELEASED` | ENGINEERING_REVIEWED ＋ 外部組織放行紀錄的 reference（MEGIS 只記錄，不執行放行） |

【v3】成熟度規則：

- 任何輸入、規則版本、engine 版本或 waiver 變更，都必須使該 Design Run 的成熟度重新計算；已簽核的 `ENGINEERING_REVIEWED` 在輸入變更後自動失效並回到重新計算結果。
- Waiver 到期時，受影響的 Design Run 成熟度必須重新計算。
- 屬於第 21 章禁止類別的產品，evaluator 上限為 `CONCEPT`（Robot）或 `PROTOTYPE`，且永不自動輸出 `RELEASED`。
- 【D6】目前未指定具名工程師，因此 `ENGINEERING_REVIEWED` 與 `RELEASED` 不可達；自我審查最多支撐到 `PROTOTYPE`，所有輸出必須標示「未經具名工程師審查」。

## 1.5 【v3】製品分類（Classification）

| 分類（Classification） | 用途 | 可否有成熟度 |
|---|---|---|
| `DESIGN_RUN` | 由 IR 驅動的正式設計執行 | 可，且必須由 evaluator 計算 |
| `FEASIBILITY_SPIKE` | 驗證外部工具可行性 | 不可，`maturity` 必須為 `null` |
| `UX_DEMO` | UX-0 合成展示 | 不可 |
| `BENCHMARK_CASE` | 驗證語料 | 不可 |
| `TEST_FIXTURE` | 單元／契約測試輸入 | 不可 |

Control-plane verifier 必須掃描 repository 內所有 `manifest.json`：`classification != DESIGN_RUN` 且 `maturity != null` 即失敗。

## 1.6 【v3】刻意不追求的目標（Anti-goals）

以下為刻意不追求的目標，任何 work item 不得以此為成功指標：

- 支援的產品種類數量。
- 規則數量。
- LLM 對話的流暢度或「看起來像工程師」。
- 未經校準的信心百分比。
- 把任何輸出宣稱為可量產、已驗證安全或符合法規。

---

# 2. 支援邊界（Supported envelope）

## 2.1 第一條垂直切片的支援範圍

| 項目 | 支援範圍 |
|---|---|
| 產品 | 小型 CNC 電子治具／外殼 |
| 外形 | 矩形、單腔、可拆上蓋 |
| 尺寸 | 50–300 mm 主尺度；【v3】高度 15–120 mm；長寬比 ≤ 6:1 |
| 材料 | Aluminum 6061（【v3】T6 回火） |
| 製程 | 3-axis CNC；【v3】≤ 2 次裝夾 |
| 零件 | PCB、USB-C、M3 fastener、cover、base；【v3】PCB ≤ 2 片、USB-C ≤ 2 個、M3 ≤ 16 支 |
| 幾何 | box、plate、shell、hole、pocket、boss、cutout、fillet、chamfer、mount；【v3】tapped hole（cosmetic thread）、counterbore |
| 組裝 | 由上方裝入、螺絲固定、無運動機構 |
| 驗證 | schema、unit、geometry、collision、clearance、wall、basic CNC DFM |
| 圖面 | 固定模板、白名單尺寸、人工 QA |
| 輸出 | STEP、STL、2D DXF section、BOM、DFM report、manifest |
| 【v3】平台 | Windows 10/11 x64；Windows 11 ARM64 經 x64 emulation；CI 為 GitHub-hosted Windows x64；其他平台未驗證 |
| 【v3】部署 | 本機 single-user，服務只綁定 `127.0.0.1` |

## 2.2 明確不支援

- 自由曲面、Class-A surface、拓樸最佳化。
- 完整 GD&T 自動決策。
- 自動安全認證或 Production Ready 宣告。
- 注塑、鈑金、壓鑄、多軸加工。
- 疲勞、衝擊、非線性結構、完整熱流耦合。
- 任意 STEP/DXF 自動推斷材料、載荷、供應商或物理屬性。
- 任意新產品只靠 YAML 即獲得新幾何或新求解能力。
- 完整 Creo 相容、完整 COMSOL 取代。
- 【v3】防水／IP 等級、EMI 屏蔽、散熱能力、跌落與振動宣稱。
- 【v3】陽極處理、表面處理造成的尺寸變化補償。
- 【v3】LLM 直接輸出幾何、尺寸或規則判定結果。
- 【v3】多使用者、雲端部署、外部分享連結。

## 2.3「產品即資料」（Product = Data）的精確定義

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

## 2.4 【v3】支援範圍的機器可讀形式與變更程序

- Supported envelope 必須同時存在於 `docs/SUPPORTED_ENVELOPE.md`（人讀）與 `config/envelope/*.yaml`（機器讀），並有測試確保兩者一致。
- UI、API、Question Engine、geometry adapter 與 maturity evaluator 必須讀取同一份機器可讀 envelope，不得各自硬編碼範圍。
- 超出 envelope 的輸入必須回傳 `MEGIS-ENV-*` 結構化錯誤或標示 `unsupported`，不得靜默夾限（clamp）。
- 擴張 envelope 的程序：`envelope_change` sign-off → ADR → 新增 golden／boundary／negative cases → 規則與來源 → UI filtering 測試 → migration path → 自我審查報告。缺任一項不得合併。

---

# 3. 系統不變量與強制機制

## 3.1 不變量

以下不變量適用於每一階段。v2.0 的 1–10 條保留，v3.0 新增 11–18 條，並為每一條指定強制機制——**沒有強制機制的不變量只是願望**。

| # | 不變量 | 強制機制 | 最早生效 Gate |
|---|---|---|---|
| 1 | LLM 只提出 Design Intent、問題、候選方案及解釋；不能成為幾何、物理或放行的唯一真相 | `llm_proposed` provenance；IR confirmed 區拒絕未確認值的 schema 測試；AI 模組無 geometry／rules 寫入 API（import 邊界檢查） | G1（schema）、G6（執行） |
| 2 | 所有工程數值必須有明確 unit，不接受無單位裸值 | Quantity 型別；schema 拒絕裸數值；property tests | G1 |
| 3 | 所有衍生決策必須記錄來源：`user`、`derived`、`defaulted`、`database`、`engineer_override`，【v3】及 `llm_proposed`、`researched`（附 URL 與取用日期） | Provenance 必填欄位；schema 測試 | G1 |
| 4 | 所有未知值保持 `unknown`；不得由模型虛構 | `unknown` 為一級型別；AI hallucination KPI；golden case 檢查 | G1、G6 |
| 5 | 【v3 精確化】每次 Design Run 必須可以由固定輸入與固定版本重建，判定標準為 semantic fingerprint 一致 | Replay test；CI 雙次執行比對 | G0（spike）、G5（package） |
| 6 | 外部工具失敗時，系統回傳結構化 failure，不輸出看似成功的 artifact | Error taxonomy（§4.10）；故障注入測試；失敗時 artifact 目錄不得含成功 manifest | G2 |
| 7 | 每個規則都有來源、版本、適用範圍、測試與 owner | Rule schema 必填；規則無三類測試時 CI 失敗 | G3 |
| 8 | 每個 Gate 的失敗必須阻止成熟度升級，除非有具名 waiver 與人工簽核 | Maturity evaluator table tests | G3 |
| 9 | UI 只能引導使用者進入目前已驗證的 capability envelope | UI 讀取 envelope config；E2E 測試嘗試越界輸入 | G6 |
| 10 | 任何宣稱「完成」都必須指向可重跑的測試或驗收證據 | Control-plane verifier 檢查 evidence 路徑存在與 verification 狀態 | G0 |
| 11 | 【v3】成熟度是計算結果，不是輸入欄位 | Manifest 掃描（§1.5）；evaluator 為唯一寫入者 | G0（掃描）、G3（evaluator） |
| 12 | 【v3】同一時間只有一個 Builder 對 `main` 與 `execution/` 狀態檔有寫入權 | `execution/AGENT_CLAIM.json`；verifier 檢查 | G0 |
| 13 | 【v3】浮點幾何量比較一律使用具名容差，禁止 `==` | 集中容差模組；lint 規則／code review checklist | G1 |
| 14 | 【v3／D6】誰施工誰審查，但審查必須在全新 session 與乾淨 checkout 重跑，不得沿用施工 session 的輸出作為證據 | 審查報告記錄審查 session ID ≠ 施工 session ID、乾淨 checkout commit 與重跑輸出；CI 對同一 commit 全綠；verifier 檢查 | G0 |
| 15 | 【v3】任何對外動作（push、發布、呼叫雲端 LLM、上傳檔案）必須有使用者授權紀錄 | `AGENTS.md`；ADR；AI provider adapter 預設關閉 | G0 |
| 16 | 【v3】Golden 預期值的變更必須是獨立 commit，附差異報告並經自我審查（全新 session）核准 | `golden-update` commit 慣例；verifier 檢查 golden 變更 commit 不含其他程式變更 | G1 |
| 17 | 【v3】單位內部表示唯一（mm、deg、g、N、s、°C），轉換只發生在輸入／輸出邊界 | Quantity 型別與邊界轉換測試 | G1 |
| 18 | 【v3】系統不得以沉默方式縮小或夾限使用者輸入 | 越界輸入測試必須回傳錯誤或 `unsupported` | G2 |

## 3.2 【v3】不變量違反的處置

- 在 CI 中偵測到的違反：CI 必須失敗，不得以 retry、skip 或 `xfail` 讓其變綠。
- 在已合併程式中發現的違反：立即建立 `BLOCKERS.yaml` 條目，受影響 Design Run 成熟度重新計算，相關 Gate 若已 accepted，須由施工者以全新 session 評估是否以 V3C／修補工作項目處理。
- 不變量本身的修改只能透過 BCR（§5.10）。

---

# 4. 架構契約（Architecture contracts）

## 4.1 主資料流

```text
Human Intent
↓（AI Intent Extractor：可棄權；離線時改走結構化表單）【v3】
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
Artifacts + Evidence（byte hash + semantic fingerprint）【v3】
↓
Maturity Evaluation【v3】
↓
Prototype Package
```

## 4.2 【v3】分層與模組邊界

建議 Python 套件結構（Builder 可調整命名，但必須以 ADR 記錄並維持依賴方向）：

```text
megis/
├─ core/          quantity、tolerance、ID、provenance、errors（無外部依賴）
├─ schema/        pydantic models、JSON Schema 匯出、migrations
├─ envelope/      supported envelope 載入與檢查
├─ dna/           Product DNA、Module 定義
├─ graph/         Constraint Graph
├─ rules/         rule engine、rule packs、waivers
├─ geometry/      capability contract、CadQuery adapter
├─ validation/    geometry/collision/clearance validators
├─ maturity/      maturity evaluator
├─ package/       manifest、fingerprint、BOM、drawing、package builder
├─ jobs/          job state、local worker
├─ ai/            provider adapter、intent extractor、eval harness
└─ api/           本機 HTTP API（127.0.0.1）
apps/web/          React UI（只透過 api 或 adapter 取得資料）
```

依賴方向（必須以 import-linter 或等效工具在 CI 強制）：

```text
core ← schema ← envelope/dna/graph ← rules/geometry ← validation ← maturity ← package ← jobs ← api
ai → 只能依賴 core、schema、envelope；不得 import geometry、rules、validation、maturity、package
apps/web → 只能經由 api（或 UX-0 adapter）
```

## 4.3 工程中介表示（Engineering IR）必備欄位

Engineering IR 最少包含：

```yaml
schema_version: 0.1.0          # 【v3】與藍圖版本無關；G1 exit 時凍結為 1.0.0
design_id: PROJECT-0001
revision: A
units:                         # 【v3】由單一字串改為分量明確
  length: mm
  angle: deg
  mass: g
  force: N
  time: s
  temperature: degC
coordinate_system:
  handedness: right
  x: width
  y: depth
  z: height
  origin: base_bottom_center   # 【v3】明定原點
  up: +z

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

【v3】Entity 最小欄位：

| 實體（Entity） | 必填欄位 |
|---|---|
| Requirement | `id`、`statement`、`kind`（functional/geometric/manufacturing/regulatory）、`priority`、`provenance`、`verification_method` |
| Component | `id`、`module_ref`、`module_version`、`quantity`、`placement`、`provenance` |
| Interface | `id`、`component_ref`、`type`（mechanical/electrical/acoustic）、`geometry_ref`、`clearance_envelope` |
| Relationship | `id`、`type`（§4.16 vocabulary）、`source`、`target`、`parameters`、`provenance` |
| Material | `id`、`designation`、`temper`、`property_source`、`provenance` |
| Manufacturing | `id`、`process`、`setups`、`tooling_assumptions`、`provenance` |
| Constraint | `id`、`expression`、`applies_to`、`origin`（rule/user/module）、`severity` |
| Assumption | `id`、`statement`、`knowledge_state`、`impact`、`owner`、`review_required` |
| Unknown | `id`、`field_path`、`criticality`（critical/major/minor）、`unsafe_to_default`、`question_ref` |
| Provenance | `id`、`source`、`actor`、`timestamp`、`evidence_ref`、`approved_by` |

## 4.4 【v3】ID 規則

- 格式：`<TYPE>-<NNNN>` 或語意 slug（`cmp.pcb_a`），全檔唯一，大小寫敏感禁止僅大小寫不同的 ID。
- ID 一經發布不得重用於不同語意；刪除的 entity 其 ID 永久保留為 tombstone（migration 中記錄）。
- 引用必須指向存在的 entity；循環引用只允許在 relationship 類型明確允許時存在。
- 幾何 feature 的 semantic ID 格式：`<component>.<feature_type>.<name>[<index>]`，例如 `base.hole.m3_cover[2]`。

## 4.5 【v3】數量、公差與範圍模型

```yaml
wall_thickness:
  nominal: 2.0
  unit: mm
  tolerance:
    class: ISO2768-m          # 或 plus/minus 明確值
  range: { min: 1.5, max: 5.0 }   # 可選：允許的設計範圍
  provenance: { source: defaulted, ref: G1-REQ-001, approved_by: null }
```

規則：

- `nominal` 必須落在 `range` 內；`min ≤ max`；公差不可為負。
- 明確 `plus/minus` 優先於 `class`；兩者同時存在時必須一致，否則 schema 錯誤。
- 角度、長度、質量不得互相比較；型別系統必須拒絕。
- 百分比與比例以無因次量 `unit: "1"` 表示，不得省略 unit。

## 4.6 【v3】座標系與框架

- 全域框架：右手系，+Z 向上，原點為 base 底面中心。
- 每個 component 有 local frame，以 `placement`（translation mm + rotation 以四元數或 XYZ intrinsic deg 表示，ADR 擇一）轉換至全域。
- STEP 匯出使用全域框架；DXF section 必須在 metadata 記錄截面平面方程式。
- 視覺預覽（glTF 為 +Y up）必須在匯出邊界轉換，並有測試確認轉換後 bounding box 一致。

## 4.7 【v3】知識狀態與來源（Knowledge state／Provenance）

| 知識狀態 | 定義 | 可否進入幾何 | UI 顯示 |
|---|---|---|---|
| `known` | 使用者或工程師明確提供 | 可 | Verified／Supported |
| `derived` | 由 known 值經已測試規則推導 | 可 | Supported，顯示推導鏈 |
| `defaulted` | 採用已核准預設值 | 可 | 顯示為「系統預設」並可修改 |
| `researched` | 施工者依公開來源研究決定（附 URL、取用日期、料號／版次） | 可 | 顯示為「依公開資料建議」並列出來源 |
| `llm_proposed` | AI 提議、尚未經使用者確認 | **不可** | 顯示為「待確認建議」 |
| `unknown` | 未知且可暫緩 | 視 criticality | Unknown |
| `unsafe_to_default` | 未知且不得預設 | **不可**，阻擋生成 | 必答問題 |

## 4.8 【v3】Schema 版本與 migration 政策

- 所有 schema（Requirement、IR、Rule、Module、Manifest、Work Queue）各自 SemVer，與藍圖版本、軟體版本獨立。
- MAJOR：刪除欄位、改變語意、收緊驗證；必須提供 migration 與 rollback。
- MINOR：新增選填欄位或新列舉值；舊資料必須不需 migration 即可驗證。
- PATCH：文件、描述、範例修正。
- `0.x` 期間允許破壞性變更，但每次仍須更新 golden 與 migration 測試；Gate G1 exit 時 IR 凍結為 `1.0.0`。
- Migration 必須是純函數、可單向重跑、有 round-trip 測試（`migrate → rollback → migrate` 結果一致）。

## 4.9 能力契約（Capability contract）

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
- 【v3】`fingerprint_policy`：可指紋化的輸出、欄位、捨入精度、informational 欄位
- 【v3】`resource_limits`：記憶體、CPU 時間、輸出大小上限
- 【v3】`envelope_ref`：該 adapter 宣稱支援的 envelope 版本

第一版固定單一 CadQuery／OpenCascade backend。build123d 與 commercial CAD adapter 只保留介面，不在沒有實際遷移需求時同步實作。

## 4.10 【v3】錯誤分類與錯誤碼（Error taxonomy）

錯誤碼格式：`MEGIS-<DOMAIN>-<NNN>`。

| 領域 | 範圍 | 範例 |
|---|---|---|
| `SCH` | schema／型別 | `MEGIS-SCH-001` unit mismatch |
| `REF` | referential integrity | `MEGIS-REF-001` dangling reference |
| `ENV` | envelope | `MEGIS-ENV-001` dimension out of supported range |
| `GEO` | geometry kernel | `MEGIS-GEO-010` boolean failed |
| `VAL` | validation | `MEGIS-VAL-001` collision detected |
| `RUL` | rule engine | `MEGIS-RUL-003` rule source not approved |
| `PKG` | package／manifest | `MEGIS-PKG-002` fingerprint mismatch |
| `JOB` | job lifecycle | `MEGIS-JOB-004` timeout |
| `AI` | AI provider／extraction | `MEGIS-AI-002` schema-invalid model output |
| `IMP` | import／parser | `MEGIS-IMP-005` file exceeds limit |
| `SYS` | 環境／依賴 | `MEGIS-SYS-001` toolchain version mismatch |

每個錯誤物件必須包含：`code`、`severity`（fatal/error/warning/info）、`retryable`（bool）、`user_message_zh_tw`（非專業語言）、`engineer_detail`、`entity_refs`、`correlation_id`。錯誤碼一經發布不得改變語意；新增錯誤碼需更新錯誤碼登錄表與測試。

## 4.11 工作狀態契約（Job state contract）

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

【v3】合法轉移表（其他轉移一律拒絕並記錄）：

| 從 | 到 | 條件 |
|---|---|---|
| QUEUED | RUNNING | worker 取得 |
| QUEUED | CANCELLED | 使用者取消 |
| RUNNING | SUCCEEDED | 所有步驟成功且 manifest 寫入完成 |
| RUNNING | FAILED | 任一步驟 fatal/error 或 timeout |
| RUNNING | CANCELLED | 使用者取消且已清理暫存 artifact |
| RUNNING | NEEDS_REVIEW | 生成成功但存在需人工處置項（未處置 warning、drawing QA 待辦） |
| NEEDS_REVIEW | SUCCEEDED | 所有待辦已處置 |

- Idempotency key = `sha256(canonical requirement + versions)`；相同 key 的 SUCCEEDED job 直接回傳既有結果。
- MVP 採本機單一 worker process 與 SQLite 或檔案佇列；G6 前不得引入外部 message broker。

## 4.12 【v3】確定性（Determinism）與雙層指紋

| 層 | 名稱 | 計算對象 | 用途 |
|---|---|---|---|
| L1 | `byte_sha256` | 檔案原始 bytes | 傳輸／儲存完整性、竄改偵測 |
| L2 | `semantic_fingerprint` | canonical JSON 的 SHA-256 | 可重現性、golden regression、跨平台比較 |

幾何 semantic fingerprint canonical 內容：

```json
{
  "fingerprint_policy_version": "1.0.0",
  "solids": 1,
  "shells": 1,
  "faces": 38,
  "edges": 96,
  "vertices": 60,
  "volume_mm3": "44999.37",
  "area_mm2": "25873.12",
  "bbox_mm": ["120.000", "80.000", "35.000"],
  "center_of_mass_mm": ["0.000", "0.000", "14.212"],
  "semantic_features": ["base.shell.main", "base.hole.m3_cover[0]"]
}
```

規則：

- Canonical JSON：key 排序、UTF-8、無多餘空白、浮點依 policy 捨入後以字串表示。
- 捨入精度：長度 1e-3 mm、面積 1e-2 mm²、體積 1e-2 mm³。
- 若某拓樸計數在跨平台（ARM64 emulation vs x64）不穩定，policy 可將其宣告為 `informational`（記錄但不納入 hash），必須有 ADR。
- 非幾何製品：BOM 以排序後 CSV 正規化；報告以 Markdown 去除時間戳行；drawing 以向量元素集合（排序後）正規化。
- STEP 匯出後處理：`FILE_NAME` 時間戳固定為 `1970-01-01T00:00:00`、author／organization 固定；DXF 固定 `$TDCREATE`／`$TDUPDATE` 與 handle seed；STL 使用 binary 格式並固定 80-byte header。正規化後同平台 byte hash 應一致，作為附加證據。
- Manifest 自身的 fingerprint 必須排除 `generated_at` 等執行期欄位。

## 4.13 【v3】數值容差政策

| 容差名稱 | 預設值 | 用途 |
|---|---|---|
| `kernel_tol` | 1e-6 mm | OCC 幾何運算 |
| `export_reload_tol` | 1e-4 mm | STEP 重載比較 |
| `mesh_tol` | 0.05 mm | STL 比較 |
| `mesh_linear_deflection` | 0.01 mm | STL 生成 |
| `mesh_angular_deflection` | 0.1 rad | STL 生成 |
| `fingerprint_round_length` | 1e-3 mm | semantic fingerprint |
| `fingerprint_round_volume` | 1e-2 mm³ | semantic fingerprint |
| `engineering_tol` | 由 IR tolerance 決定 | 尺寸驗收 |

所有容差集中定義於單一模組（例如 `megis/core/tolerances.py`）並版本化；測試不得使用散落的魔術常數。

## 4.14 【v3】拓樸命名（Topological naming）政策

- 內部永不保存 transient face／edge index 作為識別。
- Feature 建構時以 CadQuery `tag()` 或等效機制記錄 semantic feature ID。
- 建構完成後以幾何謂詞（面法向、面中心座標、面積、所屬 feature 的 bounding box）重新定位並驗證對應關係；對應失敗回傳 `MEGIS-GEO-020`。
- Drawing 尺寸、規則檢查與 UI 高亮只能引用 semantic feature ID。

## 4.15 【v3】技術基線（可經 ADR 變更）

| 領域 | 基線選擇 | 理由 |
|---|---|---|
| Python | CPython 3.11 x64 | CadQuery／OCP wheel 可用性 |
| CAD kernel | CadQuery + OCP（OpenCascade） | 開源、可 headless、STEP 支援 |
| Schema | pydantic v2 → JSON Schema 2020-12 | 跨語言契約單一來源 |
| TS 型別 | 由 JSON Schema 產生 | 禁止手寫重複型別 |
| DXF | ezdxf | 成熟、可控 header |
| Property testing | Hypothesis | range、tolerance、ID 邊界 |
| Lint／type | ruff、mypy 或 pyright（strict 於 core/schema） | 靜態保證 |
| 前端 | React + TypeScript + Vite | 沿用 UX-0 |
| Drawing | FreeCAD headless projection ＋ 固定 SVG template；PDF 轉換於 G5 決策 | TechDraw 原生匯出依賴 GUI 時採 fallback |
| API | 本機 HTTP（例如 FastAPI）綁 `127.0.0.1` | G6 才需要 |
| 佇列 | SQLite 或檔案佇列 | 單機足夠 |
| 依賴鎖定 | pip hash-pinned lockfile；npm lockfile + `npm ci` | 可重現與供應鏈安全 |

## 4.16 【v3】產品 DNA、模組與限制關係詞彙

Product DNA 最小欄位：

```yaml
dna_id: dna.cnc_enclosure
version: 1.0.0
envelope_ref: envelope.cnc_enclosure@1.0.0
required_modules: [mod.base, mod.cover]
optional_modules: [mod.pcb, mod.usbc, mod.m3_fastener]
parameters: []          # 帶 range、default、provenance、question_ref
question_set_ref: qs.cnc_enclosure@1.0.0
rule_packs: [rp.cnc_dfm@1.0.0, rp.enclosure_clearance@1.0.0]
maturity_cap: PROTOTYPE
```

Module 最小欄位：`module_id`、`version`、`capability_level`（`metadata_only`／`layout_capable`／`geometry_capable`／`validated`）、`interfaces`、`clearance_envelopes`、`geometry_generator_ref`（capability ≥ geometry_capable 時必填）、`metadata`（每欄 provenance）、`rule_refs`、`datasheet_refs`。

Relationship vocabulary（第一版封閉集合，新增需 MINOR schema 版本與語意測試）：

| 類型 | 語意 | 必要驗證 |
|---|---|---|
| `contains` | A 的內腔容納 B | B 的 clearance envelope 完全在 A 內腔內 |
| `mounts_to` | B 以 fastener 固定於 A | 孔位對齊、boss 存在、嚙合長度 |
| `fastens` | fastener 連接 A 與 B | 螺絲長度、通孔、內螺紋 |
| `opens_through` | 介面 B 穿過 A 的壁面 | 開口存在、開口 ≥ 介面 envelope + 間隙 |
| `clears` | A 與 B 最小距離 ≥ d | 距離計算 |
| `aligns` | A 與 B 在指定軸對齊 | 軸向偏差 ≤ 容差 |
| `covers` | A 覆蓋 B 的開口 | 配合面與干涉檢查 |
| `removable_along` | A 可沿方向移除 | 掃掠干涉檢查 |

---

# 5. Agent 連續施工控制面

## 5.1 Repository 必備狀態檔

G0 建立下列單一真相來源：

```text
AGENTS.md                      repository 邊界與所有 Agent 共通規則
CLAUDE.md                      【v3】Claude Code 補充指示（引用 AGENTS.md，不重複、不衝突）
docs/
├─ PRODUCT.md                  產品定位、使用者、anti-goals
├─ ARCHITECTURE.md             分層、依賴方向、資料流、adapter 清單
├─ DECISIONS.md                ADR 索引（ADR-0001…）
├─ decisions/                  【v3】個別 ADR 詳文
├─ SUPPORTED_ENVELOPE.md       人讀 envelope（與 config/envelope 一致）
├─ ACCEPTANCE.md               各 Gate 驗收紀錄索引
├─ RISKS.md                    風險登錄表（第 28 章欄位）
├─ OPERATIONS.md               環境重建、備份、還原、故障處理
├─ ERROR_CODES.md              【v3】錯誤碼登錄表
├─ RULE_SOURCES.md             【v3】規則來源登錄表（第 19 章）
└─ research/                   【v3／D8】網路研究紀錄（每份附來源 URL 與取用日期）

execution/
├─ PROJECT_STATE.md
├─ WORK_QUEUE.yaml             【v3】內容格式為 JSON（YAML 1.2 子集），以 JSON parser 驗證
├─ BLOCKERS.yaml
├─ LAST_VERIFICATION.json
├─ AGENT_CLAIM.json            【v3】目前持有寫入權的 Builder
├─ schemas/                    control-plane JSON Schemas
├─ handoffs/
├─ reviews/                    【v3】自我審查報告（全新 session）
└─ signoffs/                   【v3】人類簽核與 waiver

config/
└─ envelope/                   【v3】機器可讀 envelope

tests/
└─ golden/                     【v3】版本化 golden fixtures
```

用途：

- `PROJECT_STATE.md`：目前 Gate、已完成能力、下一工作單元、最後綠色 commit。
- `WORK_QUEUE.yaml`：有依賴邊的工作單元，不使用日曆日期排序。
- `BLOCKERS.yaml`：只記真正阻塞條件、owner、解除方法與 fallback。
- `LAST_VERIFICATION.json`：最後一次測試命令、版本、結果及 artifact hash／fingerprint。
- `handoffs/`：跨上下文的短期施工摘要；完成後可歸檔。
- 【v3】`AGENT_CLAIM.json`：防止多 Agent 同時寫入。
- 【v3】`reviews/`：自我審查結果（全新 session），是 Gate acceptance 的必要證據。
- 【v3】`signoffs/`：決策紀錄；依 D6 可由施工 Agent 記錄，使用者可否決；`engineering_review` 類型限具名工程師。

【v3】每份 `docs/*.md` 至少包含：目的、目前內容、owner、最後審查 commit。只有標題的空殼文件視為不存在。

## 5.2 每次施工循環

```text
1. Resume     讀 AGENTS.md、PROJECT_STATE、WORK_QUEUE、BLOCKERS、AGENT_CLAIM、
              最近 handoff、最近 reviews。
2. Claim      【v3】AGENT_CLAIM 為空或已過期（過期需在 handoff 說明）時寫入 claim。
3. Inspect    檢查 repository、未提交變更、相關程式、測試與決策紀錄。
4. Select     依 §5.4 選擇一個依賴已滿足、可在本回合形成驗收證據的工作單元。
5. Baseline   修改前先跑該範圍現有測試，保存結果；baseline 紅燈時先登記 blocker，
              不得在紅燈基線上施工新功能。
6. Implement  以最小 vertical increment 完成程式、schema、tests、docs。
7. Verify     單元測試、契約測試、golden regression（semantic）、artifact 檢查、
              control-plane verifier。
8. Record     更新 PROJECT_STATE、WORK_QUEUE、DECISIONS、RISKS、ERROR_CODES 與驗收證據。
9. Commit     只提交已通過驗收的一致變更，使用簡潔英文 `type: summary`。
10. Request   【v3】需要審查的項目標記 review.status = pending。
11. Release   【v3】釋放 claim，寫 handoff。
12. Continue  尚有可安全執行的 ready work item 時，進入下一循環。
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

【v3】Control-plane schema `1.1.0` 以**選填**方式擴充（`1.0.0` 資料不需 migration 即通過）：

```json
{
  "owner_role": "builder | reviewer | human",
  "requires_user_decision": false,
  "evidence_level_required": "E2",
  "review": {
    "required": true,
    "status": "not_required | pending | passed | changes_requested",
    "report": "execution/reviews/G2-CAD-001-abc1234.md"
  },
  "risk_refs": ["R-CAD-001"],
  "blueprint_ref": "v3.0 §10"
}
```

【v3】Work item 狀態轉移：

| 從 | 到 | 條件 |
|---|---|---|
| planned | ready | 所有 `depends_on` 為 done，且 Definition of Ready 成立（§25.1） |
| ready | in_progress | Builder 持有 claim；全 repository 只能有 1 個 in_progress |
| in_progress | done | 全部 acceptance 有 ≥ `evidence_level_required` 的證據；需要審查者 review.status = passed |
| in_progress | blocked | 登記 BLOCKERS 條目 |
| blocked | ready | blocker 解除或 fallback 決策 |
| done | — | 不得回退；發現缺陷時新增修補 work item |

## 5.4 【v3】在製上限（WIP）與選擇順序

- WIP limit = 1 個 `in_progress` work item（全 repository）。
- 選擇順序：
  1. 解除現有 blocker 的項目。
  2. 最低編號的 active Gate 內，拓撲排序最前的 ready 項目。
  3. 同層時，優先解鎖最多下游項目者。
  4. 再同層時，優先降低 high impact 風險者。
- `requires_user_decision: true` 的項目不得自動開始；Builder 應先彙整問題交給使用者，然後選下一個可執行項目。

## 5.5 中斷與恢復

Agent 在必須停止前：

1. 保持 repository 在可理解狀態。
2. 將未完成變更、測試結果與下一步寫入 handoff。
3. 在 `PROJECT_STATE.md` 標示最後綠色 fixed point。
4. 不為了「看起來完成」降低 Gate。
5. 【v3】釋放 claim；若無法釋放，在 handoff 標示 claim 狀態與原因。
6. 【v3】未提交變更若無法形成一致 commit，應保存為 patch 檔於 `.temp/`（不入 Git）並在 handoff 註明路徑，不得以半成品 commit 汙染 fixed point。

下次執行先驗證 fixed point；若狀態檔與實際 repository 不一致，以程式碼、測試及 Git history 為準並修正狀態檔。

## 5.6 自動前進與停止條件

Agent 可以自動前進的條件：

- 工作單元已在核准範圍內。
- 依賴已滿足。
- 不需要新產品決策、付費採購、憑證或外部人工簽核。
- 修改可由既定測試驗證並能安全回滾。

Agent 必須停止並請求決策的條件：

- supported envelope 需要擴張。
- 需要購買 COMSOL／商業 CAD／雲端服務授權。
- 工程安全假設缺失且無安全 default。
- 需求衝突會改變產品方向。
- 需要具名工程師或法規簽核。
- 同一阻塞在 fallback 後仍無法形成可信結果。
- 【v3】需要 `git push`、啟用或修改 CI 權限、發布任何內容。
- 【v3】需要把使用者資料、CAD、datasheet 傳給外部服務（含 LLM）。
- 【v3】需要修改 golden 預期值、不變量、envelope 或 maturity 規則。
- 【v3】使用者否決 Gate 或決策紀錄，或另一 Agent 的抽查結果與自我審查衝突。
- 【v3】需要刪除資料、改寫 Git history 或變更 repository 權限。

## 5.7 【v3／D6】Agent 協作協定：誰施工，誰審查

使用者決策 D6：**不設具名工程審查人；哪個 Agent 施工，就由該 Agent 審查自己的工作。** 為降低自我審查偏誤，審查必須與施工隔離。

| 角色 | 執行者 | 允許 | 不得 |
|---|---|---|---|
| 施工者 | 接手該工作項目的 Agent（ChatGPT Codex 或 Claude Code） | 修改程式、schema、文件、狀態檔；commit | 在他人持有有效寫入鎖時寫入 |
| 審查者 | 同一個 Agent，但必須開啟**全新 session** | 讀取全部、在乾淨 checkout 與隔離暫存目錄重跑、撰寫 `execution/reviews/*`、記錄決策 | 在審查 session 中修改程式、schema、golden 或狀態檔；引用施工 session 的輸出作為證據 |
| 使用者 | 使用者本人 | 產品決策、否決任何 Gate 或決策紀錄、要求另一 Agent 抽查 | — |
| 具名工程師 | 目前不設置 | — | — |

規則：

1. 同一時間只允許一個施工寫入鎖（claim，格式見附錄 A.9）；預設有效 4 小時，可續期。兩個 Agent 不得同時施工。
2. 自我審查必須：(a) 開啟全新 session，不讀取施工 session 的對話或暫存；(b) 以 `git worktree` 或 `git clone` 取得指定 commit 的乾淨副本；(c) 重跑全部驗證命令；(d) 至少嘗試一個施工時未使用的 negative 或 boundary 輸入；(e) 報告記錄審查 session ID 與施工 session ID（必須不同）。
3. CI 是外部證據；Gate accepted 前，CI 必須對同一 commit 全綠。
4. Gate acceptance 需要：施工者自評 ＋ 自我審查報告 `passed` ＋ CI 全綠 ＋ `gate_acceptance` 決策紀錄（由施工 Agent 記錄並通知使用者，使用者可否決）。
5. 審查發現缺陷時，先寫入審查報告，再以新 commit 修正；修正後必須重新自我審查。
6. 審查報告以獨立 commit（`docs: review <id>`）提交，該 commit 不得包含其他檔案。
7. 衝突時以 Git history 中較早的綠色 commit 為準，後者 rebase；**禁止 force push 與改寫 history**。
8. 使用者可隨時要求另一個 Agent 抽查；抽查結果與自我審查衝突時，以重跑證據為準並登記 blocker。
9. D6 的限制：自我審查不能取代具名工程師；指定具名工程師前，`ENGINEERING_REVIEWED` 與 `RELEASED` 不可達（§1.4）。

## 5.8 【v3】Git 政策

- 預設分支 `main` 必須永遠是綠色 fixed point 或可明確辨識的 in-progress commit。
- Commit message：`type: summary`（英文，type ∈ feat/fix/docs/test/refactor/build/ci/chore/golden），單一目的。
- Golden 預期值變更使用 `golden:` type，且該 commit 只含 golden 與差異報告。
- 禁止 `git push --force`、`git reset --hard` 已推送歷史、刪除遠端分支，除非使用者明確授權該次操作。
- Push 前必須 `git fetch` 並確認無分歧；push 後核對 `HEAD` 與 `origin/main` SHA。
- 設定 `.gitattributes`：二進位製品（`*.step *.stl *.fcstd *.glb *.pdf`）標記 `binary`，文字檔固定換行規則，避免跨平台 checkout 改變 byte hash。
- 軟體版本 tag：`megis-vX.Y.Z`；Gate acceptance tag（可選）：`gate-G2-accepted`。設計 Package 不使用 Git tag。

## 5.9 【v3】製品儲存政策

| 類型 | 位置 | 進 Git | 預算 |
|---|---|---|---|
| Golden fixture（輸入、expected fingerprint、小型 reference STEP） | `tests/golden/` | 是 | 單檔 ≤ 200 KB；總量 ≤ 5 MB |
| Spike／Gate evidence（manifest、verification JSON、fingerprint） | `artifacts/<item>/*.json` | 是 | 單檔 ≤ 50 KB |
| Spike 重型製品（STEP/STL/DXF/FCStd/SVG） | `artifacts/<item>/` | 否（gitignore），由命令重生；如需保存，改放 `tests/golden/` 並受預算限制 | — |
| Design Run 產物 | `.runs/` | 否 | 本機保留政策見 §24.3 |
| CI 產物 | CI artifact storage | 否 | 保留 30 天 |

Control-plane verifier 必須檢查：Git 追蹤的單一檔案 > 1 MB 時失敗（白名單需 ADR）。既有已提交的大型製品不改寫 history，但後續不得再新增。

## 5.10 【v3】藍圖變更流程（BCR）

藍圖本身的變更也需要流程：

1. 新版藍圖另存新檔，舊版不覆寫。
2. 新版必須包含變更處置表（第 29 章格式）。
3. 使用者核准（`blueprint_change` sign-off）。
4. Builder 執行 BCR work item：更新 README 主要藍圖指向、`DECISIONS.md` 新增 ADR、`WORK_QUEUE.yaml` 增加新項目、更新 verifier 的必要 ID 清單、測試通過後 commit。
5. 已 `done` 的項目不重開；範圍差異以新 work item 補足。
6. 施工者以全新 session 自我審查 BCR commit，確認沒有遺漏或越權修改。

## 5.11 【v3】決策紀錄（ADR）規則

- 每個 ADR：ID、標題、狀態（proposed/accepted/superseded）、背景、決策、替代方案、後果、證據、決策者、日期。
- 被取代的 ADR 保留並指向新 ADR。
- 必須有 ADR 的情境：技術基線變更、容差或 fingerprint policy 變更、envelope 變更、角色互換、驗收範圍縮窄、大型檔案白名單、偏離「應」條款。

## 5.12 【v3】證據等級

| 等級 | 定義 | 例 |
|---|---|---|
| E0 | 只有敘述 | 「已測試」 |
| E1 | 產物存在 | 檔案路徑存在 |
| E2 | 自動化檢查在本機通過且記錄命令與結果 | pytest 輸出、verification JSON |
| E3 | 獨立環境重跑通過（CI，或施工者以全新 session 於乾淨 checkout 重跑） | CI run ID、自我審查報告 |
| E4 | 決策紀錄（D6：施工者自我審查後記錄，使用者可否決；`engineering_review` 限具名工程師） | `SO-xxxx` |

- Work item `done`：預設 ≥ E2；涉及 golden、envelope、rules、maturity、package 者 ≥ E3。
- Gate accepted：所有 exit criteria ≥ E3，且 Gate acceptance 本身為 E4。
- E0 與 E1 不得單獨作為任何 acceptance 的證據。

## 5.13 【v3】控制面驗證腳本必須檢查的項目

1. 必備檔案存在且非空殼（§5.1）。
2. `WORK_QUEUE.yaml` 通過 schema；ID 唯一；依賴存在且無循環。
3. 藍圖要求的 work item ID 全部存在（含 V3C 與 v3 新增項）。
4. 恰好 1 個 active Gate；accepted Gate 的依賴皆 accepted；accepted Gate 內無未完成項目。
5. 至多 1 個 `in_progress`；其 ID 與 `PROJECT_STATE.md`、`AGENT_CLAIM.json` 一致。
6. `done` 項目：commitSha 存在於 Git history；evidence 路徑存在；verification = passed；review 需要時為 passed。
7. Manifest maturity 掃描（§1.5）。
8. Git 追蹤檔案大小預算（§5.9）。
9. Accepted Gate 具備 review 報告與 sign-off 檔案。
10. `docs/SUPPORTED_ENVELOPE.md` 與 `config/envelope` 一致（G1 起）。

---

# 6. Gate 依賴圖與通用規則

## 6.1 Gate 依賴

```text
UX-0 誠實的使用者體驗原型（前置軌道）
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
G6 引導式介面與 AI 輔助
├───────────────┐
↓               ↓
G7 聲學         G8 機器人
薄切片          薄切片
└───────┬───────┘
        ↓
G9 強化與擴充
```

Gate 只表示依賴順序，不表示時間。G7 與 G8 可在 G6 後平行，但各自仍需獨立 acceptance；WIP limit 仍為 1 個 work item。

## 6.2 【v3】每個 Gate 的通用結構

每個 Gate 章節必須包含：目標、Entry criteria、工作、Work items、Exit criteria、必要證據、回滾邊界、非目標、主要風險。每個 Gate 以 `Gx-REV-001`（全新 session 自我審查）與 `Gx-ACC-001`（Gate 決策紀錄）收尾。

## 6.3 【v3】Gate 審查程序

1. 施工者完成所有工作項目，撰寫 Gate 自評（每條完成條件 → 證據路徑 → 證據等級）。
2. 施工者開啟全新 session，在乾淨 checkout 與隔離暫存目錄重跑所有驗證命令。
3. 抽查：至少 1 個 negative case、1 個 boundary case、所有 golden 的 fingerprint、已封存的 holdout corpus（若該 Gate 有）。
4. 檢查狀態檔與 Git 一致、不變量強制機制仍有效、無未登記風險。
5. 報告結論 `passed` 或 `changes_requested`；後者列出每個缺陷的檔案、重現步驟、影響的完成條件。
6. 確認 CI 對同一 commit 全綠後，記錄 `gate_acceptance` 決策紀錄並通知使用者；使用者可否決。
7. 更新 Gate 狀態為 accepted，並啟動下一 Gate。

## 6.4 【v3】Gate 失敗與範圍縮窄

- Exit criterion 無法達成時，只有兩種合法處置：(a) 登記 blocker 並停留；(b) 以 ADR ＋ 使用者 sign-off 將該項目移出 Gate，並在後續 Gate 建立承接 work item。
- 不得以修改驗收文字、降低容差或刪除測試的方式讓 Gate 通過；此類變更必須經全新 session 自我審查、有 ADR，並通知使用者。

---

# 7. 【v3】UX-0 — 誠實的使用者體驗原型

## 目標

在工程能力建設前，先讓使用者確認施工進度中心與 Fixture／Enclosure 引導流程的資訊架構，而**不冒充工程能力**。

## 邊界

- UX-0 使用有版本的 `PrototypeViewModel` 合成資料，經可替換 adapter 提供。
- 所有模擬結果必須永久顯示 `Synthetic demo data` 與 `No engineering artifact generated`。
- UX-0 不得產生 STEP、工程圖、BOM、Prototype Package 或任何可能被誤認為工程輸出的製品。
- 真實 CAD、IR、validation、上傳解析、多使用者、雲端與放行行為均不在 UX-0 範圍。
- UX-0 accepted 的意義是 `UX PROTOTYPE ACCEPTED`，不代表任何 Gate 的工程能力。

## 完成條件（Exit criteria）

- 所有規劃路由可渲染，Fixture flow 可走完到合成結果頁。
- Loading、empty、error、success 狀態具備。
- 鍵盤可完成主要流程；自動化無障礙檢查通過。
- 桌面與行動版視覺證據；無非預期水平捲動。
- 正常使用無外部網路請求；服務只綁 `127.0.0.1`。
- Progress schema、非法轉移、斷裂證據測試通過。
- 非 CAD 使用者可用性回饋已記錄。

## 與 G6 的關係

G6-UI-001 必須以 adapter 替換方式把 `PrototypeViewModel` 換成真實 API，並以 UX-0 可用性結果作為對照基線。UX-0 accepted 不得作為跳過任何 G6 exit criterion 的理由。

---

# 8. G0 — 基礎建設與可行性

## 目標

建立可持續施工的 repository、固定技術決策，並在大量開發前證明關鍵外部工具可用；【v3】並證明產物可以被可重現地比較、成熟度不會被誤標。

## 進入條件（Entry criteria）

- 使用者核准本藍圖。
- Repository 可建立於核准工作區。

## 工作

1. 建立 repository、開發環境與鎖定依賴版本。
2. 建立第 5 章的施工控制面文件（【v3】包含 `CLAUDE.md`、`reviews/`、`signoffs/`、`AGENT_CLAIM.json`、`ERROR_CODES.md`、`RULE_SOURCES.md`）。
3. 決定並記錄（【v3】以 `G0-DEC-001` 執行，決策清單見 §8.1）：
   - local/internal prototype 或 cloud。
   - single-user 或 multi-tenant。
   - 支援 OS、Python、Node、CadQuery、OpenCascade、FreeCAD 版本。
   - LLM provider 與離線 deterministic fallback。
   - artifact retention、IP、上傳資料政策。
   - 【v3】Agent 角色分工與 push 授權範圍。
4. 完成 feasibility spikes：
   - CadQuery：Reference Case 可輸出合法 STEP、STL、2D DXF section。
   - FreeCAD TechDraw：headless 產生固定模板圖面；若失敗，採人工 QA 或 SVG/PDF fallback。
   - COMSOL：只驗證授權、headless、API、queue 與範例模型，不納入核心 Gate。
   - 【v3】Determinism：semantic fingerprint 原型、STEP/DXF header 正規化、兩次重跑一致性。
5. 建立 CI、lint、type check、unit test、schema test 與 artifact smoke test；【v3】加上 fingerprint replay、manifest maturity 掃描、檔案大小預算、secret scan。

## 8.1 【v3】G0 使用者決策清單

| # | 決策 | 建議選項 | 若不決定的預設 |
|---|---|---|---|
| D1 | 部署範圍 | local single-user（建議） | local single-user |
| D2 | 是否擁有 COMSOL 授權與 API | 無授權 → `out_of_scope` | `out_of_scope` |
| D3 | LLM provider | 以 adapter 抽象；G6 前不呼叫真實 LLM | 無 provider，僅表單流程 |
| D4 | CI 平台與 push 授權範圍 | GitHub Actions Windows x64；Builder 可在驗證後推送 `main`，禁止 force | 不 push，只本機 |
| D5 | 客戶／公司 CAD、datasheet 可否入 repo 或送外部服務 | 不可；golden 只用自建或公開資料 | 不可 |
| D6 | 工程審查人 | ✅ 使用者已決定：誰施工誰自我審查（全新 session 隔離）；不設具名工程師 | — |
| D7 | Agent 角色 | ✅ 依 D6：Codex 或 Claude Code 誰接手施工，誰負責該項審查；同時只能一個 Agent 持有寫入鎖 | — |
| D8 | 參考案例未知值（PCB 尺寸、擺放、USB-C 位置） | ✅ 使用者已決定：由施工者上網研究最適合的方案並附來源（§9.1） | — |
| D9 | Artifact 保留期間 | Design Run 本機保留 90 天；golden 永久 | 同建議 |

## 完成條件（Exit criteria）

- 新環境依 README 可重建。
- 所有 dependency 都有 pinned version 或可重現 lockfile（【v3】Python lockfile 應含 hash）。
- CadQuery spike 有 STEP artifact 與 automated validity check。
- FreeCAD／COMSOL 各有 `pass`、`fallback` 或 `out_of_scope` 決策，沒有 undecided dependency。
- `PROJECT_STATE.md` 與 `WORK_QUEUE.yaml` 可驅動下一 Gate。
- baseline CI 全綠。
- 【v3】同一平台連續兩次重跑 spike，semantic fingerprint 一致（自動化測試）。
- 【v3】所有 spike manifest `maturity == null`，且 verifier 掃描生效。
- 【v3】§5.1 所有文件存在且非空殼。
- 【v3】§8.1 所有決策已寫入 ADR（D6、D7、D8 依使用者決定記錄）。
- 【v3】`.gitattributes` 與檔案大小預算檢查生效。
- 【v3】G0-REV-001 報告 passed；G0-ACC-001 sign-off 完成。

## 必要證據

toolchain lock、環境重建紀錄、spike manifests、fingerprint replay 測試結果、FreeCAD／COMSOL 決策文件、CI run ID、ADR 清單、review 報告、sign-off。

## 回滾邊界

G0 只建立 scaffold 與 spike。若外部工具不可用，保留 spike evidence，切換 fallback，不把失敗 adapter 帶入核心架構。

## 非目標

正式 IR、正式 geometry backend、規則、UI 工程整合。

---

# 9. G1 — 工程契約與黃金案例

## 目標

以 schema、語意與 golden cases 固定跨模組契約。

## 進入條件（Entry criteria）

- G0 accepted。
- D6、D8 已決定（§8.1）。

## 工作

1. 定義 Requirement、Product DNA、Module、Engineering IR、Rule、Constraint、Validation Result schema。
2. 定義 unit system、coordinate system、tolerance、range、ID/reference、provenance、revision（依 §4.3–§4.8）。
3. 建立 schema migration 介面及 semantic version policy。
4. 建立 Reference Fixture golden input、expected IR、expected graph、expected artifact metadata。
5. 建立 Acoustic 與 Robot 的 schema-only golden input，用來證明 vocabulary 可擴充，不宣稱 CAD 完成。
6. 建立 assumption review：
   - known
   - derived
   - defaulted
   - unknown
   - unsafe_to_default
   - 【v3】llm_proposed
7. 【v3】`G1-REQ-001`：依附錄 B 與 §9.1 研究規範完成參考案例參數檔，以網路研究解決所有 unknown 並記錄來源。
8. 【v3】`G1-ENV-001`：機器可讀 envelope 與人讀文件一致性測試。
9. 【v3】`G1-ERR-001`：error taxonomy 與錯誤碼登錄表。

## 9.1 【v3／D8】參考案例未知值研究規範

使用者決策 D8：PCB 尺寸、擺放方式、USB-C 位置等未知值，**由負責 `G1-REQ-001` 的施工 Agent 上網研究，選擇最適合的建議方案**。研究必須符合：

1. **優先採用有公開機械圖面的真實產品**：市面常見、製造商公開外形尺寸、安裝孔座標與連接器位置的開發板或模組；不得自行虛構尺寸。
2. **來源要求**：每個研究值至少 1 份官方來源（製造商機械圖、datasheet、官方 CAD）；若無官方來源，至少 2 份互相獨立且一致的公開來源。記錄 URL、文件標題、版次或料號、取用日期。
3. **USB-C**：選定具體 receptacle 料號（主流連接器製造商），以其 datasheet 的外殼尺寸、安裝方式與板邊內縮距離推導面板開口；插頭外形間隙參考 USB Type-C 規格對插頭 overmold 的建議尺寸。
4. **適配性檢查**：方案必須放得進 §1.3 外形與壁厚；與 M3 安裝相容（板子原生孔徑不是 M3 時，記錄轉接方式或改選方案）；兩片 PCB 的零件高度加 standoff 高度在內腔高度內；USB-C 開口不與角落 boss 或分割面衝突。
5. **比較與理由**：至少比較 2 個候選方案，以表格列出尺寸、孔位、連接器、適配性、取得難易，寫成 ADR 說明選擇理由。
6. **紀錄方式**：值的來源設為 `researched`，填入 `sources` 與 `rationale`；研究全文存於 `docs/research/G1-REQ-001.md`。
7. **不得**：引用無法開啟的來源、以 LLM 記憶作為唯一依據、把研究值標為 `user`。
8. **重新研究**：來源失效、料號停產或規則檢查不通過時，重新研究並更新 ADR。


## 完成條件（Exit criteria）

- 三個 golden inputs 通過 schema validation。
- Reference Fixture 可完成 serialize／deserialize round trip。
- unit mismatch、dangling reference、duplicate ID、invalid range 都有失敗測試。
- schema migration 有至少一個前版 fixture 與 rollback test。
- downstream test consumer 能實際讀取 IR；不以「JSON 可產生」作為成功。
- 【v3】參考案例無未解決 unknown；所有 `defaulted`／`researched` 值有來源與決策紀錄（E4）。
- 【v3】`llm_proposed` 值無法進入 IR confirmed 區（負向測試）。
- 【v3】Property-based tests 覆蓋 Quantity、Range、Tolerance、ID reference。
- 【v3】JSON Schema 匯出結果與 pydantic 模型一致（契約測試），TS 型別由 schema 產生且編譯通過。
- 【v3】IR schema 凍結為 `1.0.0`。
- 【v3】G1-REV-001 passed；G1-ACC-001 sign-off。

## 必要證據

schemas、JSON Schema 匯出、golden files、round-trip 與 negative tests、migration tests、參數核准 sign-off、review 報告。

## 回滾邊界

每個 schema 變更為獨立 commit；golden 變更使用 `golden:` commit。

## 非目標

幾何生成、規則評估。

---

# 10. G2 — 治具幾何垂直切片

## 目標

從固定 Engineering IR 產生 Reference Fixture 的 base、cover 與 assembly artifacts。

## 進入條件（Entry criteria）

- G1 accepted；IR `1.0.0` 與 Reference Fixture golden case 可用。

## 工作

1. 建立 Geometry Backend capability contract（含 §4.9 v3 欄位）。
2. 實作 primitives：box、plate、shell、hole、pocket、boss、cutout、fillet、chamfer、mount；【v3】tapped hole（cosmetic thread metadata）、counterbore。
3. 實作 PCB envelope、USB-C cutout、M3 mounting、removable cover。
4. 建立 deterministic feature ordering 與 structured error handling。
5. 輸出 STEP、STL、glTF 或 web preview format；DXF 只輸出指定 2D section/sketch。
6. 建立 topological naming 風險隔離：內部以 semantic feature ID 對應，避免把 transient face index 當永久識別（依 §4.14）。
7. 【v3】螺紋不建實體：孔徑採 tap drill（M3 → Ø2.5 mm），metadata 記錄 `thread: M3x0.5`、`engagement_mm`。
8. 【v3】建立 geometry boundary corpus（≥ 10 例）與 negative corpus（≥ 10 例：負尺寸、壁厚 < 容許、fillet 大於邊長、boolean 無交集、越界尺寸等）。
9. 【v3】Adapter 在獨立 process 執行並有 timeout，kernel crash 回傳 `MEGIS-GEO-*`。

## 完成條件（Exit criteria）

- 相同 IR、engine version 與 seed 重跑得到相同 semantic manifest（【v3】semantic fingerprint）。
- STEP 可由獨立 parser 重新開啟（【v3】第二路徑：FreeCAD headless import 或 STEP 結構層 parser）。
- 每個 solid 通過 kernel validity check。
- Reference Case 的主要尺寸符合 tolerance。
- 故意破壞的尺寸、boolean、fillet case 回傳明確 error code。
- golden artifact comparison 通過。
- 【v3】Base 與 Cover 組合干涉體積 ≤ `kernel_tol` 等效體積。
- 【v3】所有 semantic feature ID 可由幾何謂詞重新定位。
- 【v3】Boundary corpus 100% 產生 kernel-valid 且尺寸合格；negative corpus 100% 回傳預期錯誤碼；0 個「看似成功」輸出。
- 【v3】越界輸入不被 clamp（不變量 18）。
- 【v3】本機與 CI fingerprint 一致或差異已 ADR。
- 【v3】G2-REV-001 passed；G2-ACC-001 sign-off。

## 必要證據

capability contract、golden／boundary／negative 結果、fingerprint、第二 parser 重載紀錄、干涉檢查結果、review 報告。

## 回滾邊界

每個 feature generator 為獨立 commit；adapter 介面變更需 ADR。

## 非目標

DFM 規則判定、drawing、BOM。

---

# 11. G3 — 規則與驗證

## 目標

用少量可信規則證明工程決策鏈，不追求規則數量。

## 進入條件（Entry criteria）

- G2 accepted。
- 施工 Agent 可存取網路以查證規則來源（D6：自我審查）。

## 11.1 規則治理（Rule governance）

每條規則必須包含：

```yaml
rule_id: CNC_MIN_WALL_001
version: 1.0.0
status: approved              # 【v3】draft | in_review | approved | deprecated
source: SRC-INTERNAL-ME-001   # 【v3】指向 docs/RULE_SOURCES.md 登錄 ID
source_revision: 2026-A
source_clause: "§3.2"         # 【v3】條號，不存原文
owner: mechanical_engineering
reviewed_by: null             # 【v3】approved 時必填，對應 sign-off
scope: {}
condition: {}
severity: error
recommendation: increase_wall
auto_fix: false
effective_date: 2026-09-16
applicability:                # 【v3】
  envelope_ref: envelope.cnc_enclosure@1.0.0
  materials: [AL6061-T6]
  processes: [cnc_3axis]
tests:
  positive: []
  negative: []
  boundary: []
```

【v3】規則生命週期：`draft`（建立）→ `in_review`（施工者以全新 session 查核來源）→ `approved`（需 `rule_source_check` 決策紀錄，且至少 1 份官方標準／製造商文件或 2 份獨立一致的公開來源）→ `deprecated`（保留歷史，不再評估新 Design Run）。依 D6，規則由施工 Agent 自我審查核准；未附可查證來源者不得設為 `approved`。

## 11.2 第一批規則

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

【v3】補充規則（仍計入 20–30 條上限內，依價值取捨）：

| 規則 ID（提議） | 內容 | 嚴重度 | 來源類型 |
|---|---|---|---|
| `CNC_TAP_BLIND_001` | 盲孔攻牙：鑽孔深度 ≥ 螺紋長 + 未完全螺紋餘量 | error | 內部準則／加工廠能力 |
| `FAS_ENGAGE_AL_001` | 鋁材內螺紋嚙合長度 ≥ 提議 2.0 D | error | 內部準則（需上網查證加工與扣件資料後核准） |
| `FAS_BOSS_WALL_001` | 螺紋孔周圍剩餘壁厚 ≥ 提議 1.5 mm | error | 內部準則 |
| `FAS_CBORE_DEPTH_001` | 沉頭深度 ≥ 螺絲頭高 + 餘量 | warning | ISO 4762 尺寸 ＋ 內部餘量 |
| `FAS_CLEAR_HOLE_001` | 通孔直徑符合 ISO 273 選定等級 | error | ISO 273 |
| `CNC_INT_RADIUS_001` | 內腔垂直角半徑 ≥ 刀具半徑 + 餘量 | error | 加工廠能力 |
| `CNC_DEPTH_RATIO_001` | 口袋深度 ≤ 提議 4 × 刀徑 | warning | 加工廠能力 |
| `CNC_SETUP_COUNT_001` | 必要加工面方向數 ≤ envelope 允許裝夾數 | error | envelope |
| `PCB_EDGE_CLEAR_001` | PCB 邊至內壁 ≥ 設定間隙 | error | 內部準則 |
| `PCB_STANDOFF_001` | Standoff 高度 ≥ 底面零件高 + 間隙 | error | 內部準則 |
| `PCB_TOP_CLEAR_001` | 零件頂面至上蓋內面 ≥ 設定間隙 | error | 內部準則 |
| `CON_USBC_OPEN_001` | USB-C 開口：receptacle 齊平時 ≥ receptacle 外殼 + 間隙；內縮時 ≥ 插頭 overmold 外形 + 間隙 | error | 零件 datasheet ＋ USB Type-C 規格 |
| `ASM_COVER_REMOVE_001` | 上蓋沿 +Z 移除路徑無干涉 | error | 幾何 |
| `ASM_COLLISION_001` | 任兩 component 無干涉 | error | 幾何 |
| `TOL_GENERAL_001` | 未標註尺寸套用一般公差等級 | info | ISO 2768-1 |

表中「提議」數值在 `approved` 前必須由施工者上網查證（標準摘要、製造商技術文件、加工服務商公開設計指南等），記錄 URL 與取用日期；不得憑記憶填入數值並宣稱已核對。

## 11.3 衝突與豁免（waiver）

規則衝突不只靠全域 priority。系統必須記錄：

- 被哪一條規則覆蓋。
- 覆蓋理由。
- 決策者。
- 生效範圍。
- 是否需要重新驗證。

Waiver 必須有 ID、owner、理由、到期條件及受影響 artifacts。【v3】Waiver 存放於 `execution/signoffs/`（格式見附錄 A.6），到期或輸入變更時自動失效並觸發 maturity 重算；`unsafe_to_default` 與安全類規則不得被 waive。

## 11.4 【v3】驗證結果格式

```json
{
  "rule_id": "CNC_MIN_WALL_001",
  "rule_version": "1.0.0",
  "status": "pass | fail | not_applicable | error",
  "severity": "error",
  "measured": { "value": 1.8, "unit": "mm" },
  "limit": { "value": 2.0, "unit": "mm", "comparator": ">=" },
  "entity_refs": ["base.wall.minus_x"],
  "evidence": { "method": "min_distance", "tolerance": "kernel_tol" },
  "disposition": "open | fixed | waived",
  "waiver_ref": null
}
```

## 11.5 【v3】成熟度計算器（Maturity evaluator）

G3 建立 `megis.maturity`，實作 §1.4 表格；每個狀態至少一組 positive 與 negative table-driven tests；evaluator 為 manifest `maturity` 欄位的唯一寫入者。

## 完成條件（Exit criteria）

- 每條規則具有 positive、negative、boundary tests。
- Reference Fixture benchmark 中沒有 false release。
- 報告同時呈現 precision、recall、false-positive count，不只 detection rate。
- 規則更新會觸發相關 golden regression。
- 任一 error 級規則未處置時，成熟度不得升到 PROTOTYPE。
- 【v3】Benchmark corpus ≥ 30 個已標註缺陷案例 ＋ ≥ 10 個無缺陷案例；報告附 Wilson 95% 信賴區間。
- 【v3】所有 `approved` 規則的來源已上網查證並附 URL 與取用日期（E4 決策紀錄）。
- 【v3】Maturity evaluator table tests 全數通過。
- 【v3】Waiver 到期與輸入變更觸發重算的測試通過。
- 【v3】Holdout corpus 依 §18.1 先封存後施工的程序執行，false release = 0。
- 【v3】G3-REV-001 passed；G3-ACC-001 sign-off。

## 回滾邊界

每條規則或 rule pack 為獨立 commit；規則版本遞增，不就地修改已 approved 規則。

## 非目標

大量規則、機器學習規則推薦。

---

# 12. G4 — 模組與限制條件組合

## 目標

證明 Module 可攜帶幾何、介面、clearance 與規則 metadata，並能組成產品。

## 進入條件（Entry criteria）

- G3 accepted。

## 第一批完整模組

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

【v3】Capability level 對系統行為的限制：

| 能力等級 | UI | 佈局 | 幾何 | 驗證 | 成熟度上限 |
|---|---|---|---|---|---|
| `metadata_only` | 顯示為「僅資料」、不可放置 | 否 | 否 | 否 | DRAFT |
| `layout_capable` | 可放置 envelope | 是 | envelope box | collision／clearance | CONCEPT |
| `geometry_capable` | 可放置 | 是 | 是 | 幾何規則 | PROTOTYPE（需規則通過） |
| `validated` | 可放置 | 是 | 是 | 全部適用規則 ＋ golden | PROTOTYPE |

## 匯入政策（Import policy）

STEP／DXF 自動抽取只可產生可證明的資訊：

- bounding box。
- solid／shell count。
- candidate holes／planar sections。
- file unit（存在時）。
- parser warnings。

Material、loads、supplier、electrical／acoustic property、mount intent 必須來自 datasheet、使用者或工程師確認，並保存 provenance。

【v3】Import 安全要求（即使 single-user local 也適用）：parser 在獨立 subprocess 執行；檔案大小上限（提議 50 MB）；timeout（提議 60 s）；實體數量上限；拒絕副檔名與內容不符的檔案；parser 例外一律轉為 `MEGIS-IMP-*`；匯入結果標示 `derived_from_import` 且不得自動提升 capability level。

## 完成條件（Exit criteria）

- 將 PCB／USB-C 拖入 fixture graph 會產生 mount、clearance、opening constraints。
- 移除 Module 會清除或明確標示所有 dependent constraints。
- 不完整 metadata 不會被自動補成虛構工程值。
- capability level 會正確限制 UI、CAD 與 validation 行為。
- 【v3】Relationship vocabulary（§4.16）每一型別有語意測試與反例。
- 【v3】Module 版本升級時，引用舊版的 Design Run 可重現且不被靜默升級。
- 【v3】Import 惡意／損毀樣本集（≥ 10 例：超大、截斷、錯誤副檔名、深度巢狀、零實體）全部被安全拒絕。
- 【v3】G4-REV-001 passed；G4-ACC-001 sign-off。

## 回滾邊界

每個 Module 為獨立 commit；vocabulary 變更需 schema MINOR 版本。

## 非目標

任意第三方 CAD 零件庫、自動推斷 datasheet。

---

# 13. G5 — 原型套件與可重現性

## 目標

產出可稽核、可重建、誠實標示成熟度的 Prototype Package。

## 進入條件（Entry criteria）

- G4 accepted。
- Drawing 路徑的 G0 決策（pass／fallback）已確認。

## 套件結構

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

【v3】Package 名稱中的 `release_manifest.json` 保留 v2 命名以相容，但其 `maturity` 欄位不得為 `RELEASED`，除非 §1.4 條件成立；檔案頂部必須有 `package_kind: PROTOTYPE_PACKAGE`。

## 清單（Manifest）必備資訊

- input hashes。
- artifact hashes（【v3】`byte_sha256` 與 `semantic_fingerprint`）。
- schema、engine、library、rule、model、solver versions。
- OS／runtime identity（【v3】含 `platform.machine()`、是否 emulation）。
- random seed。
- executed validations。
- passed、failed、waived、skipped gates。
- assumptions、unknowns、human sign-offs。
- maturity state（【v3】由 evaluator 計算，附計算輸入摘要）。
- 【v3】`classification: DESIGN_RUN`、`fingerprint_policy_version`、`envelope_ref`、`dna_ref`、`module_versions`、`ai_involvement`（是否使用 AI、模型與 prompt 版本、哪些欄位曾為 `llm_proposed`）。

## 圖面政策

圖面由 Engineering IR／feature metadata 驅動，不從 STEP 猜 critical dimension。第一版只允許固定 Fixture template 與 dimension whitelist，且標示 `DRAFT — ENGINEERING REVIEW REQUIRED`。

【v3】Drawing QA checklist（每張圖）：標題欄（design_id、revision、材料、一般公差、單位、投影法）；白名單尺寸全部出現且數值與 IR 一致；無重複或矛盾尺寸；水印存在；視圖比例標示；QA 結果（pass/fail/N/A 每項）寫入 manifest。

## 【v3】BOM 規格

欄位：`item`、`part_id`、`description`、`quantity`、`material`、`finish`、`standard`（如 ISO 4762）、`size`、`module_ref`、`module_version`、`revision`、`provenance`。排序固定（item 升冪），CSV UTF-8、LF 換行。BOM 數量必須與 IR component quantity 完全一致，否則 `MEGIS-PKG-*`。

## 完成條件（Exit criteria）

- 從 clean environment 使用同一 input 可重新產生完整 package。
- manifest 能驗證所有 artifact hash。
- BOM 不從 filename 推測，且 quantity／material／revision 與 IR 一致。
- Drawing 經固定 checklist 或人工 QA，結果寫入 manifest。
- Package 明確標示 `PROTOTYPE`，不含 Production Ready 宣告。
- 【v3】Clean environment 重建之所有 semantic fingerprint 與原始一致（E3：CI 或全新 session 自我審查）。
- 【v3】本機（含 ARM64 emulation）與 CI x64 fingerprint 一致，或差異欄位已依 ADR 列為 informational。
- 【v3】竄改任一 artifact 1 byte，manifest 驗證必須失敗（負向測試）。
- 【v3】存在未處置 error 的案例產出 package 時，maturity 正確停在 CONCEPT 或以下。
- 【v3】G5-REV-001 passed；G5-ACC-001 sign-off。

## 回滾邊界

Package builder、BOM、drawing、manifest 各為獨立 commit。

## 非目標

量產放行、ERP/PLM 整合。

---

# 14. G6 — 引導式介面與 AI 輔助

## 目標

只對已驗證的 vertical slice 建立新人 UI；不先做空殼式通用 Wizard。【v3】以 adapter 替換 UX-0 的 `PrototypeViewModel`，並導入受約束、可棄權、可關閉的 AI 輔助。**系統在 AI 完全停用時必須仍然完整可用。**

## 進入條件（Entry criteria）

- G5 accepted。
- D3（LLM provider）已決策；若決策為「無 provider」，G6-AI-001／002 以 recorded fixtures 與本機 stub 完成介面與評估框架，真實模型評估移至 G9。

## 流程

```text
選擇 Fixture / Enclosure
↓
（可選）以自然語言描述需求 → AI 萃取為 Requirement 草稿（llm_proposed）【v3】
↓
選擇大致外形
↓
加入 PCB 與 USB-C
↓
回答用途、數量、可拆性與優先目標
↓
檢視 assumptions、unknowns 與 AI 提議值（逐項確認或拒絕）【v3】
↓
接受或修改有證據的建議
↓
Generate
↓
查看 CAD、規則結果與 Prototype Package
```

## 動態問題引擎（Dynamic Question Engine）

問題的排序以資訊價值與安全性決定：

1. `unsafe_to_default` 先問。
2. 會改變架構或製程的問題優先。
3. 可由可靠資料衍生者不問。
4. recommendation 必須附來源與適用範圍。
5. 永遠提供「不知道，交由系統建議」，但 critical unknown 不得因此消失。

【v3】補充：

6. 每個問題必須對應至少一個 IR 欄位與一個 envelope 範圍；不影響 IR 的問題不得出現。
7. 問題排序演算法必須是 deterministic（相同狀態 → 相同順序），並有 golden 測試。
8. 使用者選「不知道」時，若欄位為 `unsafe_to_default`，系統必須阻擋生成並說明原因與可行的下一步（例如「請提供 PCB 尺寸或上傳 PCB 外形圖」）。
9. 問題文字以繁體中文、非專業語言撰寫，專業詞首次出現附白話解釋。

## 信心標示政策

MVP 不顯示未校準的 60%、85%、92% 等概率。改用：

```text
Verified
Supported
Partially supported
Unknown
Needs engineering review
```

等累積有標註資料後，再以 Brier score、ECE 或適用 calibration 方法證明百分比可信。

【v3】對應規則：

| 標示 | 條件 |
|---|---|
| Verified | 值為 known 或 engineer_override，且相關規則 pass |
| Supported | 值為 derived／defaulted（已核准），相關規則 pass |
| Partially supported | 部分相關規則 not_applicable 或 warning 未處置 |
| Unknown | knowledge state 為 unknown |
| Needs engineering review | 存在 waiver、fail、llm_proposed 未確認或超出 validated capability |

## 14.1 【v3】AI 施工線

| 工作項目 | 內容 | 驗收條件 |
|---|---|---|
| G6-AI-001 | Provider adapter 與離線 fallback：預設關閉；可設定 provider、模型版本、prompt 版本、timeout、單次成本上限 | AI 關閉時所有 E2E 測試通過；adapter 故障回傳 `MEGIS-AI-*` 且流程退回表單 |
| G6-AI-002 | Intent → Requirement 萃取：structured output 綁定 Requirement JSON Schema；每欄標 `llm_proposed`；附 `evidence_span`（使用者原文引用位置） | 100% 輸出通過 schema；無 evidence span 的具體數值一律拒收；未確認值無法進入 IR confirmed 區 |
| G6-AI-003 | AI 評估語料與報告：≥ 50 筆標註 intent，類別包含完整、缺資訊、矛盾、超出 envelope、單位混用、prompt injection | 報告第 18.3 節全部 AI KPI；`unsafe_to_default` 欄位 hallucination = 0；injection resistance = 100% |
| G6-AI-004 | AI 解釋器：以 IR、規則結果與 manifest 為唯一事實來源產生白話解釋 | 解釋中出現的每個數值必須可在來源資料中找到（自動比對測試）；找不到即拒絕輸出 |

## 完成條件（Exit criteria）

- 新人可在不輸入 CAD 專業詞的情況下產生 Reference Fixture。
- UI 不提供超出 capability envelope 的選項，或清楚標成 unsupported。
- 生成前必須顯示 assumption review。
- UI 與直接 API 對相同輸入產生等價 IR。
- usability test 保存題數、完成率、錯誤點及人工介入次數。
- 【v3】Usability test ≥ 5 位非 CAD 背景參與者；記錄任務完成率、完成時間中位數、錯誤點、求助次數，並與 UX-0 基線比較。
- 【v3】WCAG 2.2 AA 自動化檢查通過，並有人工鍵盤與螢幕閱讀器抽查紀錄。
- 【v3】AI 開啟與關閉兩種模式的 E2E 測試皆通過，且產生等價 IR（AI 模式在使用者確認所有提議值後）。
- 【v3】G6-AI-001～004 acceptance 全數通過。
- 【v3】UI 不顯示任何百分比信心值（自動化掃描測試）。
- 【v3】G6-REV-001 passed；G6-ACC-001 sign-off。

## 回滾邊界

UI 路由、Question Engine、每個 AI work item 各為獨立 commit；AI 功能以 feature flag 控制，可整體停用。

## 非目標

聊天式自由設計、語音輸入、多語系（zh-TW 以外）。

---

# 15. G7 — 聲學薄切片

## 目標

驗證 Product DNA、Module 與 Constraint Graph 能描述聲學模組；solver 能力獨立分級。

## 進入條件（Entry criteria）

- G6 accepted。
- Acoustic schema-only golden input（G1）存在。

## 範圍

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

## 求解器等級（Solver levels）

```text
L0: geometry and parameter report
L1: validated reduced-order model
L2: template-based COMSOL run
L3: mesh-converged engineering simulation with reviewer sign-off
```

COMSOL 授權、API 或 worker 不可用時，停在 L0/L1，系統仍可繼續其他 Gate；不得以近似模型冒充 L2/L3。

【v3】Solver level 精確條件：

| 等級 | 必要條件 |
|---|---|
| L0 | 腔體體積、開口面積、outlet／vent 幾何參數由幾何計算並附單位與來源 |
| L1 | 集總參數模型（例如以 Thiele/Small 參數描述驅動器，腔體以聲容、開口以聲質量與聲阻表示）；**必須以至少一組使用者提供的量測資料（SPL 或阻抗曲線）驗證**，並報告頻段內誤差；未驗證只能標 L0 |
| L2 | 固定 COMSOL 模板執行成功；記錄 mesh、邊界條件、材料、頻率範圍；無收斂證明 |
| L3 | L2 ＋ mesh convergence study ＋ 與量測比對 ＋ 具名聲學工程師 sign-off |

【v3】聲學專屬驗證：sealed volume 閉合性（封閉 shell 檢查）、洩漏路徑列為 assumption（不可預設為零洩漏而不標示）、gasket 壓縮量列為 unknown 直到提供材料資料、mesh 聲阻抗未提供時標 unknown。

## 完成條件（Exit criteria）

- Acoustic golden case 與 Fixture 使用相同 core IR／graph infrastructure。
- sealed volume、outlet connectivity、leak assumptions 可被驗證。
- 結果標示 solver level、mesh、boundary、material、frequency range 與 limitations。
- 每個數值結果可追溯到 solver input 與版本。
- 【v3】沒有為 Acoustic 新增專屬 IR 頂層欄位（只能透過 Module、Interface、Relationship 擴充）；若必須新增，需 BCR。
- 【v3】所有數值結果標示 solver level；L1 以上附量測比對證據。
- 【v3】G7-REV-001 passed；G7-ACC-001 sign-off。

## 非目標

自動聲學最佳化、ANC 演算法、麥克風陣列波束成形。

---

# 16. G8 — 機器人薄切片

## 目標

驗證 Module composition、assembly relationship 與 layout constraints 可跨到 Robot Car。

## 進入條件（Entry criteria）

- G6 accepted。
- Robot schema-only golden input（G1）存在。

## 範圍

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

## 完成條件（Exit criteria）

- Robot golden case 與 Fixture 共用 ID、unit、provenance、graph、rule-result 及 manifest contracts。
- motor／wheel、battery／controller、sensor／cover 關係可表達並驗證 referential integrity。
- layout collision、clearance、mounting zone 可執行。
- 缺少 kinematics、cable 或 safety validation 時，maturity 不得超過 CONCEPT。
- 【v3】含鋰電池的設計，assumptions 必須強制列出「電池安全、熱失控、充放電規範未驗證」，且不可被 waive。
- 【v3】質心位置與總質量僅在所有 component 質量為 known／database 時計算；否則標 unknown。
- 【v3】沒有為 Robot 新增專屬 IR 頂層欄位；若必須新增，需 BCR。
- 【v3】G8-REV-001 passed；G8-ACC-001 sign-off。

## 非目標

運動學、控制、線束、結構強度、安全認證。

---

# 17. G9 — 強化與擴充

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
- 【v3】AI 評估語料的新增案例。
- 【v3】風險登錄表更新。
- 【v3】自我審查（全新 session）與決策紀錄。

【v3】擴充准入條件（全部成立才可開始新 slice）：

- 前一 slice 的所有 KPI 在 regression corpus 上未退化。
- 無開啟中的 high impact blocker。
- 新規則來源可經公開資料上網查證。
- Envelope 變更 sign-off 已完成。
- 新 slice 的非目標已明確寫出。

---

# 18. 驗證策略

## 18.1 基準語料（Benchmark corpus）

Benchmark 必須版本化並分成：

```text
golden
negative
boundary
regression
holdout
```

每個 case 保存 input、oracle、適用 envelope、expected validations 與 reviewer。

【v3】補充：

- `holdout`：因 D6 沒有獨立審查者，改採「先封存、後施工」：holdout 案例與 oracle 必須在相關實作開始前以獨立 commit 建立，並把 oracle 檔 hash 記入 `docs/ACCEPTANCE.md`；之後修改 oracle 視同 golden 更新，需 ADR 說明理由。此做法無法完全排除施工者偏誤，列為 R-AGT-002。
- 每個 corpus 有 `corpus_version`；任何 case 新增、刪除或 oracle 修改都遞增版本並記錄理由。
- 從實際缺陷（bug、自我審查發現、使用者回報）產生的案例必須加入 `regression`，且永不刪除。
- 最小規模：G2 geometry boundary ≥ 10、negative ≥ 10；G3 defect ≥ 30、clean ≥ 10；G4 import 惡意樣本 ≥ 10；G6 AI intent ≥ 50；usability ≥ 5 人。

## 18.2 KPI 定義

不得只寫「成功率 90%」。每個 KPI 必須定義：

- numerator／denominator。
- corpus version。
- seed 與 runtime version。
- timeout。
- pass definition。
- confidence interval 或樣本量。
- false positive／false negative。

核心指標：

| 指標 | 定義 | 【v3】目標 |
|---|---|---|
| Generation pass rate | 在固定 supported corpus 中，產生 kernel-valid、尺寸合格 artifact 的比例 | golden 100%；boundary 100% |
| Validation recall | 已標註缺陷被偵測的比例 | error 級缺陷 100% |
| Validation precision | 系統提出的缺陷中真正成立的比例 | 報告並追蹤，G3 不設硬門檻 |
| False release | 存在 error 級已知缺陷卻升級成熟度的 case 數 | 0 |
| Deterministic replay | 相同 manifest 可重建相同 semantic outputs 的比例 | 100% |
| Manual intervention | 每個成功 design run 需要人工修正的次數 | 報告 |
| Question count | 從初始 intent 到可生成 IR 的人工問題中位數 | 報告，與 UX-0 基線比較 |
| 【v3】Correct failure rate | negative corpus 回傳預期錯誤碼的比例 | 100% |
| 【v3】Silent success | 應失敗卻輸出成功 artifact 的次數 | 0 |

【v3】統計規則：比例在 n < 100 時使用 Wilson score 95% 信賴區間；KPI 報告必須附原始 case-level 結果檔，不得只報聚合值。

## 18.3 【v3】AI 指標

| 指標 | 定義 | 目標 |
|---|---|---|
| Schema conformance | 模型輸出通過 Requirement schema 的比例 | 100%（不合格者由 adapter 拒收並計入） |
| Field precision／recall | 萃取欄位與標註答案比對 | 報告 |
| Hallucinated value rate | 使用者輸入中無依據卻填入具體數值的欄位比例 | 全體報告；`unsafe_to_default` 欄位 = 0 |
| Abstention correctness | 應回 unknown 時正確棄權的比例 | 報告 |
| Out-of-envelope detection | 超出 envelope 的需求被標示的比例 | 100% |
| Unit error rate | 單位錯誤或未標單位的數值比例 | 0（adapter 拒收） |
| Injection resistance | 含注入字串的案例未改變系統行為的比例 | 100% |
| Explanation grounding | 解釋中數值可追溯至來源資料的比例 | 100% |

## 18.4 測試層級

```text
Unit tests
→ Schema / contract tests
→ Property-based tests【v3】
→ Geometry property tests
→ Rule tests
→ Golden regression（semantic fingerprint）
→ Adapter integration tests
→ Fault-injection tests【v3】
→ AI recorded-fixture regression【v3】
→ End-to-end design run
→ Accessibility tests【v3】
→ Artifact visual / engineering review
→ Gate 自我審查（全新 session）【v3】
```

## 18.5 【v3】測試紀律

- **Flaky test**：不得以自動重試讓 CI 變綠。發現 flaky 時登記 blocker、隔離（quarantine）並於同一 Gate 內修復；quarantine 中的測試不得作為任何 acceptance 證據。
- **Skip／xfail**：必須附 issue 或 blocker ID 與到期條件；verifier 統計數量並在 Gate review 中列出。
- **Golden 更新**：只能以 `golden:` commit 進行，附前後 fingerprint 差異與理由；自我審查通過前不得合併到被 Gate 引用的 fixed point。
- **Coverage**：`core`、`schema`、`maturity`、`rules` 行覆蓋率下限 85%、分支覆蓋率下限 75%。覆蓋率是下限不是目標，不得為衝覆蓋率撰寫無斷言測試。
- **CI 不呼叫網路服務**（含 LLM）；需要外部服務的測試以 recorded fixtures 取代，真實呼叫僅在人工觸發的 eval job。
- **測試資料**不得包含客戶資料或未授權 datasheet 內容。

---

# 19. 【v3】工程知識治理

## 19.1 規則來源登錄表（`docs/RULE_SOURCES.md`）

| 來源 ID | 來源 | 可存內容 | 處置 |
|---|---|---|---|
| SRC-ISO-2768-1 | ISO 2768-1 一般公差 | 公差等級與數值表的參數化結果 | 只存參數與條號，不存原文 |
| SRC-ISO-273 | ISO 273 緊固件通孔 | fine／medium／coarse 孔徑 | 同上 |
| SRC-ISO-261-262 | ISO 公制螺紋 | pitch、基本尺寸 | 同上 |
| SRC-ISO-4762 | 內六角圓柱頭螺絲 | 頭徑、頭高 | 同上 |
| SRC-USB-TYPEC | USB Type-C Cable and Connector Specification | receptacle／plug 外形參考 | 優先使用實際零件 datasheet |
| SRC-IPC-2221 | PCB 設計通則 | 參考值 | 只作 warning／info，不作 error |
| SRC-INTERNAL-ME-001 | 內部機構設計準則 | CNC 與組裝經驗值 | 需 owner 與版次；D6 下由施工者整理並附公開依據 |
| SRC-WEB-<slug> | 公開網路工程資料（製造商技術文件、加工服務商設計指南等） | 經驗值與建議值 | 至少 2 份獨立一致來源；記錄 URL 與取用日期 |
| SRC-VENDOR-<name> | 加工廠能力表 | 最小刀徑、深寬比、公差能力 | 記錄廠商、日期、有效期 |
| SRC-DATASHEET-<part> | 零件 datasheet | 零件尺寸與介面 | 記錄料號、版次、取得日期 |

## 19.2 規則

- 每個來源必須記錄：版次或發行日期、取得方式、授權限制、owner、下次審查時間。
- 標準文件受著作權保護；repository 只存參數、條號與摘要，**不得存原文或整表複製**。
- Agent 不得憑記憶填寫標準數值後標為已核對；必須上網查證並記錄 URL、取用日期與文件版次，查證前一律 `status: draft`。
- 來源過期或被取代時，所有引用規則自動標記 `needs_review`，相關 golden regression 重跑。
- 客戶或公司內部資料是否可放入 repository 依 D5 決策；預設不可。

## 19.3 知識變更影響分析

任何規則、來源、Module 或 envelope 變更，必須自動列出：受影響的規則、golden cases、benchmark cases、既有 Design Run（需重算 maturity）、UI 問題。影響分析結果附於該 commit 的 review 請求中。

---

# 20. 【v3】AI 治理

## 20.1 AI 可以做

- 將自然語言意圖轉為 Requirement 草稿（`llm_proposed`）。
- 建議下一個要問的問題（最終排序仍由 deterministic Question Engine 決定）。
- 以 IR、規則結果與 manifest 為唯一事實來源產生白話解釋。
- 摘要 assumptions 與 unknowns。

## 20.2 AI 不得做

- 產生或修改幾何、尺寸、公差、材料屬性、規則結果、maturity。
- 核准規則、waiver、sign-off 或 envelope 變更。
- 在未經使用者確認下將任何值寫入 IR confirmed 區。
- 輸出來源資料中不存在的工程數值。
- 顯示信心百分比。

## 20.3 技術控制

- **版本鎖定**：provider、模型識別字、prompt template 版本、schema 版本寫入 manifest 的 `ai_involvement`。
- **結構化輸出**：只接受綁定 JSON Schema 的輸出；不合格輸出拒收並記錄 `MEGIS-AI-002`，不嘗試「修補」後接受。
- **資料最小化**：只傳送完成任務所需的文字；預設不傳送 CAD 檔、datasheet 或客戶識別資訊；傳送任何檔案內容需 D5 授權。
- **不可信輸入隔離**：使用者文字、檔名、metadata、datasheet 文字只能放入資料區塊，不得拼接進指令區；system prompt 明示資料區塊內的指令一律忽略。
- **成本與速率**：單次 Design Run 的 AI 呼叫次數、token 與成本上限可設定；超過時停止 AI 並退回表單。
- **紀錄**：保存 prompt 版本、輸入 hash、輸出、拒收原因；日誌不保存 API key，敏感欄位遮罩。
- **可重現性**：AI 輸出不被視為 deterministic；Design Run 的可重現性以「使用者確認後的 Requirement」為起點，AI 原始輸出僅作稽核紀錄。
- **離線**：AI 停用時所有功能以表單與 Question Engine 完成。

## 20.4 模型變更流程

更換模型或 prompt 版本時：重跑 AI 評估語料 → 與前版比較全部 AI KPI → 任何 KPI 退化需 ADR 說明並經使用者同意 → 更新 recorded fixtures（`golden:` commit）。

---

# 21. 安全與人的責任

## 21.1 生成前揭露

所有 design run 在生成前顯示：

- 使用者提供的事實。
- 系統衍生值。
- 使用的 defaults。
- 未知值。
- unsafe-to-default 值。
- 不在驗證範圍的能力。
- 【v3】尚未確認的 AI 提議值。
- 【v3】目前可達到的最高 maturity 與原因。

## 21.2 禁止自動升級類別

下列類別不得由本系統自動升級為 Production Ready：

- Helmet、medical/hearing、human safety device。
- Underwater vehicle、pressure vessel。
- Robot safety structure。
- 法規管制、生命安全、重大財產風險產品。
- 【v3】含鋰電池產品的電池安全相關部分。
- 【v3】承受人體重量或懸吊載重的治具與結構。
- 【v3】接觸食品、藥品或可能被兒童使用的產品。

【v3】Product DNA 必須宣告 `safety_category`；屬上述類別者 evaluator 強制套用 maturity 上限，且 UI 在首頁選擇時即顯示限制。

## 21.3 簽核

安全 Gate 需要具名 reviewer、review scope、evidence、時間與 signature reference。LLM 的「看起來合理」不是簽核。

【v3】簽核規則：

- 格式見附錄 A.5；依 D6，施工 Agent 完成自我審查後可自行記錄決策，`reviewer_name` 填 Agent 身分（例如 `codex`、`claude-code`）並附審查 session ID；使用者可隨時以新紀錄否決。`engineering_review` 類型必須由具名工程師簽署，Agent 不得代簽。
- 簽核範圍必須列出 artifact byte hash 或 fingerprint；artifact 變更後簽核自動失效。
- 簽核不得溯及既往擴大範圍；新增範圍需新簽核。

## 21.4 【v3】輸出標示

所有 Design Run 輸出（CAD 檔 metadata、drawing 水印、報告頁首、UI 結果頁）必須顯示 maturity 與 `ENGINEERING REVIEW REQUIRED`（maturity < ENGINEERING_REVIEWED 時）。STEP header 的 description 欄位應寫入 design_id、revision 與 maturity。

---

# 22. 資訊安全、隱私與供應鏈

## 22.1 多使用者前的必要能力

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

## 22.2 【v3】本機部署基線

- 所有服務綁定 `127.0.0.1`；不得綁定 `0.0.0.0` 或區域網路介面（自動化測試檢查）。
- 無 analytics、telemetry、外部字型、CDN 或未核准 API。
- 所有寫入、快取、暫存、環境、下載限制在 repository 工作區內。
- 不建立指向工作區外的 symlink／junction。

## 22.3 【v3】威脅模型（本機單一使用者範圍）

| 威脅 | 範例 | 控制 |
|---|---|---|
| 惡意 CAD 檔 | 讓 parser 崩潰或耗盡記憶體的 STEP | subprocess、timeout、大小與實體數上限 |
| Prompt injection | datasheet 內含「忽略規則」字串 | 資料區塊隔離、AI 無寫入權、injection 語料測試 |
| 秘密外洩 | API key 被寫入 handoff 或 commit | secret scan（pre-commit 與 CI）、環境變數、日誌遮罩 |
| 供應鏈 | 被竄改的相依套件 | hash-pinned lockfile、`npm ci`、升級需 ADR ＋ 全 regression |
| 工作區逃逸 | 工具寫入工作區外 | 路徑檢查、環境變數固定 cache 目錄 |
| 狀態竄改 | 手動修改狀態檔使未完成項目變 done | verifier 核對 Git history、commit SHA、evidence |
| 網路暴露 | dev server 對外開放 | 綁定檢查測試 |
| 資料外送 | 客戶 CAD 被送到雲端 LLM | D5 決策、AI adapter 預設不傳檔案、呼叫紀錄 |

## 22.4 【v3】供應鏈政策

- Python：lockfile 含 hash，安裝使用 `--require-hashes`（若工具鏈限制無法使用，需 ADR 記錄替代控制）。
- Node：`package-lock.json` 必須提交；CI 使用 `npm ci`。
- 相依升級：一次一組相關套件；ADR 記錄理由；全部 regression 與 fingerprint 比對通過；fingerprint 改變時視同 golden 更新流程。
- 不得從未知來源下載二進位檔；外部工具（如 FreeCAD）需記錄官方來源 URL、版本與檔案 hash。

---

# 23. 【v3】使用者體驗原則

1. **新人優先**：預設使用者不懂 CAD；首頁不是 prompt box，而是「我要做什麼？」的選擇。
2. **誠實優先於流暢**：寧可多一個確認步驟，也不隱藏假設或把建議偽裝成事實。
3. **不問可以推算的東西；只問會改變結果的問題**。
4. **永遠有「不知道」**，但不讓 critical unknown 消失。
5. **不支援的選項顯示為停用並說明原因**，不直接隱藏導致使用者困惑。
6. **視覺優先**：外形、介面位置等以圖示或 3D 預覽輔助選擇。
7. **可逆**：每一步可返回修改，修改後相關衍生值與 maturity 即時更新。
8. **成熟度常駐**：結果頁與下載前都顯示 maturity 與限制。
9. **無障礙**：WCAG 2.2 AA；鍵盤完整操作；對比度與焦點可見。
10. **語言**：繁體中文為主；技術名詞可保留英文並附白話解釋。
11. **本機資產**：不載入外部字型、腳本或圖片。
12. **錯誤訊息**：使用 `user_message_zh_tw` 說明發生什麼、為什麼、下一步怎麼做；工程細節可展開。

---

# 24. 執行環境、營運與資料管理

## 24.1 正式環境需要

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

## 24.2 【v3】本機營運基線（G6 前）

- `OPERATIONS.md` 必須包含：從零重建環境、驗證工具鏈、執行完整驗證、啟動 UI、清理暫存、備份與還原 `.runs/` 與狀態檔、常見錯誤碼處置。
- Structured log 格式：JSON Lines，欄位 `timestamp`、`level`、`correlation_id`、`job_id`、`event`、`error_code`、`detail`。
- Health check：toolchain 版本、kernel 可建立 solid、磁碟空間、佇列狀態。
- 軟體版本 `megis-vX.Y.Z`；設計 Package 以 `design_id@revision` 識別，兩者命名空間不重疊。

## 24.3 【v3】資料管理

| 資料 | 保留 | 刪除方式 | 備註 |
|---|---|---|---|
| Golden／benchmark | 永久（版本化） | 只可透過 corpus 版本更新 | — |
| Design Run 產物 | 預設 90 天（D9） | 使用者操作刪除；刪除前顯示清單並確認 | 已簽核者保留至使用者明確刪除 |
| Sign-off／waiver | 永久 | 不刪除，只可 supersede | 稽核必要 |
| 日誌 | 30 天 | 自動輪替 | 不含秘密 |
| AI 呼叫紀錄 | 90 天 | 自動輪替 | 輸入以 hash 保存，原文保存需 D5 |
| 使用者上傳檔 | 與所屬 Design Run 相同 | 同上 | 不入 Git |

- 智慧財產：使用者輸入與產物屬使用者所有；不得用於未授權用途或送往外部服務。
- 刪除操作屬破壞性操作，Agent 必須事先取得使用者同意。

---

# 25. 開工條件與完成定義（DoR／DoD）

## 25.1 【v3】開工條件（Definition of Ready）

- 所有 `depends_on` 為 done。
- Acceptance 可被客觀驗證（有明確 pass/fail 判定）。
- 已知需要的使用者決策已取得。
- 輸入資料存在且版本明確。
- 驗證命令已規劃（可在施工中補齊，但 done 前必須完整）。
- 無未解除且相關的 blocker。
- 預期證據等級已設定。

## 25.2 工作項目完成定義（Definition of Done）

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
- evidence 可由另一個 Agent session 重跑。
- commit scope 單一且訊息使用簡潔英文。
- 【v3】證據達到 `evidence_level_required`。
- 【v3】需要審查者，review.status = passed。
- 【v3】新 manifest 符合 classification／maturity 規則。
- 【v3】未違反 artifact 大小預算。
- 【v3】新增錯誤碼已登錄於 `ERROR_CODES.md`。
- 【v3】claim 已釋放、handoff 已寫。
- 【v3】control-plane verifier 通過。

## 25.3 Gate 完成定義

Gate 完成還必須額外具備：

- Gate exit criteria 全部通過。
- 未完成項目已移出 Gate 或正式登記 blocker。
- architecture／decision／risk 文件與實作一致。
- 下一 Gate 的 entry conditions 已滿足。
- 【v3】所有 exit criteria 證據 ≥ E3。
- 【v3】`Gx-REV-001` 全新 session 自我審查報告 passed，且 CI 對同一 commit 全綠。
- 【v3】`Gx-ACC-001` 使用者 `gate_acceptance` sign-off（E4）。
- 【v3】`docs/ACCEPTANCE.md` 已登錄 Gate、commit、review、sign-off。

---

# 26. 完整工作佇列

本清單只定義工作、依賴與驗收，**不含施工狀態**；狀態只存在於 `execution/WORK_QUEUE.yaml`。v2.0 的 30 個 ID 全部保留（以 ◆ 標示），其餘為 v3.0 新增。轉入 `WORK_QUEUE.yaml` 時必須補齊完整 acceptance、verification commands 與 evidence level，且不得同時標示多個 `in_progress`。

欄位說明：「依賴」＝ depends_on；「證據等級」＝ 最低證據等級。

## 26.1 V3 相容補強線（V3C，導入既有 repository 時使用）

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 | 新 repository 對應 |
|---|---|---|---|---|---|
| V3C-BCR-001 | 導入 v3.0 藍圖 | — | README 指向 v3；ADR；WORK_QUEUE 新增 v3 項目；verifier ID 清單更新並有測試；已 done 項目未被修改 | E3 | G0-REP-001 |
| V3C-CTL-001 | 控制面 schema 1.1 與 claim | V3C-BCR-001 | schema 1.1.0 選填欄位；`AGENT_CLAIM.json`；§5.13 檢查 1–6、9 生效 | E3 | G0-REP-001 |
| V3C-DOC-001 | 補齊控制面文件 | V3C-BCR-001 | §5.1 全部文件存在且非空殼；`CLAUDE.md` 不與 `AGENTS.md` 衝突 | E2 | G0-DOC-001 |
| V3C-DEC-001 | G0 決策補記 | V3C-DOC-001 | §8.1 D1–D9 全部有 ADR（D6、D7、D8 依使用者決定記錄）；已由既有施工實質決定者補記證據 | E4 | G0-DEC-001 |
| V3C-DET-001 | Determinism 與 fingerprint | V3C-BCR-001 | fingerprint policy 1.0.0；STEP/DXF header 正規化；binary STL；兩次重跑一致測試；CI 執行 | E3 | G0-DET-001 |
| V3C-MAT-001 | Classification／maturity 修正 | V3C-DET-001 | 所有既有 spike manifest `maturity: null`；verifier 掃描生效；負向測試 | E3 | G0-DET-001 |
| V3C-ART-001 | Artifact 政策 | V3C-BCR-001 | `.gitattributes`；檔案大小預算檢查；重型製品不再新增入 Git（不改寫 history）；既有大型檔以 ADR 白名單 | E3 | G0-CI-001 |
| V3C-REV-001 | 已 accepted Gate 追溯審查 | V3C-CTL-001, V3C-DOC-001, V3C-DEC-001, V3C-MAT-001, V3C-ART-001 | 施工者以全新 session 對已 accepted Gate 依 v3 完成條件出具審查報告；差距皆有承接工作項目 | E3 | G0-REV-001 |
| V3C-ACC-001 | 導入完成簽核 | V3C-REV-001 | 使用者 `blueprint_change` sign-off | E4 | G0-ACC-001 |

規則：V3C 項目掛在當前 active Gate 下執行；V3C-ACC-001 完成前，當前 active Gate 不得 accepted。

## 26.2 UX-0

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| UI-0A | 最小可行基礎 | — | 鎖定前端工具鏈；本機驗證腳手架 | E2 |
| UI-0B | 施工進度中心 | UI-0A | 由狀態檔驅動；斷裂證據使完成失效 | E2 |
| UI-0C | 引導式 UX 原型 | UI-0B | Fixture flow 完整；永久合成資料標示 | E2 |
| UI-0D | 驗證與使用者驗收 | UI-0C | 自動化、瀏覽器、無障礙、使用者回饋 | E4 |

## 26.3 G0 — 基礎建設與可行性

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G0-REP-001 | 建立 repository 與狀態檔 | UI-0D | 控制面檔案與 verifier；schema 驗證 | E2 |
| ◆ G0-ENV-001 | 鎖定 Python / Node / CAD dependencies | G0-REP-001 | 乾淨重建；版本檢查腳本；lockfile | E3 |
| ◆ G0-CAD-001 | CadQuery Reference Case spike | G0-ENV-001 | STEP/STL/DXF 輸出並重新載入驗證；manifest `classification: FEASIBILITY_SPIKE`、`maturity: null` | E2 |
| ◆ G0-DRW-001 | FreeCAD TechDraw headless spike | G0-ENV-001 | pass／fallback／out_of_scope 決策與證據 | E2 |
| ◆ G0-SIM-001 | COMSOL license / API / batch feasibility decision | G0-ENV-001 | pass／fallback／out_of_scope 決策；不阻塞核心 | E2 |
| G0-DOC-001 | 控制面文件完整化 | G0-REP-001 | §5.1 文件非空殼 | E2 |
| G0-DEC-001 | G0 使用者決策 | G0-DOC-001 | D1–D9 ADR（D6、D7、D8 依使用者決定） | E4 |
| G0-DET-001 | Determinism 與 fingerprint 原型 | G0-CAD-001 | 兩次重跑 fingerprint 一致；header 正規化；maturity 掃描 | E3 |
| ◆ G0-CI-001 | 建立 baseline CI | G0-DET-001, G0-DEC-001 | lint、typecheck、unit、schema、artifact smoke、fingerprint replay、size budget、secret scan 全綠 | E3 |
| G0-REV-001 | G0 自我審查（全新 session） | 以上全部 | 自我審查報告 passed | E3 |
| G0-ACC-001 | G0 acceptance 決策紀錄 | G0-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.4 G1 — 工程契約與黃金案例

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G1-IR-001 | 定義 unit / coordinate / ID / provenance primitives | G0-ACC-001 | Quantity、Tolerance、Range、ID、Provenance、knowledge state（含 `llm_proposed`）；正反向與 property tests | E3 |
| ◆ G1-IR-002 | 定義 Engineering IR schema | G1-IR-001 | 拒絕 unit mismatch、dangling reference、duplicate ID、invalid range；JSON Schema 匯出一致 | E3 |
| G1-ERR-001 | Error taxonomy | G1-IR-001 | 錯誤物件 schema；`ERROR_CODES.md`；碼唯一性測試 | E2 |
| G1-ENV-001 | 機器可讀 envelope | G1-IR-002 | `config/envelope` 與 `SUPPORTED_ENVELOPE.md` 一致性測試 | E3 |
| G1-REQ-001 | 參考案例參數研究與決定 | G1-IR-002 | 依 §9.1 上網研究；附錄 B 無 unknown；每個 researched／defaulted 值附來源 | E4 |
| ◆ G1-IR-003 | 建立 Reference Fixture golden case | G1-REQ-001, G1-ENV-001 | Fixture、Acoustic、Robot 三個 golden inputs 通過 schema；Fixture round trip；downstream consumer 測試 | E3 |
| ◆ G1-MIG-001 | 建立 schema migration contract | G1-IR-003 | 前版 fixture migration 與 rollback round-trip；IR 凍結 1.0.0 | E3 |
| G1-REV-001 | G1 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G1-ACC-001 | G1 acceptance 決策紀錄 | G1-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.5 G2 — 治具幾何垂直切片

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G2-CAD-001 | 實作 geometry capability contract | G1-ACC-001 | 含 fingerprint_policy、resource_limits、envelope_ref；由 golden IR 驅動且不洩漏 kernel 型別 | E3 |
| ◆ G2-CAD-002 | 產生 fixture base | G2-CAD-001 | shell、boss、tapped hole、內腔半徑；kernel-valid；尺寸合格；semantic feature ID 可重新定位 | E3 |
| ◆ G2-CAD-003 | 產生 cover / fasteners / cutout | G2-CAD-002 | cover、counterbore、USB-C 開口、PCB envelope、組立干涉為零 | E3 |
| ◆ G2-CAD-004 | 輸出與重新載入 artifacts | G2-CAD-003 | STEP（兩條 parser 路徑）、binary STL、DXF、glTF；fingerprint 一致 | E3 |
| G2-NEG-001 | Boundary 與 negative geometry corpus | G2-CAD-004 | boundary ≥ 10 全數合格；negative ≥ 10 全數回傳預期錯誤碼；silent success = 0；越界不 clamp | E3 |
| G2-REV-001 | G2 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G2-ACC-001 | G2 acceptance 決策紀錄 | G2-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.6 G3 — 規則與驗證

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G3-RUL-001 | 建立 rule schema / governance / waiver | G2-ACC-001 | 規則生命週期；waiver 格式與到期失效；不可 waive 類別 | E3 |
| G3-SRC-001 | 規則來源登錄與核對流程 | G3-RUL-001 | `RULE_SOURCES.md`；來源過期觸發 needs_review；draft 規則不可被評估為 approved | E3 |
| ◆ G3-VAL-001 | 建立 geometry / collision / clearance validators | G3-RUL-001 | Validation Result 格式；已知 pass/fail cases | E3 |
| ◆ G3-VAL-002 | 建立 CNC DFM rule pack | G3-VAL-001, G3-SRC-001 | 20–30 條規則；每條 positive/negative/boundary；來源已查證（URL／取用日期） | E4 |
| G3-MAT-001 | Maturity evaluator | G3-VAL-002 | §1.4 table-driven tests；唯一寫入者；輸入變更重算 | E3 |
| ◆ G3-BEN-001 | 建立 benchmark metrics | G3-MAT-001 | defect ≥ 30、clean ≥ 10；precision、recall、FP、Wilson CI；false release = 0；holdout 先封存後施工（§18.1） | E3 |
| G3-REV-001 | G3 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G3-ACC-001 | G3 acceptance 決策紀錄 | G3-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.7 G4 — 模組與限制條件組合

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G4-MOD-001 | 建立 Module capability levels | G3-ACC-001 | 四級 capability 對 UI/layout/geometry/validation/maturity 的限制測試 | E3 |
| G4-GRF-001 | Relationship vocabulary 語意 | G4-MOD-001 | §4.16 每型別語意測試與反例 | E3 |
| ◆ G4-MOD-002 | PCB / USB-C / M3 composition | G4-GRF-001 | 加入產生 constraints；移除清除或標示 dependent constraints；不補虛構值；Module 版本固定 | E3 |
| ◆ G4-IMP-001 | 建立 safe STEP / DXF metadata extraction | G4-MOD-002 | 只抽可證明資訊；subprocess、timeout、上限；惡意樣本 ≥ 10 全數安全拒絕 | E3 |
| G4-REV-001 | G4 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G4-ACC-001 | G4 acceptance 決策紀錄 | G4-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.8 G5 — 原型套件與可重現性

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G5-PKG-001 | 建立 manifest 與 content hashes | G4-ACC-001 | byte hash ＋ semantic fingerprint；竄改偵測負向測試；maturity 由 evaluator | E3 |
| ◆ G5-BOM-001 | 建立 BOM exporter | G5-PKG-001 | §13 BOM 規格；數量與 IR 一致；正規化 fingerprint | E3 |
| ◆ G5-DRW-001 | 建立 fixed-template draft drawing | G5-BOM-001 | 白名單尺寸與 IR 一致；水印；QA checklist 寫入 manifest | E4 |
| ◆ G5-REP-001 | Clean-environment reproducibility test | G5-DRW-001 | 乾淨環境與 CI 重建 fingerprint 一致或差異已 ADR | E3 |
| G5-REV-001 | G5 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G5-ACC-001 | G5 acceptance 決策紀錄 | G5-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.9 G6 — 引導式介面與 AI 輔助

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G6-UI-001 | 建立 capability-driven guided flow | G5-ACC-001 | 以 adapter 替換 `PrototypeViewModel`；只呈現已證明能力；UI 與 API 產生等價 IR | E3 |
| ◆ G6-QST-001 | 建立 question ordering / abstention | G6-UI-001 | deterministic 排序 golden；unsafe unknown 阻擋生成 | E3 |
| G6-AI-001 | AI provider adapter 與離線 fallback | G6-QST-001 | 預設關閉；故障退回表單；成本與速率上限 | E3 |
| G6-AI-002 | Intent → Requirement 萃取 | G6-AI-001 | schema-bound；`llm_proposed`；evidence span；未確認值不入 IR | E3 |
| G6-AI-003 | AI 評估語料與 KPI | G6-AI-002 | ≥ 50 intents；§18.3 KPI；unsafe hallucination = 0；injection resistance = 100% | E3 |
| G6-AI-004 | AI grounded explanation | G6-AI-002 | 解釋數值 100% 可追溯 | E3 |
| G6-A11Y-001 | 無障礙驗證 | G6-UI-001 | WCAG 2.2 AA 自動化 ＋ 人工抽查 | E3 |
| G6-USE-001 | Usability test | G6-AI-004, G6-A11Y-001 | ≥ 5 位非 CAD 參與者；與 UX-0 基線比較 | E4 |
| ◆ G6-E2E-001 | UI-to-IR-to-package end-to-end test | G6-USE-001 | AI 開／關兩模式；失敗狀態不遺失；越界輸入被阻擋 | E3 |
| G6-REV-001 | G6 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G6-ACC-001 | G6 acceptance 決策紀錄 | G6-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.10 G7 — 聲學薄切片

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G7-ACO-001 | Acoustic graph / sealed-volume thin slice | G6-ACC-001 | 共用 core contracts；sealed volume 閉合；leak assumptions 明示 | E3 |
| G7-SOL-001 | Solver level 分級報告 | G7-ACO-001 | L0 必達；L1 需量測比對；結果標示 level 與限制 | E3 |
| G7-REV-001 | G7 自我審查（全新 session） | 以上全部 | 自我審查 passed | E3 |
| G7-ACC-001 | G7 acceptance 決策紀錄 | G7-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.11 G8 — 機器人薄切片

| ID | 標題 | 依賴 | 驗收摘要 | 證據等級 |
|---|---|---|---|---|
| ◆ G8-ROB-001 | Robot layout / assembly-relationship thin slice | G6-ACC-001 | 共用 contracts；collision／clearance／mounting zone；maturity ≤ CONCEPT；電池安全 assumption 不可 waive | E3 |
| G8-REV-001 | G8 自我審查（全新 session） | G8-ROB-001 | 自我審查 passed | E3 |
| G8-ACC-001 | G8 acceptance 決策紀錄 | G8-REV-001 | `gate_acceptance` 決策紀錄；使用者可否決 | E4 |

## 26.12 G9 — 強化與擴充（範本）

每個擴充 slice 使用以下 work item 組：

```text
G9-<SLICE>-ENV-001   envelope 變更與 sign-off
G9-<SLICE>-GLD-001   golden / boundary / negative corpus
G9-<SLICE>-CAP-001   capability 程式實作
G9-<SLICE>-RUL-001   規則與來源
G9-<SLICE>-UI-001    UI capability filtering
G9-<SLICE>-AI-001    AI 評估語料擴充
G9-<SLICE>-REV-001   自我審查（全新 session）
G9-<SLICE>-ACC-001   Gate 決策紀錄（使用者可否決）
```

## 26.13 驗證腳本必要 ID

`scripts/verify-control-plane.mjs`（或等效工具）的必要 ID 清單必須包含 §26.3–§26.11 全部 ID；導入既有 repository 期間另包含 §26.1 全部 V3C ID。

---

# 27. Agent 指令範本

## 27.1 施工者：繼續施工

```text
請依 MEGIS v3.0-claude-code 藍圖繼續施工，你的角色是 Builder。

先讀 AGENTS.md、execution/PROJECT_STATE.md、execution/WORK_QUEUE.yaml、
execution/BLOCKERS.yaml、execution/AGENT_CLAIM.json、最近 handoff 與 execution/reviews/；
檢查 Git 與現有測試。

確認沒有其他 Agent 持有有效 claim 後寫入 claim。
依 §5.4 選擇依賴已滿足的最高優先 ready work item；先跑 baseline，
再完成實作、驗證、狀態更新與 commit；完成後以全新 session 依 §5.7 自我審查；
最後釋放 claim 並寫 handoff。
只在 §5.6 停止條件成立時停止並詢問。
所有新增文件、報告、ADR、handoff 與說明使用繁體中文。
```

## 27.2 施工者：導入 v3.0（既有 repository）

```text
使用者已核准 MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md。

請先完成並 commit 目前 in_progress 的 work item，不得混入 v3 範圍。
然後依 v3 §0.6 與 §26.1 執行 V3C lane，從 V3C-BCR-001 開始：
- 已 done 的 work item 與已 accepted 的 Gate 不得重開或修改其歷史紀錄。
- V3C 項目掛在當前 active Gate 下。
- 不改寫 Git history；既有大型製品以 ADR 白名單處理。
- D6（誰施工誰自我審查）與 D8（施工者上網研究 PCB／USB-C 方案）已由我決定，直接記錄於 ADR；其餘決策若需要我回答，請一次整理成問題清單。
- 所有新增或修改的文件、報告、ADR、handoff 一律使用繁體中文。
```

## 27.3 自我審查：工作項目

```text
你剛完成 <WORK_ITEM> 的施工。依 v3.0-claude-code 藍圖 §5.7（D6：誰施工誰審查），
現在以全新 session、乾淨 checkout 自我審查 <WORK_ITEM> 於 commit <SHA>：
1. 在隔離暫存目錄重跑 verificationCommands，記錄輸出。
2. 逐條對照 acceptance，檢查證據等級是否達到要求。
3. 檢查 manifest classification／maturity、fingerprint 重跑一致性、artifact 大小預算、
   狀態檔與 Git 一致、有無未登記 assumption／risk／錯誤碼。
4. 至少嘗試一個 negative 或 boundary 輸入。
不得修改程式、schema、golden 或狀態檔。
輸出 execution/reviews/<WORK_ITEM>-<shortsha>.md（附錄 A.3 格式），
結論為 passed 或 changes_requested。報告使用繁體中文。
```

## 27.4 自我審查：Gate

```text
你是負責 Gate <Gx> 施工的 Agent。依 v3.0-claude-code §6.3，以全新 session、乾淨 checkout 對 commit <SHA> 進行 Gate 自我審查。
逐項列出 exit criteria → 證據路徑 → 證據等級 → 重跑結果 → 判定。
執行 holdout corpus（若適用），抽查 negative 與 boundary cases，
確認不變量強制機制仍有效。
未通過項目不得判定 passed。確認 CI 對同一 commit 全綠。輸出 execution/reviews/<Gx>-GATE-<shortsha>.md（繁體中文）。
```

## 27.5 任一 Agent：狀態不一致時恢復

```text
請比對 execution/ 狀態檔與 Git history、實際測試結果。
以 Git history 與重跑結果為準，列出所有不一致項目、原因推測與修正方案；
施工 session 可修正狀態檔並以 `chore: reconcile control plane` commit，
審查 session 只輸出報告。不得為了一致而把未驗證項目標為 done。
```

## 27.6 施工者：使用者決策請求

```text
請把目前需要我決定的事項整理成決策包：每項包含背景、選項、建議、
若不決定的預設與影響的 work item。一次列出全部，不要逐項分次詢問。
```

---

# 28. 風險登錄表

欄位：機率與影響以 L／M／H（低／中／高）表示；負責角色見表。每項風險於 `docs/RISKS.md` 另記目前狀態與下次審查時機（每個 Gate review 必審）。

| ID | 風險 | 機率 | 影響 | 負責角色 | 觸發條件 | 應變措施 |
|---|---|---|---|---|---|---|
| R-CAD-001 | CAD boolean／fillet 不穩定 | M | H | 施工 Agent | golden case 間歇失敗 | 縮小參數 envelope、固定 feature ordering、保留可診斷中間 shape |
| R-DRW-001 | FreeCAD headless 圖面不穩定 | H | M | 施工 Agent | CI 無法重現 PDF | 固定版本；降為 SVG/PDF template + manual QA |
| R-SIM-001 | COMSOL 授權或 worker 不可用 | H | L | 使用者 | feasibility spike 失敗 | Acoustic 停在 L0/L1；核心工程繼續 |
| R-RUL-001 | 規則品質不足 | M | H | 施工 Agent | precision／recall 不合格 | 減少規則範圍、補上網查證來源與 test vectors |
| R-DNA-001 | Product DNA 過度抽象 | M | M | 施工 Agent | 三案例需要大量例外 | 收斂 core vocabulary；以 extension SDK 處理 domain-specific capability |
| R-PM-001 | Schedule illusion | M | M | 施工 Agent（審查 session） | 大量工作同時 in progress | WIP limit = 1；以 Gate evidence 而非百分比報進度 |
| R-AI-001 | AI hallucination | H | H | 施工 Agent | unknown 被填入無來源值 | schema 強制 provenance／`llm_proposed`／evidence span；AI KPI |
| R-DET-001 | Artifact 不可重建 | M | H | 施工 Agent | replay fingerprint 不一致 | pin versions、header 正規化、保存 manifest、禁止成熟度升級 |
| R-SAFE-001 | 安全宣稱過度 | L | H | 使用者 | 未簽核 artifact 被稱為 released | maturity evaluator、強制水印、safety_category 上限 |
| R-DET-002 | ARM64 emulation 與 x64 CI 浮點差異 | M | M | 施工 Agent | 本機綠 CI 紅（或相反） | fingerprint 捨入；informational 欄位 ADR |
| R-AGT-001 | 多 Agent 狀態漂移或衝突 | M | H | 施工 Agent | 兩個 claim、狀態檔衝突 | 單一施工寫入鎖；審查 session 唯讀；reconcile 指令 |
| R-AGT-002 | 自我審查偏差（D6 無獨立審查者） | H | H | 施工 Agent | Gate accepted 但後續重跑、CI 或使用者檢查失敗 | 全新 session 乾淨重跑；CI 外部證據；holdout 先封存後施工；使用者否決權；可隨時指派另一 Agent 抽查 |
| R-AGT-003 | 驗收範圍被悄悄縮窄 | M | H | 施工 Agent（審查 session） | acceptance 文字或測試被修改 | §6.4 規則；verifier 比對必要 ID；review 檢查 diff |
| R-GIT-001 | Repository 因二進位製品膨脹 | H | M | 施工 Agent | Git 追蹤大檔增加 | §5.9 預算與 verifier |
| R-LEG-001 | 標準原文或客戶資料入庫 | M | H | 施工 Agent | 原文或客戶 CAD 被提交 | §19.2；D5；secret／大檔掃描；review 檢查 |
| R-PLT-001 | CadQuery/OCP 無 ARM64 wheel 長期不改善 | M | M | 維運者 | emulation 失效或效能不足 | 保留 x64 CI 重建路徑；評估 Linux x64 container |
| R-SPEC-001 | 參考案例研究值缺乏可靠依據（D8） | M | H | 施工 Agent | 研究值無來源、來源無法開啟或互相矛盾 | §9.1 研究規範；每值附 URL／取用日期；verifier 檢查 researched 值必有來源 |
| R-SME-001 | 無具名工程師審查（D6 已接受） | H | M | 使用者 | 需要 `ENGINEERING_REVIEWED` 或安全相關判斷 | 成熟度上限 PROTOTYPE；輸出標示「未經具名工程師審查」；需要時再指定工程師 |
| R-UX-001 | 新人仍無法理解假設與限制 | M | M | 施工 Agent | usability 完成率低 | 簡化問題、視覺化、UX-0 基線比較後迭代 |
| R-SUP-001 | 相依套件遭竄改或破壞性升級 | L | H | 施工 Agent | 安裝 hash 不符或 fingerprint 改變 | hash-pinned lock；升級流程 §22.4 |
| R-AI-002 | Prompt injection 影響流程 | M | M | 施工 Agent | injection 語料失敗 | 資料隔離；AI 無寫入權；拒收 |
| R-OPS-001 | 本機資料遺失 | L | M | 維運者 | 磁碟故障或誤刪 | OPERATIONS 備份還原程序；Git 遠端同步狀態檔 |

---

# 29. 審查意見處置與追溯

## 29.1 v1.0 → v2.0（沿用）

| 審查問題 | v2.0 處置 |
|---|---|
| 90 天與三案例範圍不可成立 | 移除日曆；Fixture full slice，Acoustic／Robot thin slices |
| UI 排在工程能力之前 | UI 移至 G6，依賴 G1–G5 |
| Validation 與 RELEASED 矛盾 | 導入 maturity states；自動化上限為 PROTOTYPE |
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

## 29.2 v2.0 → v3.0

| # | v2.0 缺口 | 為何重要 | v3.0 處置 | 章節 |
|---|---|---|---|---|
| V1 | 「相同輸入 → 相同 hash」在 STEP/DXF 含時間戳時不可能成立（實測兩次重跑 byte hash 不同） | 不變量 5 與 G5 exit criteria 永遠無法誠實通過 | 雙層指紋；header 正規化 | §4.12 |
| V2 | 成熟度可被任意腳本寫入，spike 可能被標 PROTOTYPE | 誤導使用者，違反 maturity 精神 | Classification；evaluator 唯一寫入；manifest 掃描 | §1.4、§1.5、§3.1 #11 |
| V3 | G0 決策（部署、LLM、資料政策）無對應 work item | Gate 可能在決策未定時被判定完成 | G0-DEC-001、決策清單 D1–D9 | §8.1 |
| V4 | 控制面文件清單無「非空殼」要求與 verifier 檢查 | 文件缺漏不會被發現 | 非空殼定義；verifier 檢查 | §5.1、§5.13 |
| V5 | 產品名為 Generative Intelligence，但 G0–G9 無 AI work item 與 AI KPI | AI 會在無規格、無評估下被臨時加入 | AI 施工線、AI governance、AI KPI | §14.1、§18.3、§20 |
| V6 | 無多 Agent 協作與審查隔離機制 | 狀態衝突；審查沿用施工上下文容易自我確認 | 寫入鎖；D6 誰施工誰審查，但須全新 session 與乾淨 checkout；CI 外部證據；E3/E4 | §5.7、§5.12、§6.3 |
| V7 | Reference Case 僅 8 個欄位，缺 PCB 尺寸、USB-C 位置、螺紋、公差、boss | 無法形成可驗證 golden case；2 mm 壁無法直接攻 M3 | 完整參數表與核准流程 | §1.3、附錄 B |
| V8 | 無 artifact 儲存政策 | Git 膨脹、跨平台 checkout 改變 bytes | 儲存政策、`.gitattributes`、預算 | §5.8、§5.9 |
| V9 | 不變量缺強制機制 | 不變量流於口號 | 每條不變量對應強制機制與生效 Gate | §3.1 |
| V10 | 缺 error taxonomy | 「結構化 failure」無統一定義 | `MEGIS-<DOMAIN>-<NNN>` 與錯誤物件 | §4.10 |
| V11 | IR `schema_version: 2.0.0` 與藍圖版本混淆 | 版本語意錯亂 | Schema SemVer 獨立；G1 凍結 1.0.0 | §4.3、§4.8 |
| V12 | Maturity 狀態無精確進入條件 | Evaluator 無法實作與測試 | 必要且充分條件表 | §1.4 |
| V13 | 規則來源僅寫 `internal_me_standard` | 無法追溯；標準著作權風險 | 來源登錄表、生命週期、Agent 不得自行核准 | §11.1、§19 |
| V14 | Job state 無合法轉移表 | 狀態機實作不一致 | 轉移表與 idempotency key 定義 | §4.11 |
| V15 | Work item 無狀態轉移、WIP 選擇規則、Definition of Ready | 選擇與狀態更新依賴個別判斷 | 轉移表、選擇順序、DoR | §5.3、§5.4、§25.1 |
| V16 | 無 relationship vocabulary 語意 | Constraint Graph 可被任意擴張 | 封閉 vocabulary 與必要驗證 | §4.16 |
| V17 | 無測試紀律（flaky、skip、golden 更新、coverage 下限） | CI 綠燈可信度不足 | 測試紀律 | §18.5 |
| V18 | 無威脅模型與供應鏈政策 | 本機也有惡意檔、秘密外洩、依賴竄改風險 | 威脅模型、供應鏈政策、本機基線 | §22 |
| V19 | UX-0 未被藍圖承認 | 藍圖與實際施工脫節，可能被誤當 G6 | UX-0 章節與邊界 | §7 |
| V20 | 無資料保留與 IP 政策 | 資料外送與保存無規範 | 資料管理表 | §24.3 |
| V21 | Acoustic L1 無驗證要求 | 未驗證模型可能被當成可信結果 | L1 必須量測比對 | §15 |
| V22 | Gate 失敗時的合法處置未定義 | 可能以修改驗收文字方式通過 | §6.4 失敗與範圍縮窄規則 | §6.4 |
| V23 | Usability、無障礙無量化最低要求 | G6 驗收主觀 | ≥ 5 人、WCAG 2.2 AA | §14 |
| V24 | 藍圖變更無流程 | 藍圖版本與施工脫節 | BCR 與 V3C lane | §0.6、§5.10、§26.1 |

## 29.3 v3.0 刻意未改變的 v2.0 決策

- 第一條 vertical slice 仍為 CNC Fixture／Electronics Enclosure。
- 自動化成熟度上限仍為 PROTOTYPE。
- 單一 CadQuery／OCC backend。
- 不使用日曆排程。
- Gate 順序 G0 → G9 不變。
- 規則採少量高價值策略。
- 不顯示未校準信心百分比。

---

# 30. 最終成功定義

第一個重大成功不是「支援 100 種產品」，而是：

> 一名不懂 CAD 的使用者，可以在明確的 supported envelope 內，透過 Guided UI 建立 CNC Fixture／Enclosure；系統能產生可重新開啟的 CAD、可追溯的規則結果、BOM、draft drawing 與完整 manifest，而且相同輸入可以由另一個 Agent session 重新建構並得到一致結果。

【v3】精確化：上述「一致結果」指 semantic fingerprint 一致；此成功必須以全新 session 在乾淨環境重跑、CI 同步確認（E3），並有決策紀錄（E4）且使用者未否決；AI 關閉時同樣成立。

第二個重大成功是：

> Acoustic 與 Robot thin slices 確實重用核心 IR、Module、Graph、Validation Result 與 Manifest，而不是各自長出一套硬編碼 Wizard。

【v3】精確化：G7／G8 未新增任何專屬 IR 頂層欄位，或新增者均經 BCR 核准。

第三個重大成功才是：

> 在工程師審核、規則治理、solver fidelity 與安全 Gate 成熟後，逐步把 `PROTOTYPE` 能力提升到 `ENGINEERING_REVIEWED`，再由組織流程決定是否 `RELEASED`。

【v3】第零個成功（任何重大成功的前提）：

> 整個施工歷程中，沒有任何一個 Gate、work item 或 Design Run 在證據不足時被標示為完成或升級成熟度。

---

# 附錄 A. 範本

## A.1 工作項目（`WORK_QUEUE.yaml` 內，JSON 格式）

```json
{
  "id": "G2-CAD-002",
  "title": "產生 fixture base",
  "gate": "G2",
  "status": "planned",
  "dependsOn": ["G2-CAD-001"],
  "inputs": ["tests/golden/reference_fixture/ir.json"],
  "outputs": ["megis/geometry/generators/base.py", "tests/geometry/test_base.py"],
  "acceptance": [
    "base kernel-valid 且為單一 solid",
    "外尺寸在 engineering_tol 內",
    "所有 semantic feature ID 可由幾何謂詞重新定位",
    "semantic fingerprint 與 golden 一致"
  ],
  "acceptanceResults": [],
  "verificationCommands": [".venv/Scripts/python.exe -m pytest tests/geometry/test_base.py"],
  "rollbackBoundary": "commit",
  "blockedBy": [],
  "evidence": [],
  "verification": "not_run",
  "commitSha": null,
  "owner_role": "builder",
  "requires_user_decision": false,
  "evidence_level_required": "E3",
  "review": { "required": true, "status": "not_required", "report": null },
  "risk_refs": ["R-CAD-001"],
  "blueprint_ref": "v3.0 §10"
}
```

## A.2 交接紀錄（`execution/handoffs/<timestamp>-<item>.md`）

```markdown
# Handoff — <WORK_ITEM> — <ISO timestamp>

- Agent／角色：
- Session ID：
- 起始 commit：
- 最後綠色 fixed point：
- 寫入鎖狀態：已釋放 | 持有中（原因）

## 已完成
## 未完成（含未提交變更與 patch 位置）
## 驗證結果（命令 → 結果）
## 發現的風險 / 假設 / 錯誤碼
## 下一步（具體到命令或檔案）
## 需要使用者決定的事項
```

## A.3 審查報告（`execution/reviews/<ID>-<shortsha>.md`）

```markdown
# 審查報告 — <WORK_ITEM 或 GATE> @ <SHA>

- 審查 Agent／審查 session ID：
- 施工 Agent／施工 session ID（D6：Agent 可相同，session 必須不同）：
- 乾淨 checkout 方式與路徑：
- 審查時間：
- 環境（作業系統／架構／是否模擬／工具鏈版本）：
- CI run ID 與結果：
- 結論：passed | changes_requested

## 驗收條件對照
| # | 條件 | 證據 | 等級 | 重跑結果 | 判定 |
|---|---|---|---|---|---|

## 重跑紀錄
## 額外嘗試（negative / boundary / holdout）
## 發現
| ID | 嚴重度 | 檔案 | 重現步驟 | 影響的條件 |
|---|---|---|---|---|

## 狀態檔與 Git 一致性
## 未登記的風險／假設
```

## A.4 決策紀錄 ADR（`docs/decisions/ADR-<NNNN>-<slug>.md`）

```markdown
# ADR-<NNNN>: <title>

- 狀態：proposed | accepted | superseded by ADR-<NNNN>
- 日期：
- 決策者：
- 相關工作項目：

## 背景
## 決策
## 考慮過的替代方案
## 後果
## 證據
```

## A.5 決策／簽核紀錄（`execution/signoffs/SO-<NNNN>.yaml`）

```yaml
signoff_id: SO-0001
type: gate_acceptance   # gate_acceptance | engineering_review | envelope_change | rule_source_check | blueprint_change | decision
subject: G2
reviewer_name: <審查者身分；D6 下為施工 Agent，例如 codex 或 claude-code>
reviewer_role: self_review   # self_review | user | named_engineer（engineering_review 類型必須為 named_engineer）
review_session_id: <審查 session ID，必須不同於施工 session>
build_session_id: <施工 session ID>
scope: <審查範圍>
evidence:
  - path: execution/reviews/G2-GATE-abc1234.md
  - artifact: tests/golden/reference_fixture/expected_fingerprint.json
    semantic_fingerprint: <sha256>
decision: approved       # approved | rejected | approved_with_conditions
conditions: []
signed_at: <ISO timestamp>
signature_reference: <commit SHA 或外部簽核單號>
recorded_by: <agent | user>
user_veto: null   # 使用者否決時填入日期與理由
```

## A.6 規則豁免 Waiver（`execution/signoffs/WV-<NNNN>.yaml`）

```yaml
waiver_id: WV-0001
rule_id: CNC_DEPTH_RATIO_001
rule_version: 1.0.0
design_id: PROJECT-0001
revision: A
entity_refs: [base.pocket.main]
reason: <理由>
risk_accepted: <接受的風險描述>
owner: <具名>
approved_by_signoff: SO-0007
expires_when:
  - input_changed
  - rule_version_changed
  - date: 2026-12-31
affected_artifacts: [CAD/base.step]
revalidation_required: true
```

## A.7 規則

見 §11.1。

## A.8 清單（Manifest）骨架

```json
{
  "manifest_schema_version": "1.0.0",
  "package_kind": "PROTOTYPE_PACKAGE",
  "classification": "DESIGN_RUN",
  "design_id": "PROJECT-0001",
  "revision": "A",
  "maturity": "PROTOTYPE",
  "maturity_evaluation": { "evaluator_version": "", "inputs_digest": "", "blocking_reasons": [] },
  "inputs": [{ "path": "requirement.yaml", "byte_sha256": "", "semantic_fingerprint": "" }],
  "artifacts": [{ "path": "CAD/base.step", "byte_sha256": "", "semantic_fingerprint": "", "fingerprint_policy_version": "1.0.0" }],
  "versions": { "megis": "", "ir_schema": "", "rules": {}, "modules": {}, "cadquery": "", "ocp": "", "freecad": "" },
  "runtime": { "os": "", "machine": "", "emulated": false, "python": "" },
  "seed": 0,
  "envelope_ref": "",
  "dna_ref": "",
  "validations": { "executed": [], "passed": [], "failed": [], "waived": [], "skipped": [] },
  "assumptions": [],
  "unknowns": [],
  "signoffs": [],
  "ai_involvement": { "used": false, "provider": null, "model": null, "prompt_version": null, "llm_proposed_fields": [] },
  "drawing_qa": { "checklist_version": "", "results": [] },
  "limitations": [],
  "generated_at": "<excluded from fingerprint>"
}
```

## A.9 Agent 寫入鎖（`execution/AGENT_CLAIM.json`）

```json
{
  "agent": "codex",
  "role": "builder",
  "work_item": "G2-CAD-002",
  "claimed_at": "2026-09-17T09:00:00+08:00",
  "expires_at": "2026-09-17T13:00:00+08:00",
  "base_commit": "<sha>"
}
```

無人持有時內容為 `{ "agent": null }`。

## A.10 阻塞紀錄（`execution/BLOCKERS.yaml` 內，JSON 格式）

```json
{
  "id": "BLK-0001",
  "work_item": "G1-REQ-001",
  "title": "PCB 尺寸未提供",
  "type": "user_decision | external_dependency | defect | license | signoff",
  "owner": "user",
  "opened_at": "",
  "unblock_condition": "使用者提供 PCB-A/B 外形與堆疊方式",
  "fallback": "無；golden case 不得以臆測值完成",
  "status": "open | resolved"
}
```

---

# 附錄 B. 參考案例參數檔（機器可讀草案）

路徑建議：`tests/golden/reference_fixture/requirement.yaml`。以下所有 `defaulted` 值在 G1-REQ-001 完成前 `approved_by: null`；`unknown` 值由施工者依 §9.1 上網研究後改為 `state: researched` 並附 `sources`；`proposed` 只是研究起點，不得未經查證直接使用。

```yaml
schema_version: 0.1.0
design_id: REF-FIXTURE-0001
revision: A
dna_ref: dna.cnc_enclosure@1.0.0
units: { length: mm, angle: deg, mass: g }

envelope:
  outer_size:
    length: { nominal: 120.0, unit: mm, provenance: { source: user } }
    width:  { nominal: 80.0,  unit: mm, provenance: { source: user } }
    height: { nominal: 35.0,  unit: mm, provenance: { source: user } }
  split:
    base_height:     { nominal: 29.0, unit: mm, provenance: { source: defaulted, approved_by: null } }
    cover_thickness: { nominal: 6.0,  unit: mm, provenance: { source: defaulted, approved_by: null } }
  outer_vertical_edge_radius: { nominal: 3.0, unit: mm, provenance: { source: defaulted, approved_by: null } }

material:
  designation: AL6061
  temper: { value: T6, provenance: { source: defaulted, approved_by: null } }
  provenance: { source: user }

manufacturing:
  process: cnc_3axis
  provenance: { source: user }
  max_setups: { nominal: 2, unit: "1", provenance: { source: defaulted, approved_by: null } }
  tooling_assumptions:
    min_end_mill_diameter: { nominal: 6.0, unit: mm, provenance: { source: defaulted, approved_by: null } }
    internal_radius_margin: { nominal: 0.2, unit: mm, provenance: { source: defaulted, approved_by: null } }
  general_tolerance: { class: ISO2768-mK, provenance: { source: defaulted, approved_by: null } }

walls:
  side_min:  { nominal: 2.0, unit: mm, provenance: { source: user } }
  floor:     { nominal: 2.0, unit: mm, provenance: { source: defaulted, approved_by: null } }
  cover_min: { nominal: 2.0, unit: mm, provenance: { source: defaulted, approved_by: null } }

pcbs:
  # 研究完成後格式範例（D8）：
  # outline: { length: <值>, width: <值>, thickness: <值>, unit: mm,
  #            provenance: { source: researched,
  #                          sources: [{ url: <URL>, title: <文件標題>, revision: <版次/料號>, accessed: <YYYY-MM-DD> }],
  #                          rationale: <選擇理由，對應 ADR> } }
  - id: cmp.pcb_a
    outline: { state: unknown, criticality: critical, unsafe_to_default: true,
               proposed: { length: 100.0, width: 60.0, thickness: 1.6, unit: mm } }
    component_height_top:    { state: unknown, criticality: critical, unsafe_to_default: true, proposed: { value: 12.0, unit: mm } }
    component_height_bottom: { state: unknown, criticality: critical, unsafe_to_default: true, proposed: { value: 2.0, unit: mm } }
    mounting_holes: { state: unknown, criticality: critical, unsafe_to_default: true }
  - id: cmp.pcb_b
    outline: { state: unknown, criticality: critical, unsafe_to_default: true,
               proposed: { length: 60.0, width: 40.0, thickness: 1.6, unit: mm } }
    component_height_top:    { state: unknown, criticality: critical, unsafe_to_default: true, proposed: { value: 12.0, unit: mm } }
    component_height_bottom: { state: unknown, criticality: critical, unsafe_to_default: true, proposed: { value: 2.0, unit: mm } }
    mounting_holes: { state: unknown, criticality: critical, unsafe_to_default: true }
  arrangement: { state: unknown, criticality: critical, unsafe_to_default: true,
                 options: [side_by_side, stacked], proposed: stacked }
  edge_to_wall_clearance: { nominal: 1.0, unit: mm, provenance: { source: defaulted, approved_by: null } }
  top_to_cover_clearance: { nominal: 1.0, unit: mm, provenance: { source: defaulted, approved_by: null } }

connectors:
  - id: cmp.usbc_1
    type: usb_type_c_receptacle
    host_pcb: { state: unknown, criticality: critical, unsafe_to_default: true, proposed: cmp.pcb_a }
    wall_face: { state: unknown, criticality: critical, unsafe_to_default: true, proposed: minus_x }
    part_number: { state: unknown, criticality: critical, unsafe_to_default: true }
    recess_from_outer_wall: { state: unknown, criticality: major, unsafe_to_default: true }
    opening_rule: CON_USBC_OPEN_001

fasteners:
  cover_screws:
    standard: ISO4762
    size: M3
    length: { nominal: 8.0, unit: mm, provenance: { source: defaulted, approved_by: null } }
    quantity: { nominal: 4, unit: "1", provenance: { source: defaulted, approved_by: null } }
    cover_clearance_hole: { nominal: 3.4, unit: mm, standard_ref: SRC-ISO-273, fit: medium,
                            provenance: { source: defaulted, approved_by: null } }
    counterbore: { diameter: 6.5, depth: 3.3, unit: mm, provenance: { source: defaulted, approved_by: null } }
  base_thread:
    method: { value: direct_tap, options: [direct_tap, thread_insert], provenance: { source: defaulted, approved_by: null } }
    thread: M3x0.5
    tap_drill: { nominal: 2.5, unit: mm, provenance: { source: derived } }
    min_engagement: { nominal: 6.0, unit: mm, note: "2.0 D for aluminum", provenance: { source: defaulted, approved_by: null } }
  corner_boss:
    diameter: { nominal: 7.0, unit: mm, provenance: { source: defaulted, approved_by: null } }
    min_wall_around_thread: { nominal: 1.5, unit: mm, provenance: { source: defaulted, approved_by: null } }

assembly:
  insertion_direction: +z
  cover_removal_direction: +z
  moving_parts: false
  provenance: { source: user }

outputs:
  - CAD/assembly.step
  - CAD/base.step
  - CAD/cover.step
  - CAD/preview.glb
  - CAD/base.stl
  - Drawing/reference_fixture_draft.pdf
  - Drawing/section_z10.dxf
  - BOM/bom.csv
  - Reports/dfm_report.md
  - Reports/verification_report.md
  - release_manifest.json

safety_category: none
maturity_cap: PROTOTYPE
```

---

# 附錄 C. 版本紀錄

## v3.0-claude-code — 2026-09-17

- 以 v2.0 為基礎全面擴充；v2.0 全部決策、Gate、30 個 work item ID、不變量與限制完整保留。
- 新增規範用語、文件優先順序、名詞定義與既有 repository 導入規則（V3C lane）。
- 新增使用者角色、Reference Case 完整參數檔、maturity 必要且充分條件、classification、anti-goals。
- Envelope 機器可讀化與變更程序。
- 不變量擴充為 18 條並逐條指定強制機制。
- Architecture：分層與依賴方向、entity 最小欄位、ID 規則、數量／公差模型、座標框架、knowledge state、schema 版本政策、error taxonomy、job 轉移表、雙層指紋、容差政策、topological naming、技術基線、Product DNA／Module／relationship vocabulary。
- 控制面：非空殼要求、work item 狀態轉移、WIP 選擇順序、雙 Agent 協定、Git 政策、artifact 政策、BCR、ADR、證據等級 E0–E4、verifier 檢查清單。
- Gate：通用結構、review 程序、失敗與範圍縮窄規則；新增 UX-0 章節；每個 Gate 增加 entry criteria、量化 exit criteria、審查與簽核項目。
- 新增 AI 施工線（G6-AI-001～004）、AI governance、AI KPI。
- 新增 engineering knowledge governance、威脅模型、供應鏈政策、UX principles、資料管理、Definition of Ready。
- 完整 Work Queue（不含施工狀態）、Agent 指令範本、擴充風險登錄表、v2 → v3 追溯表（24 項）。
- 附錄：work item、handoff、review、ADR、sign-off、waiver、manifest、claim、blocker 範本與 Reference Case 參數檔。
- 使用者決策 D6：不設具名工程審查人，誰施工誰自我審查；以全新 session、乾淨 checkout、CI 外部證據與使用者否決權降低偏誤；`ENGINEERING_REVIEWED`／`RELEASED` 在指定具名工程師前不可達。
- 使用者決策 D8：參考案例未知值由施工者上網研究決定；新增 `researched` 來源類型與 §9.1 研究規範。
- 全文標題、表頭與範本改為繁體中文（技術名詞、ID、程式碼保留英文）。

## v2.0 — 2026-09-16

- 保留 v1.0 願景，另建可執行版本。
- 移除 90 天與週次排程。
- 改為 Codex 可持續、可中斷恢復的 Gate DAG。
- 將 Fixture 設為完整 vertical slice；Acoustic、Robot 設為後續 thin slices。
- 新增 supported envelope、maturity states、schema contract、規則治理、benchmark、reproducibility、安全、部署、fallback 與 Definition of Done。
- 納入獨立反方審查的 blocking／high-severity findings。
