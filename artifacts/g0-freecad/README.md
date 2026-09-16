# G0-DRW-001 evidence artifacts

此資料夾是 FreeCAD 1.1.3 TechDraw headless feasibility spike 證據，不是工程放行圖。

- `reference_case_techdraw.FCStd`：包含固定 template、Reference Case source、TechDraw top view 與 review annotation。
- `reference_case_techdraw_fallback.svg`：由 FreeCAD TechDraw headless 投影的 12 條 visible edges，套入 MEGIS 固定 A4 SVG template。
- `verification.json`：工具版本、能力決策、SHA-256 與責任邊界。

原生 TechDraw SVG/PDF export 依賴 `TechDrawGui`，不能在 `FreeCADCmd` console application 載入，因此決策為 `fallback`。PDF 轉換與人工 QA 保留給 `G5-DRW-001`。
