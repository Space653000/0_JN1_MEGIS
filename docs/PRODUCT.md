# MEGIS 產品定義

> 文件治理
> - 目的：固定 MEGIS 的產品定位、使用者、首條能力切片與 anti-goals。
> - 目前內容：V3 Reference Fixture 產品範圍及誠實成熟度邊界。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 目的

MEGIS 將機械與製造工程判斷轉成可追溯、可驗證、可重現的引導式設計流程。第一條完整能力固定為 supported envelope 內的小型 CNC 治具／電子外殼。

## 使用者

- 主要使用者：不熟悉 CAD、但能回答用途、外形、零件與製造限制的產品開發者。
- 工程使用者：機構／製造工程師，檢查假設、規則、幾何與 package 證據。
- 維運者：在單機 Windows 環境重建、驗證與保存 Design Run。

## 目前內容

Repository 已完成 UX-0、G0、G1 舊版基線及 G2 assembly geometry，正在執行 V3C 補強。自動化成熟度上限為 `PROTOTYPE`；無具名工程師時不得宣稱 `ENGINEERING_REVIEWED` 或 `RELEASED`。

## Anti-goals

- 不把 UI 合成資料、feasibility spike 或 benchmark case 冒充 Design Run。
- 不提供任意 CAD、任意材料／製程、量產放行或安全認證。
- AI 不決定尺寸、材料、規則結果、maturity 或 sign-off。
- 不將客戶 CAD、datasheet 或識別資訊送往未授權外部服務。

## Owner

MEGIS Builder；產品方向與 envelope 擴張由使用者決策。

## 最後審查 commit

`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`
