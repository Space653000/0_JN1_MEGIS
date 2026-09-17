# G1 Engineering IR

> 文件治理
> - 目的：說明 Engineering IR schema 與邊界。
> - 目前內容：v2 IR、語意驗證與 V3 補強缺口。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## 契約內容

`G1-IR-002` 將 V2 藍圖的最小 Engineering IR 固定為 Draft 2020-12 schema：design ID、revision、maturity、unit／coordinate system，以及 requirements、components、interfaces、relationships、materials、manufacturing、constraints、assumptions、unknowns、provenance。

結構驗證與語意驗證分層：

- JSON Schema：required fields、closed objects、列舉、ID shape、measurement shape 與 primitive references。
- MEGIS semantic validator：全域 ID 唯一性、所有 reference 完整性、dimension/unit 相容性、range 與 nominal 邊界。

## 關鍵不變量

- 所有工程數值位於 `measurement.quantity` 並攜帶 unit。
- dimension 與 unit 必須相容，例如 `length/mm`、`force/N`；`length/N` 必須拒絕。
- design 與十種 entity collection 共用單一 ID namespace。
- relationship endpoint、interface participant、constraint target、material／manufacturing／provenance reference 不得懸空。
- `min <= max`，nominal 若有 bounds 必須位於 bounds 內。
- maturity 只允許 `CONCEPT`、`PROTOTYPE`、`ENGINEERING_REVIEWED`、`RELEASED`；此 schema 不會自行升級 maturity。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g1_engineering_ir.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

固定負向測試至少涵蓋 blueprint 指定的 unit mismatch、dangling reference、duplicate ID 與 invalid range，另驗證 provenance dangling reference 及非法 maturity。

## 邊界

本工作項定義契約，不產生 CAD、BOM、圖面或 Release Package。Reference Fixture、Acoustic 與 Robot golden inputs 在 `G1-IR-003` 建立，migration contract 在 `G1-MIG-001` 建立。
