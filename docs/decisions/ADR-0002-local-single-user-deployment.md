# ADR-0002：採本機單一使用者部署

> 文件治理
> - 目的：記錄 D1 部署範圍與其安全邊界。
> - 目前內容：已接受的 local single-user 決策、替代方案、後果與證據。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D1
- 決策者：V3 藍圖預設，並由既有本機實作與使用者工作區限制確認
- 相關工作項目：V3C-DEC-001、G6-UI-001

## 背景

MEGIS 第一條能力切片需要可重建 CAD 工具鏈、本機檔案存取與長時間工程工作。現階段沒有多租戶隔離、遠端身分驗證、雲端資料治理或服務營運證據。

## 決策

部署固定為 Windows 本機 single-user。所有服務只綁定 `127.0.0.1`；不提供 LAN、公網、multi-user 或 multi-tenant 模式。所有快取、環境、資料與製品留在 `C:\0_JN1_MEGIS`，唯一允許的遠端同步目標是指定 GitHub repository。

## 考慮過的替代方案

1. Cloud service：需要額外的資料、權限、租戶與營運控制，目前沒有需求或證據。
2. LAN multi-user：仍需 authentication、concurrency 與資料隔離，超出目前 envelope。
3. Local single-user：與現有工具鏈、風險與使用者工作方式一致，因此採用。

## 後果

- D1 不授權公開部署、遠端 API 或多人共用資料目錄。
- 未來若要擴張部署範圍，必須建立新 ADR、威脅模型、envelope change 與 sign-off。
- G6 正式 UI 仍須保持本機邊界；UI-0 不因本決策升級成工程能力。

## 證據

- `AGENTS.md`
- `docs/OPERATIONS.md`
- `docs/SUPPORTED_ENVELOPE.md`
