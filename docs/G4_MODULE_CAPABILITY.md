# Module Capability Levels（G4-MOD-001）

> 文件治理
> - 目的：描述 `megis.module` 如何實作藍圖 §4.16 Module 最小欄位與四級 capability，以及 §12 capability-to-behaviour 限制表。
> - 目前內容：四級閉集合、capability policy、schema 與語意驗證規則、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：G4-MOD-001 實作 commit（完工報告列出 SHA）

## 目的

Module 是 MEGIS 產品組裝的最小可索引單位。`megis.module` 將「某個 Module 到底能提供多少工程行為」收斂成一個封閉的四級詞彙，並讓每一級對 UI、佈局、幾何、驗證與成熟度上限產生可被測試的限制。任何模組宣稱某一級能力，都必須通過 `schemas/v3/module.schema.json` 與 `validate_module_document` 的一致檢查。

## 四級閉集合（藍圖 §4.16）

| capability_level | UI | 佈局 | 幾何 | 驗證 | 成熟度上限 |
|---|---|---|---|---|---|
| `metadata_only` | 顯示「僅資料」、不可放置 | 否 | 否 | 否 | DRAFT |
| `layout_capable` | 可放置 envelope | 是 | envelope box | collision／clearance | CONCEPT |
| `geometry_capable` | 可放置 | 是 | 是 | 幾何規則 | PROTOTYPE（需規則通過） |
| `validated` | 可放置 | 是 | 是 | 全部適用規則 ＋ golden | PROTOTYPE |

此詞彙是封閉集合：新增等級需 schema MINOR 版本並增加語意測試（§4.16）。等級順序具單調性，`capability_index` 遇到未知等級回傳 `-1`，不拋例外、不靜默放行。

## Capability policy（`megis/module/capability.py`）

`policy_for(level)` 回傳該級的行為表列，對應藍圖 §12：

- `metadata_only`：不可佈局、不可幾何、無驗證、成熟度上限 `DRAFT`。
- `layout_capable`：可佈局、限 envelope、驗證為 `collision`／`clearance`、上限 `CONCEPT`。
- `geometry_capable`：可佈局與幾何、驗證為 `geometry_rules`、上限 `PROTOTYPE`。
- `validated`：可佈局與幾何、驗證為 `all_applicable_rules` ＋ `golden`、上限 `PROTOTYPE`。

幾何產生器參考（`geometry_generator_ref`）在 `geometry_capable` 以上為必填；低於 `geometry_capable` 時不得攜帶，避免 `metadata_only` 模組被誤當成可產生幾何。

## Schema 與語意驗證（`megis/module/schema.py`）

`validate_module_document` 合併兩種檢查並回傳一份確定性的 JSON Pointer 錯誤清單：

- Schema 層（`schemas/v3/module.schema.json`）：`module_id`、SemVer `version`、四級 `capability_level`、`metadata` 每欄必含 `value` 與 `provenance`、未知欄位拒絕、`geometry_generator_ref` 依能力等級的條件必填。
- 語意層：`geometry_generator_ref` 只能在 `geometry_capable` 以上出現；介面 ID 不得重複；`clearance_envelopes` 必須參照已宣告的介面。

每個 finding 都指向精確的 JSON Pointer（例如 `/metadata/wall_thickness_mm/provenance`），`required`／`additionalProperties` 這類 jsonschema 原生指向父物件的錯誤會被展開為確切缺欄位置，確保存取者不必猜測哪個鍵出錯。

## Golden corpus 與驗證

`contracts/g4/golden/module-corpus.json` 提供 18 個 table-driven cases（6 positive、12 negative），涵蓋四級正例、未知等級、缺產生器、缺必填、重複介面、懸空 envelope、無 provenance metadata 與未知欄位。`scripts/verify_g4_mod_001.py` 全數驗證後寫入 `artifacts/g4-mod-001/verification.json`（E3），不產生工程製品。

```powershell
.venv/Scripts/python.exe -m pytest tests/test_g4_mod_001.py
.venv/Scripts/python.exe scripts/verify_g4_mod_001.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

## Owner

MEGIS Builder；使用者可否決某個模組的 capability level 宣稱及其行為開放範圍。
