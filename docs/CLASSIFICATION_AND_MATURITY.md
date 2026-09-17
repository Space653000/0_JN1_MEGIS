# Artifact classification 與成熟度邊界

> 文件治理
> - 目的：定義 artifact classification 與 maturity 的不可混淆邊界。
> - 目前內容：v3 classification 契約、repository manifest scanner 與 Design Run provenance 最低要求。
> - Owner：MEGIS Builder
> - 最後審查 commit：`b8dc09748eb2f105764b08fb7c48c1891b50da0d`

## 目的

MEGIS v3 將「製品種類」與「工程成熟度」分開治理，避免可行性 spike、UX 展示或測試資料被誤認為正式工程輸出。這份規範落實藍圖 §1.4、§1.5；它只執行邊界檢查，不取代 G3 才會建立的 `megis.maturity` evaluator。

## 分類契約

| classification | 用途 | maturity |
|---|---|---|
| `DESIGN_RUN` | 由 Engineering IR 驅動的正式設計執行 | 必須是正式狀態，並附 evaluator provenance |
| `FEASIBILITY_SPIKE` | 外部工具可行性驗證 | 必須為 `null` |
| `UX_DEMO` | 合成 UX 展示 | 必須為 `null` |
| `BENCHMARK_CASE` | 驗證語料 | 必須為 `null` |
| `TEST_FIXTURE` | 單元或契約測試輸入 | 必須為 `null` |

所有 repository 內名為 `manifest.json` 的檔案都在掃描範圍。`.git`、`.venv`、`.temp`、`.cache`、`.pytest_cache`、`node_modules` 與 `dist` 等非版本化執行目錄不在範圍內；掃描器不追蹤 symlink，避免越過 repository 邊界。

## Design Run provenance

`DESIGN_RUN` 必須具有 `maturity_evaluation`，至少記錄非空 `evaluator_version`、代表評估輸入的 64 位小寫 SHA-256 `inputs_digest`，以及 `blocking_reasons` 陣列。這只證明 manifest 具有可稽核來源欄位；在 G3 evaluator、table-driven tests 與唯一寫入路徑完成前，不宣稱成熟度計算能力已存在。

## 自動驗證

```powershell
.\.venv\Scripts\python.exe scripts\verify_maturity.py
.\.venv\Scripts\python.exe -m pytest tests\test_v3_maturity.py
```

`scripts/run-baseline-ci.ps1` 會獨立執行 maturity scanner。任何缺少或未知 classification、缺少 maturity、非 Design Run 的非空 maturity、或缺少 evaluator provenance 的 Design Run，都會使本機 baseline 與 GitHub Actions 失敗。

機器可讀契約位於 `schemas/v3/artifact-classification.schema.json`；執行規則位於 `megis/governance/classification.py`。兩者均允許 manifest 帶有其他領域欄位，但不能放寬 classification/maturity 邊界。
