# 風險登錄表

> 文件治理
> - 目的：追蹤 V3 風險、觸發條件、緩解措施與下次審查點。
> - 目前內容：藍圖第 28 章風險的現況索引；每個 Gate review 必審。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## 目前內容

| ID | 風險 | P/I | 狀態 | 緩解／下一次審查 |
|---|---|---|---|---|
| R-CAD-001 | CAD boolean／fillet 不穩定 | M/H | open | deterministic ordering；G2 review |
| R-DRW-001 | FreeCAD headless 不穩定 | H/M | mitigated | 固定 SVG fallback；G5 review |
| R-SIM-001 | COMSOL 不可用 | H/L | accepted | 保持 out_of_scope；G7 review |
| R-RUL-001 | 規則品質不足 | M/H | open | 公開來源與 test vectors；G3 review |
| R-DNA-001 | Product DNA 過度抽象 | M/M | open | 三案例共用 vocabulary；G4/G8 review |
| R-PM-001 | Schedule illusion | M/M | controlled | WIP=1、只報證據；每次轉場 |
| R-AI-001 | AI hallucination | H/H | open | provenance、abstention、KPI；G6 review |
| R-DET-001 | Artifact 不可重建 | M/H | open | fingerprint 與 replay；V3C-DET/G5 |
| R-SAFE-001 | 安全宣稱過度 | L/H | controlled | maturity 上限與水印；每 Gate |
| R-DET-002 | ARM64／x64 差異 | M/M | open | tolerance 與 ADR；G5 review |
| R-AGT-001 | Agent 狀態漂移 | M/H | controlled | claim、verifier、WIP=1；每次轉場 |
| R-AGT-002 | 自我審查偏差 | H/H | accepted | fresh session、CI、holdout；Gate review |
| R-AGT-003 | 驗收被悄悄縮窄 | M/H | controlled | 必要 ID 與 immutable done；每 commit |
| R-GIT-001 | 二進位製品膨脹 | H/M | open | V3C-ART-001；下一 work item |
| R-LEG-001 | 標準原文／客戶資料入庫 | M/H | controlled | D5、只存摘要；研究與 review |
| R-PLT-001 | ARM64 CAD wheel 缺失 | M/M | open | x64 CI／emulation；工具鏈升級 |
| R-SPEC-001 | 研究值無可靠來源 | M/H | open | D8 與來源紀錄；G1-REQ-001 |
| R-SME-001 | 無具名工程師 | H/M | accepted | maturity ≤ PROTOTYPE；每 Gate |
| R-UX-001 | 新人不理解限制 | M/M | open | usability 對照；G6-USE-001 |
| R-SUP-001 | 相依套件供應鏈風險 | L/H | open | hash lock 與 secret scan；G0/V3C |
| R-AI-002 | Prompt injection | M/M | open | 資料隔離與 injection corpus；G6 |
| R-OPS-001 | 本機資料遺失 | L/M | open | Git 同步與備份還原；每季演練 |

## Owner

各列依藍圖角色；登錄維護者為 MEGIS Builder。

## 最後審查 commit

`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

