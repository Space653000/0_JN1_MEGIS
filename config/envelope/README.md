# Envelope configuration

G1-ENV-001 已建立機器可讀 envelope：`config/envelope/envelope.yaml`（schema `schemas/v3/envelope.schema.json`），並由 `tests/test_g1_env_001.py` 與 `docs/SUPPORTED_ENVELOPE.md` 做人讀／機器讀一致性測試。

- 本目錄的 runtime 讀取入口：`megis/envelope/load_envelope()`；UI、API、geometry 與 maturity evaluator 一律讀同一份機器設定，不得各自硬編碼範圍。
- 超出已驗證 envelope 的輸入必須回傳 `MEGIS-ENV-001` 結構化錯誤或標示 `unsupported`，不得 silent clamp。
- Envelope 擴張仍需 ADR、`envelope_change` sign-off、golden／boundary／negative regression、UI capability filter 與 maturity 重算（blueprint §2.4）。
