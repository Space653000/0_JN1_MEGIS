# Maturity Evaluator（G3-MAT-001）

> 文件治理
> - 目的：描述 `megis/maturity` evaluator 如何實作藍圖 §1.4 成熟度表格與 §11.5 唯一寫入者要求。
> - 目前內容：狀態表、必要且充分條件、D6／禁止類別上限、重算規則與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：G3-MAT-001 實作 commit（完工報告列出 SHA）

## 目的

MEGIS v3 將「製品分類」與「工程成熟度」分開治理。`megis.maturity` evaluator 是 Design Run `maturity` 欄位的唯一寫入者：任何 manifest 要宣稱成熟度，都必須附上 evaluator 產出的 `maturity_evaluation`（含 64 位輸入摘要與 blocking reasons），不可由人工或 UI 直接寫值。本文件是 §1.4／§11.5 的機器可讀合約之人的說明。

## 狀態表（藍圖 §1.4）

| 狀態 | 必要且充分條件（全部成立） | blocking 訊息 |
|---|---|---|
| `DRAFT` | Requirement 通過 schema validation | 需求未通過 schema 驗證 |
| `CONCEPT` | DRAFT ＋ IR 通過 schema 與參照完整性 ＋ 無未解決 `unsafe_to_default` ＋ layout／collision 已執行且無 error | IR schema／參照完整性／unsafe_to_default／layout 任一未過 |
| `PROTOTYPE` | CONCEPT ＋ geometry kernel 有效 ＋ 所有適用 rule packs 已執行 ＋ 0 個未處置 error ＋ warning 全 disposition ＋ 無 critical unknown ＋ fingerprint 可重現 ＋ drawing QA 已記錄 ＋ capability 全在 envelope 內 | 任一 gate 未過則停在 CONCEPT |
| `ENGINEERING_REVIEWED` | PROTOTYPE ＋ 具名 Mechanical Engineering Reviewer 的 sign-off 涵蓋所有 artifacts | 缺少具名 sign-off |
| `RELEASED` | ENGINEERING_REVIEWED ＋ 外部組織放行紀錄 reference（只記錄，不執行放行） | 缺少放行紀錄 reference |

## 治理規則

- 唯一寫入者：`MaturityEvaluation` 只能由 `evaluate_design_run` 產生；`megis/governance/classification.py` 只驗證 provenance，不寫 `maturity`。
- 重算（輸入、規則、engine 或 waiver 變更）：`input_changed` 或 `waiver_expired` 觸發重算；既有 `ENGINEERING_REVIEWED` sign-off 失效並回到重新計算結果。
- D6：目前未指定具名工程師，`ENGINEERING_REVIEWED`／`RELEASED` 不可達，上限為 `PROTOTYPE`；輸出須標示「未經具名工程師審查」。
- 禁止類別（§21）：Robot 類別上限 `CONCEPT`，其他禁止類別上限 `PROTOTYPE`；永不自動輸出 `RELEASED`。

## 輸入摘要與確定性

`MaturityInput.digest()` 對所有設計相關欄位（排除 `input_changed`／`waiver_expired` 兩個 meta flag）取 canonical JSON 的 SHA-256。相同輸入必然相同摘要；任何設計參數變更即更換摘要，使下游可稽核 sign-off 是否仍對應同一組輸入。

## 驗證

```powershell
.venv/Scripts/python.exe -m pytest tests/test_g3_mat_001.py
.venv/Scripts/python.exe scripts/verify_g3_mat_001.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

`contracts/g3/golden/maturity-corpus.json` 提供每狀態 positive／negative 以及重算、D6、禁止類別上限的 table-driven 案例；`scripts/verify_g3_mat_001.py` 全數驗證後寫入 `artifacts/g3-mat-001/verification.json`（E3），不產生工程製品。

## Owner

MEGIS Builder；使用者可否決成熟度宣稱與工程師指認決策。
