# G6-AI-002 Intent 到 Requirement 萃取

> 文件治理
> - 目的：說明 AI Requirement 草稿 schema、evidence span 與使用者確認隔離。
> - 目前內容：recorded provider output、拒收條件、confirmation ledger 與 IR promotion 邊界。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G6-AI-002 實作 commit。

## 三層資料邊界

```text
使用者原始 intent
→ provider output（不可信 JSON 字串）
→ schema-bound Requirement draft（全部 llm_proposed）
→ 使用者逐欄確認的 confirmation ledger
→ confirmed Engineering IR
```

provider output 永遠不是 Engineering IR。`parse_requirement_draft` 不修補 JSON、不猜單位、不補 evidence；任何 schema、hash、span、型別、單位或重複欄位錯誤一律以 `MEGIS-AI-002` 拒收。

## Evidence span

每個 proposal 都必須包含 `start`、`end` 與 `quote`，且 `source_text[start:end]` 必須與 quote 完全相等。數值欄位還必須在 quote 中找到相同數字；外形尺寸只能使用 `mm`，而且原文 span 必須明確含 `mm`。因此「模型推測 120 mm、原文沒有數字」無法通過 quarantine。

## 確認隔離

`confirm_requirement_fields` 只輸出使用者明確列入 `confirmed_fields` 的值，其他 proposal 留在 `unconfirmedFields`。`build_ir_with_confirmed_proposals` 以既有表單答案為基線，只覆寫已確認欄位；未確認 AI 值不會出現在 Engineering IR。確認後的 provenance 為 `engineer_override`，帶原始 intent SHA-256，不把 `llm_proposed` 狀態寫入 confirmed IR。

## 支援欄位

此階段只接受 G6 已驗證 guided flow 的封閉欄位：外形三軸尺寸、PCB 數量／envelope mode、用途、優先目標、數量級、connector、fastener 與 cover。超出 schema 的欄位被拒收，不以 additional property 暗中保留。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g6_ai_002.py
.\.venv\Scripts\python.exe scripts\verify_g6_ai_002.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

Recorded fixtures 位於 `contracts/g6/golden/ai-requirement-fixtures.json`；E3 證據寫入 `artifacts/g6-ai-002/verification.json`。所有測試只使用本機 recorded data，不呼叫外部 provider。
