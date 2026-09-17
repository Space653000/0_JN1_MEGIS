# G1 Schema Migration Contract

> 文件治理
> - 目的：說明 IR migration 與 rollback 契約。
> - 目前內容：v1 到 v2 fixture 遷移、rollback 與版本政策。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 支援路徑

目前唯一明確核准的路徑是 Reference Fixture `1.0.0 → 2.0.0`。呼叫端不可要求猜測式升級、降級或跳版；沒有註冊的來源版本一律回傳 `MigrationError`。

`schemas/v1/engineering-ir.schema.json` 是只供 migration regression 使用的封閉 legacy schema。`contracts/g1/migrations/reference-fixture-v1.json` 是版本化前版 fixture；遷移後必須逐欄等於目前的 `contracts/g1/golden/reference-fixture.json`，且再次通過 V2 Engineering IR 的結構與語意驗證。

## Rollback boundary

每次 migration 產生不可變的 `MigrationReceipt`，記錄來源／目標版本、來源／目標 canonical SHA-256，以及來源文件快照。rollback 前必須確認：

- migrated document 未在 receipt 建立後被修改；
- rollback source 仍符合來源 hash；
- rollback source 仍通過 V1 schema。

任何一項不成立都拒絕 rollback。rollback 回傳前版資料的深拷貝，不會在 V2 Engineering IR 裡偷放 legacy 欄位。

## Semantic version policy

- Major：允許破壞性 schema 變更，但必須新增顯式 migrator、前版 fixture、forward test 與 rollback test。
- Minor：只能新增向後相容且有預設或 optional 語意的能力，仍需 golden regression。
- Patch：只修文件、驗證錯誤或不改變資料語意的實作；不得悄悄改寫 canonical output。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g1_migration.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

此工作項只處理資料契約，不產生 CAD、BOM、圖面或 release package。
