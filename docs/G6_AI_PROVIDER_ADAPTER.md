# G6-AI-001 AI provider adapter 與離線 fallback

> 文件治理
> - 目的：記錄 G6-AI-001 的可替換 AI 邊界、限制與失敗行為。
> - 目前內容：預設關閉設定、provider seam、使用上限、失敗 fallback、稽核與 E3 驗證。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G6-AI-001 實作 commit。

## 決策

MEGIS 的 AI 是可選輔助，不是工程資料來源。Repository 預設設定為 `enabled: false`、`provider: none`，正常的表單、Question Engine、Engineering IR 與 Prototype Package 路徑不依賴 AI。

本工作項只建立 provider-neutral adapter 與 recorded stub。它沒有 API key 欄位、不連線至外部服務，也不授權傳送 CAD、datasheet、檔案內容或客戶識別資料。啟用真實 provider 仍需新的明確決策與資料治理審查。

## 契約

| 項目 | 實作 |
|---|---|
| Feature flag | `config/ai/provider.json` 預設關閉；關閉時 provider 呼叫次數為 0 |
| Provider seam | `AiProvider.invoke(ProviderRequest)`；provider、model、prompt、schema 版本分別記錄 |
| 不可信輸入 | instruction 與 `user_text` 分欄傳遞，資料區指令不得改變系統行為 |
| Timeout | `timeoutMs` 傳入 adapter；timeout 轉成 `MEGIS-AI-001` |
| 呼叫上限 | 每個 `AiOrchestrator` 代表一個 Design Run，累計呼叫數 |
| Token／成本 | 呼叫前檢查 conservative input upper bound；回應後檢查實報 token 與整數 microunit 成本 |
| Fallback | provider 缺失、識別不符、故障、timeout 或超限時，一律回 `form_fallback` |
| Audit | 保存版本、outcome 與輸入 SHA-256；不保存 raw intent、exception 或 secret |
| 工程邊界 | adapter 不建立、不修改 Engineering IR，也不產生工程或 release artifact |

## 錯誤碼

- `MEGIS-AI-001`：provider 不可用、timeout 或故障；可重試，立即退回表單。
- `MEGIS-AI-002`：structured output 不符合 schema；保留給 G6-AI-002，禁止修補後接受。
- `MEGIS-AI-003`：呼叫、token、output 或成本上限超出；停止 AI 並退回表單。

## Manifest 稽核

`ai_involvement` 現在固定包含 `ai_used`、`provider`、`model`、`prompt_versions`、`schema_version` 與 `llm_proposed_fields`。AI 關閉時 provider／model 為 `null`，schema version 為 `none`；後續 AI 施工項必須填入實際版本。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g6_ai_001.py
.\.venv\Scripts\python.exe scripts\verify_g6_ai_001.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

E3 證據寫入 `artifacts/g6-ai-001/verification.json`。CI 僅使用 recorded stub，不呼叫網路服務。
