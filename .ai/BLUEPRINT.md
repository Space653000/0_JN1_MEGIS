# MEGIS 藍圖索引（本專案唯一藍圖依據）

> 文件治理
> - 目的：作為本專案「唯一藍圖依據」的單一入口；不重複既有藍圖內容，只索引、引用與說明彼此關係。
> - 目前內容：v1／v2／v3 藍圖索引、v3 章節導覽、v3 之上的既有控制面文件對照表。
> - Owner：Claude Code（研究／規劃／審查角色，見 [CLAUDE_REVIEWER.md](CLAUDE_REVIEWER.md)）
> - 最後盤點日期：2026-09-24
> - 不刪除、不覆寫任何既有藍圖檔案；本檔只做索引與引用。

## 1. 生效版本

**本專案目前唯一生效、可執行的藍圖是：**

> [`MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md`](../MEGIS_Blueprint/MEGIS_Mechanical%20Engineering%20Generative%20Intelligence%20System%20—%20v3.0-claude-code.md)

採用紀錄：[`docs/decisions/ADR-0001-adopt-v3-blueprint.md`](../docs/decisions/ADR-0001-adopt-v3-blueprint.md)（V3C-BCR-001）。

其餘版本為封存基線，**保留但不再作為施工依據**：

| 版本 | 路徑 | 狀態 |
|---|---|---|
| v1.0 | [`MEGIS_Blueprint/OLD/Generative Mechanical Design Factory — Master Blueprint & Detailed Implementation Plan.md`](../MEGIS_Blueprint/OLD/Generative%20Mechanical%20Design%20Factory%20—%20Master%20Blueprint%20%26%20Detailed%20Implementation%20Plan.md) | 封存參考，願景來源 |
| v2.0 | [`MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v2.0 Codex.md`](../MEGIS_Blueprint/MEGIS_Mechanical%20Engineering%20Generative%20Intelligence%20System%20—%20v2.0%20Codex.md) | 封存基線，v3 已完整保留其 Gate 與 30 個工作項目 ID |
| **v3.0-claude-code** | 見上 | **生效版本** |

v3 相對 v2 的定位：**加法式擴充**，不推翻 v2 已核准的方向與 30 個工作項目 ID；v2 中在既有 Gate 內暴露的缺口以 `V3C-*`（V3 Conformance lane）work item 補足，見 v3 §0.6、§26.1。

## 2. v3 藍圖章節導覽（快速定位用，非內容重述）

| 主題 | 章節 |
|---|---|
| 文件目的、規範用語、既有 repository 導入規則 | §0 |
| 核心決策、成熟度狀態、Reference Case 參數 | §1 |
| 支援邊界（Supported envelope） | §2 |
| 系統不變量與強制機制（18 條） | §3 |
| 架構契約（IR、schema、error taxonomy、指紋、公差） | §4 |
| Agent 連續施工控制面（狀態檔、施工循環、寫入鎖、雙 Agent／自我審查協定） | §5 |
| Gate 依賴圖與通用規則 | §6 |
| UX-0 | §7 |
| G0～G9 個別 Gate（目標、進入條件、工作、完成條件） | §8～§17 |
| 驗證策略（benchmark、KPI、AI KPI、測試紀律） | §18 |
| 工程知識治理／AI 治理／安全／資安／UX 原則／營運 | §19～§24 |
| 開工條件與完成定義（DoR／DoD） | §25 |
| 完整工作佇列（機器可讀依據） | §26 |
| Agent 指令範本 | §27 |
| 風險登錄表 | §28 |
| 審查意見處置與追溯（v1→v2→v3） | §29 |
| 最終成功定義 | §30 |
| 附錄 A～C（範本、Reference Case 參數檔、版本紀錄） | 附錄 |

## 3. 使用者對 v3 的關鍵決策（已生效，不需重新詢問）

- **D6（誰做誰審查）**：不設具名工程審查人；哪個 Agent 施工，就由該 Agent 以全新 session、乾淨 checkout 自我審查。記錄於 v3 §5.7、[`ADR-0007`](../docs/decisions/ADR-0007-builder-self-review.md)。
- **D8（未知值研究）**：Reference Case 未知值（PCB 尺寸、擺放、USB-C 位置等）由施工者上網研究最適合方案，附可查證來源。記錄於 v3 §9.1、[`ADR-0009`](../docs/decisions/ADR-0009-research-reference-unknowns.md)。
- **本次新增（2026-09-24）**：Claude Code 在本專案的預設角色是研究／規劃／審查／驗收，而非主要施工者；細節見 [CLAUDE_REVIEWER.md](CLAUDE_REVIEWER.md)。此安排疊加在 D6 之上，不取代 D6：若 Claude Code 實際施工某工作項目，仍必須依 D6 以全新 session 自我審查該項目。

## 4. v3 藍圖與既有控制面文件的對照

v3 藍圖是規範性文件；下列既有文件是**依藍圖產生的施工證據與治理索引**，不是另一份藍圖：

| 既有文件 | 對應 v3 章節 | 用途 |
|---|---|---|
| `execution/PROJECT_STATE.md` | §5.1 | 目前 Gate、work item、最後綠色 commit |
| `execution/WORK_QUEUE.yaml` | §5.1、§26 | 機器可讀工作佇列，唯一狀態真相來源 |
| `execution/BLOCKERS.yaml` | §5.1 | 真正阻塞條件 |
| `execution/AGENT_CLAIM.json` | §5.7 | 施工寫入鎖 |
| `execution/reviews/`、`execution/signoffs/` | §5.12、§6.3 | 自我審查報告與決策紀錄（E3／E4） |
| `docs/ACCEPTANCE.md` | §25.3 | Gate 驗收索引（本專案另以 [ACCEPTANCE.md](ACCEPTANCE.md) 做精簡入口） |
| `docs/DECISIONS.md`、`docs/decisions/ADR-*` | §5.11 | 決策紀錄索引 |
| `docs/RISKS.md` | §28 | 風險登錄表現況 |
| `docs/SUPPORTED_ENVELOPE.md` + `config/envelope/` | §2.4 | 機器可讀支援範圍 |
| `docs/RULE_SOURCES.md` + `config/rule-sources/` | §19.1 | 規則來源登錄 |
| `docs/ERROR_CODES.md` | §4.10 | 錯誤碼登錄 |

## 5. 目前施工進度

完整狀態見 [STATUS.md](STATUS.md)；驗收現況見 [ACCEPTANCE.md](ACCEPTANCE.md)。
