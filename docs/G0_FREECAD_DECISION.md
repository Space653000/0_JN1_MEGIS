# G0-DRW-001 FreeCAD TechDraw 決策

> 文件治理
> - 目的：記錄圖面 backend feasibility 與 fallback。
> - 目前內容：FreeCAD headless 檢查及固定模板 SVG fallback。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 決策：fallback

FreeCAD 1.1.3 的 `TechDraw::DrawViewPart` 可在 `FreeCADCmd` headless 模式載入 G0 Reference Case STEP、完成 top-view projection，並回報 `Up-to-date` 與 12 條 visible edges。原生 SVG／PDF page export 依賴 `TechDrawGui`；該模組在 console application 明確無法載入，`TechDraw::DrawPage` 也沒有 headless `getPageSVG()` API。

因此採藍圖允許的固定模板 fallback：FreeCAD TechDraw headless 負責工程投影，MEGIS 將其 projected edges 寫入版本化 A4 SVG template。此路徑已產生有效 XML SVG、完整保留 12 條投影 edges，並永久標示 `DRAFT - ENGINEERING REVIEW REQUIRED` 與 `NOT FOR MANUFACTURING`。

## 支援與限制

| 能力 | 結果 | 證據 |
|---|---|---|
| FreeCAD 1.1.3 repository-local runtime | pass | `environment/freecad.lock.json` |
| FreeCADCmd headless STEP load | pass | `artifacts/g0-freecad/verification.json` |
| TechDraw top-view projection | pass | `Up-to-date`、12 visible edges |
| TechDrawGui in console | unavailable | `ImportError: Cannot load Gui module in console application` |
| 原生 headless SVG/PDF page export | unavailable | `DrawPage` 無 SVG API；GUI module 不可載入 |
| 固定模板 SVG fallback | pass | valid XML、12 polylines、review notice |
| PDF 與 engineering drawing QA | deferred | `G5-DRW-001` |

此決策不表示 SVG 已成為 release drawing，也不表示尺寸、GD&T、title block 或 projection 已通過工程師審查。G5 只能以此 spike 作為 fallback 起點，必須補固定 dimension whitelist、PDF conversion 與 manual QA。

## 隔離與重跑

官方 Windows x86_64 portable archive 的 byte count、SHA-256 與 URL 已鎖在 `environment/freecad.lock.json`。Archive、runtime、user cfg、system cfg 與 TEMP 全部位於 `C:\0_JN1_MEGIS`，未執行 installer、未修改系統設定，也未與其他專案共用。

```powershell
cd C:\0_JN1_MEGIS
powershell -ExecutionPolicy Bypass -File scripts\run-freecad-spike.ps1
.\.venv\Scripts\python.exe -m pytest tests\test_g0_freecad_fallback.py
```

官方版本來源：<https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3>
