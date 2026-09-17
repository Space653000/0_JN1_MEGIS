# ADR-0009：由施工者研究 Reference Case 未知值

> 文件治理
> - 目的：記錄 D8 的研究責任、來源品質與 provenance 規則。
> - 目前內容：施工者可上網研究，但尚未完成 G1-REQ-001 的政策決策。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D8
- 決策者：使用者
- 相關工作項目：V3C-DEC-001、G1-REQ-001、G3-SRC-001

## 背景

Reference Fixture 的 PCB 尺寸、擺放方式、USB-C 位置、連接器外形、螺紋與公差不能由模型猜測，也不能把過渡預設冒充使用者輸入。使用者已授權施工者上網研究最合適且可查證的方案。

## 決策

施工者負責以公開、可追溯來源研究未知值。優先使用原廠 mechanical drawing、正式 datasheet、公開標準 metadata 與可信技術文件；每個採用值記錄 URL、標題、料號／版次、取用日期、擷取參數、選擇理由與適用範圍。

研究值的 provenance 必須是 `researched`，不得改標為 `user`。來源衝突、無法開啟、授權不明或沒有足夠機械資料時，值維持 `unknown`，不得完成 golden approval。

## 考慮過的替代方案

1. 由模型補值：不可追溯且有 hallucination 風險，拒絕。
2. 讓使用者提供所有機械圖：會阻塞目前 reference case，且可能引入非公開資料。
3. 施工者研究公開來源並保留 unknown：符合 D8，故採用。

## 後果

- 本 ADR 只核准研究方法；目前 `implementationStatus` 為 `policy_only`，不表示研究已完成。
- 研究成果必須進入 `docs/research/`，並由測試核對 golden provenance。
- 受著作權保護的標準原文不得整份入庫，只保存允許的 reference metadata 與原創摘要。

## 證據

- `docs/research/README.md`
- `docs/RULE_SOURCES.md`
- `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md`
