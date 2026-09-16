# G1 Engineering Primitives

## 契約範圍

`G1-IR-001` 固定跨模組共用的最小語意，不定義完整 Engineering IR：

- JSON Schema Draft 2020-12，schema version `2.0.0`
- base units：`mm`、`deg`、`kg`、`s`
- 每個工程 quantity 必須顯式帶 `unit`，並以 `nominal` 或 `min`／`max` 表達
- coordinate system 固定右手系，明確記錄 x／y／z 的工程語意
- entity ID 使用穩定、全大寫、連字號分段格式
- provenance source 只允許 `user`、`derived`、`defaulted`、`database`、`engineer_override`
- knowledge state 支援 `known`、`derived`、`defaulted`、`unknown`、`unsafe_to_default`

`unknown` 與 `unsafe_to_default` 不得攜帶虛構的 `value`。`derived`／`database` provenance 必須有 `sourceRef`；使用者與工程師覆寫必須有 actor，default 與工程師覆寫必須有 rationale。

## 檔案

- `schemas/v2/primitives.schema.json`：正式 primitive schema
- `megis/contracts/validation.py`：Draft 2020-12、format 與跨欄位 semantic validator
- `contracts/g1/examples/primitives-valid.json`：固定正向範例
- `tests/test_g1_primitives.py`：正向與負向 contract tests

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g1_primitives.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

負向測試涵蓋缺少 unit、左手座標系、重複軸語意、duplicate／未宣告 ID、非法 provenance source、unknown 偽造值、缺少 source reference、非法 timestamp、非法 ID、dangling reference 與反向 range。

## 邊界

本工作項只固定 primitives。Requirement、Module、Rule、Constraint、Validation Result 與完整 Engineering IR 組合由 `G1-IR-002` 完成；domain golden cases 與 migration 也尚未在本工作項宣稱完成。
