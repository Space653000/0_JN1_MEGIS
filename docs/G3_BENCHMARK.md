# Benchmark Metrics（G3-BEN-001）

> 文件治理
> - 目的：描述 `megis/benchmark` 如何把 v3 藍圖的「驗證門檻」量化成可重跑的 KPI（precision／recall／FP／false release／Wilson CI）。
> - 目前內容：偵測語意、語料結構、holdout 封存規則、KPI 定義與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：G3-BEN-001 完工 commit（完工報告列出 SHA）

## 目的

`megis.benchmark` 是 G3 驗證能力的「度量引擎」：它接受一份 benchmark corpus（dev 或 holdout），逐 case 餵給真實元件——geometry／collision／clearance validators（`megis.validation`）、CNC DFM 規則（`megis.rules`）與 maturity evaluator（`megis.maturity`）——然後比較觀察值與 oracle，輸出總合 KPI。它本身不產生任何工程製品，只輸出 `artifacts/g3-ben-001/verification.json` 這類證據檔。

## 偵測語意

一次 **detection** 定義為一般流水線對某 case 產出的一次 failed check：

- 每個 failed validation check（`ValidationIssue`，status 為 `fail` 或 `error`）計一次，帶自己的 severity；
- 每個 failed rule evaluation（`RuleEvaluation`，status 為 `fail`）計一次，帶該規則的 severity。

case 的 observed max severity 是 detections 中最高 severity（`error` > `warning` > `info`）；無 detection 時為 `pass`。這個 check-level 定義同時是 corpus `expected_detection` 的語意，因此複合案例（一個 case 同時有碰撞、餘隙、薄壁規則）會如實計入每次 failed check，而不是對同一對元件去重。

## 語料結構

- `contracts/g3/golden/benchmark-corpus.json`：dev corpus，`corpus_id benchmark-g3-dev@1.0.0`，30+ defect、10+ clean；bucket 涵蓋 `golden / negative / boundary / regression`。
- `contracts/g3/holdout/holdout-corpus.json`：holdout corpus，10 cases（7 defect、3 clean），bucket `holdout`。
- 每 case 的 `oracle` 記錄 `expected_detection`、`expected_max_severity`、`error_grade`、`expected_maturity_max`、`expect_false_release`，由 `schemas/v3/benchmark-corpus.schema.json` 約束。
- 驗證輸入走 `validation_input`（AABB 元件與 clearances）、DFM 輸入走 `rule_checks`、成熟度情境走 `maturity_input`。

## Holdout 封存（§18.1）

依藍圖「先封存、後施工」，holdout oracle 在 metrics 實作前已獨立封存並將 SHA-256 寫入 `docs/ACCEPTANCE.md`（R-AGT-002）：

`73a25950c4b45d904daa6bab963a16ae11599f6bfa660966582ba0d60ed5a96b`

`scripts/verify_g3_ben_001.py` 與 `tests/test_g3_ben_001.py` 都會重新計算 holdout 的 SHA-256 並比對封存值；改 oracle 視同 golden 更新，需 ADR。

## KPI 定義

| KPI | 定義 |
|---|---|
| True positive（TP） | defect case 且 observed detections ≥ 1 |
| False negative（FN） | defect case 且 observed detections = 0 |
| False positive（FP） | clean case 且 observed detections ≥ 1 |
| True negative（TN） | clean case 且 observed detections = 0 |
| recall | TP / (TP + FN) |
| precision | TP / (TP + FP) |
| Wilson 95% CI | 對 precision／recall 取二項式 Wilson score interval（z = 1.96） |
| false release | observed maturity level > oracle `expected_maturity_max` |
| clean pass rate | TN / (TN + FP) |
| case pass rate | oracle 完全吻合（detection 數、max severity、error grade）且未 false release 的 case 比例 |
| detection exact rate | defect case 中观测 detection 數與 oracle 完全一致的比例 |

G3-BEN-001 目標：dev corpus 與 holdout corpus 均達成 recall 1.0、precision 1.0、FP 0、false release 0。

## False release 語意

每個 case 都會用 corpus 的 `maturity_input`（缺省為健康模板）組成輸入，並透過 `MaturityInput` 評估。若 case 是 error-grade defect，benchmark 會把偵測到的 error sources 注入 `unresolved_errors`，讓 evaluator 證明「error 未處置時最多停在 CONCEPT、不可能升到 PROTOTYPE」。假陽性放行（false release）＝ evaluator 給出的成熟度高於 oracle 上限。

## 驗證

```powershell
.venv/Scripts/python.exe -m pytest tests/test_g3_ben_001.py
.venv/Scripts/python.exe scripts/verify_g3_ben_001.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

`tests/test_g3_ben_001.py` 覆蓋語料 schema、規模、holdout hash、每個 case 的 oracle、KPI 公式與合成 FP／FN 情境；`scripts/verify_g3_ben_001.py`（E3）寫入並重跑兩份語料後輸出 `artifacts/g3-ben-001/verification.json`，不產生工程製品。

## Owner

MEGIS Builder；使用者可否決 KPI 目標、語料擴充與 false release 定義。
