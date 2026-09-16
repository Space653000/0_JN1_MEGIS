# G0 CadQuery Reference Case spike

此目錄只驗證藍圖 `G0-CAD-001` 所需的 CadQuery／OpenCascade 可行性。模型採固定 `120 × 80 × 35 mm` Reference Case envelope、2 mm floor/wall 與四個 M3 clearance holes；輸出 STEP、ASCII STL 與 Z=10 mm 的 2D DXF section。

這不是 G2 production geometry backend，也不是可製造放行檔。所有輸出均標記 `FEASIBILITY_SPIKE`、`PROTOTYPE` 與 `engineeringReviewRequired: true`。

```powershell
cd C:\0_JN1_MEGIS
.\.venv\Scripts\python.exe -m spikes.g0_cad.reference_case --output-dir artifacts\g0-cad
.\.venv\Scripts\python.exe -m pytest tests\test_g0_cad_reference_case.py
```
