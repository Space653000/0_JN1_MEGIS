# G2 Fixture Base

> 文件治理
> - 目的：說明 Reference Fixture base 幾何切片。
> - 目前內容：CadQuery base solid、尺寸、拓樸與重跑證據。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

`G2-CAD-002` 以 Reference Fixture golden IR 經 geometry planning 與 capability negotiation 驅動 `CadQueryBackend`。Adapter 內部持有 `cq.Shape`，核心只取得 opaque model token、尺寸、體積、validity 與 topology count。

自動驗證固定結果：120 × 80 × 20 mm、192000 mm³、1 solid、1 shell、6 faces、12 edges、8 vertices。相同 IR 與 locked CadQuery 2.8.0 會得到相同 model token 與 metadata。

```powershell
.\.venv\Scripts\python.exe scripts\verify_fixture_base.py
.\.venv\Scripts\python.exe -m pytest tests\test_g2_fixture_base.py
```

本工作項只建立記憶體內 base solid；尚未輸出 STEP、STL、DXF 或 release artifact。cover、fasteners、cutout 與 assembly 在 `G2-CAD-003`，匯出與重新載入在 `G2-CAD-004`。
