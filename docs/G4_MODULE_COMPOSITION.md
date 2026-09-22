# Module Composition（G4-MOD-002）

> 文件治理
> - 目的：描述 `megis.composition` 如何實作藍圖 §4.16 composition intent 與 §12：把 Module＋Relationship 落到 V2 Engineering IR，只衍生「有 proven 來源」的工程限制條件、移除時清除或明確標示 dependent constraints、絕不補虛構工程值、並固定 Module 版本。
> - 目前內容：closed intent 集合、constraint recipe 表、add／remove／version 三種行為、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：G4-MOD-002 實作 commit（完工報告列出 SHA）

## 目的

當使用者在組合圖上「拖入 PCB／USB-C／M3 Module」時，`megis.composition` 負責把它實體化成 IR component，並根據 G4-GRF-001（§4.16）的 Relationship 語意衍生限制條件。整顆引擎只有一個目標：讓組合後的圖保持可驗證、可再現、且每個數值都追得到來源。缺失或未被證實的工程參數絕對不會被編成默認數字，而是變成 `unsafeToDefault` 的 unknown，並封鎖對應的 constraint kind。

## Closed intent 集合

組合引擎只在 G4-GRF-001 八型別中選出五種可「實體化」為 constraints 的 intent；其餘三種（`aligns`／`covers`／`removable_along`）需要幾何 solver 支援，本階段不衍生 constraint：

| v3 intent | IR relationshipType | 介面 | constraint kind／type | proven 參數 |
|---|---|---|---|---|
| `contains` | `contains` | 無 | 無（本層級不產數值限制） | — |
| `mounts_to` | `mounts_to` | `mount` | `mount`／`interface` | `engagement_length_mm`（nominal）、`hole_alignment_tolerance_mm`（tolerance） |
| `fastens` | `fastened_by` | `mount` | `fastener`／`interface` | `screw_length_mm` |
| `opens_through` | `connects_to` | `opening` | `opening`／`clearance` | `clearance_gap_mm` |
| `clears` | `clearance_to` | 無 | `clearance`／`clearance` | `minimum_distance_mm` |

`megis.composition.COMPOSABLE_TYPES` 是封閉集合：新增 intent 需 schema MINOR 版本並增加語意測試。

## add：組合一個 Module（`compose_module`）

`compose_module(ir, module, relationship, *, component_id=None, recorded_at=..., allow_upgrade=False)` 對**通過驗證的 V2 Engineering IR 原地施工**，回傳 `CompositionResult` 報告新增了哪些實體、封鎖了哪些 constraint。

- relationship `source` 必須等於該 Module 組合後的 IR component id（預設由 `module_id` 決定，例如 `mod.pcb → COMP-PCB`）；`target` 必須是 IR 內既存且相異的 component。
- 依 recipe 產出 interface（`mount`／`opening`）、relationship 與 constraint；constraint 的 `nominal`／`tolerance` **只來自** relationship 參數 entry，且該 entry 必須帶非空 `provenance`。
- 缺值、無 provenance、或數值 ≤ 0 時：不產生該 constraint，改寫入一個 `unsafeToDefault: true` 的 unknown（`/constraints/<kind>`），並把 `blockedConstraintKinds` 標記上去。`fabricatedValuesUsed` 永遠為 `false`。
- 每個新實體（component／interface／relationship／constraint）都寫入 `source: derived` 的 provenance，`sourceRef = module:<id>@<version>`。

## remove：移除一個 Module（`decompose_module`）

`decompose_module(ir, module_id)` 清除該 Module 組合出的 component，以及所有指向它的 interface、relationship、constraint、unknown 與 provenance。被清除的 dependent constraints 會同時列在 `removedConstraintIds` 與 `markedConstraintIds`，讓「刪除連帶影響哪些限制條件」是可稽核的，而非靜默發生。

移除從未組合的 module 會拋 `CompositionValidationError`（`unknown module ...`）。

## version：固定版本、不靜默升級

每個組合後的 component 都帶 `module:<id>@<version>` 的 pinned marker。相同 `module_id` 再次組合：

- 相同版本 → idempotent（`changed=False`，不新增任何實體）。
- 較新版本且未給 `allow_upgrade` → 維持已 pinned 的版本，回傳 `upgrade_blocked=True`；IR 不變。
- 較新版本且 `allow_upgrade=True` → 先剝離舊版所有 derived 實體再以新版本重組，`pinnedModules` 更新為新版本。

這保證「引用舊版 Module 的既有 Design Run」永遠可重現，不會被後來的 Module 更新悄悄改掉。

## Golden corpus 與驗證

`contracts/g4/golden/module-composition-corpus.json` 提供 20 個 table-driven cases，基底都指向 `contracts/g1/golden/reference-fixture.json`（Fixture golden IR）。涵蓋：

- add：PCB `mounts_to` Base、USB-C `opens_through` Cover、M3 `fastens` Base、PCB `clears` Cover、Enclosure `contains` PCB、PCB＋USB-C 同圖組合。
- 缺值不補：mount 缺 `engagement_length_mm` provenance、opening 缺 `clearance_gap_mm` provenance → 只產 unknown＋blocked，不產 constraint、不補數字。
- version：同版本重組 idempotent、新版被 block、`allow_upgrade` 才更新。
- remove：移除 PCB 清除 dependent entities 並 `markedConstraintIds` 明列；移除未知 module 被拒。
- 錯誤路徑：不支援的 intent（`aligns`）、source 錯、target 缺、self-target、component id collision、invalid Module／Relationship 文件在施工前即被拒。

`tests/test_g4_mod_002.py` 以 29 個 tests 驅動 corpus 並額外斷言 IR 內容真理契約（constraint nominal／tolerance 來自 provenance、module marker、unknown `unsafeToDefault`、idempotent／版本固定）。`scripts/verify_g4_mod_002.py` 全數驗證後寫入 `artifacts/g4-mod-002/verification.json`（E3），不產生工程製品。

```powershell
.venv/Scripts/python.exe -m pytest tests/test_g4_mod_002.py
.venv/Scripts/python.exe scripts/verify_g4_mod_002.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

## Owner

MEGIS Builder；使用者可否決某個 composition intent 的 constraint 參數或版本固定策略。
