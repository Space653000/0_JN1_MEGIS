# G1 Golden Cases

## 固定案例

`G1-IR-003` 建立三個共用 Engineering IR 契約的版本化輸入：

- `reference-fixture.json`：Reference Fixture 的 PROTOTYPE golden IR，包含 base、cover、PCB、關係、CNC 製程與最小壁厚。
- `acoustic-schema-only.json`：聲學詞彙的 CONCEPT schema-only 案例，保留 solver boundary 與 leak model 為 unsafe unknown。
- `robot-schema-only.json`：機器人配置的 CONCEPT schema-only 案例，保留 kinematics、cabling 與 safety validation 為 unsafe unknown。

聲學與機器人案例只證明核心 vocabulary、ID、reference、provenance 與 knowledge-state 可共用，不宣稱 CAD、求解器、機構合成、線束或安全驗證已完成。

## Round trip 與下游消費

`megis.contracts.serialization` 在輸出前與輸入後都執行完整 Engineering IR 驗證，並使用排序 key、固定 separator 與 UTF-8 產生 deterministic JSON。Reference Fixture 經 load → serialize → deserialize → serialize 後，資料等價且序列化內容與 SHA-256 穩定。

`megis.contracts.consumer` 不是 JSON 產生器；它驗證後實際讀取 design、maturity、components、domains、relationships 與 unsafe unknowns，形成不可變的 `EngineeringIrSummary`。測試也核對 Reference Fixture 的 expected graph 與尚未生成的 future artifact metadata。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_g1_golden_cases.py
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

此工作項不生成 CAD、BOM、圖面或 release package；`reference-fixture-expectations.json` 明確分類為 `GOLDEN_EXPECTATION_ONLY`。
