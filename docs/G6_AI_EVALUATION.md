# G6-AI-003 AI 評估語料與 KPI

> 文件治理
> - 目的：記錄 recorded intent corpus、case-level 結果與 V3 §18.3 AI KPI。
> - 目前內容：54 筆平衡語料、deterministic evaluator、Wilson 95% CI、目標與延後項。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 最後審查 commit：G6-AI-003 實作 commit。

## 語料設計

語料共有 54 筆，六類各 9 筆：完整輸入、缺資訊、矛盾、超出 envelope、單位混用與 prompt injection。每筆保存 intent、recorded output、expected fields、expected unknowns、越界 oracle 與 injection target fields；不含客戶資料、未授權 datasheet 或外部服務輸出。

這是 D3「無真實 provider」決策下的 recorded-fixture evaluation framework。它驗證 adapter、schema quarantine、abstention、envelope detection 與 injection isolation；不宣稱代表任何未接入模型的真實世界品質。

## KPI

| 指標 | 結果 | Wilson 95% CI／處置 |
|---|---:|---|
| Schema conformance | 54/54，100% | 93.3584%～100% |
| Field precision | 51/51，100% | 92.9951%～100% |
| Field recall | 51/51，100% | 92.9951%～100% |
| Hallucinated value rate | 0/51，0% | 0%～7.0049% |
| Unsafe hallucinated value rate | 0/41，0% | 0%～8.5670%；目標達成 |
| Abstention correctness | 57/57，100% | 93.6859%～100% |
| Out-of-envelope detection | 9/9，100% | 70.0847%～100%；目標達成 |
| Unit error rate | 0/41，0% | 0%～8.5670%；目標達成 |
| Injection resistance | 9/9，100% | 70.0847%～100%；目標達成 |
| Explanation grounding | 不適用 | 明確延後至 G6-AI-004；未以零分母宣稱 100% |

樣本均小於 100，因此比例同時報告 Wilson score 95% 信賴區間。百分比是固定 recorded corpus 的測試結果，不是模型信心值，也不顯示於產品 UI。

## 證據

- Corpus：`contracts/g6/golden/ai-evaluation-corpus.json`
- Corpus schema：`schemas/v3/ai-evaluation-corpus.schema.json`
- Report schema：`schemas/v3/ai-evaluation-report.schema.json`
- Case-level report：`artifacts/g6-ai-003/case-results.json`
- Verification：`artifacts/g6-ai-003/verification.json`
- Tests：`tests/test_g6_ai_003.py`

```powershell
.\.venv\Scripts\python.exe scripts\verify_g6_ai_003.py
.\.venv\Scripts\python.exe -m pytest tests\test_g6_ai_003.py
```

G6-AI-004 接續實作 grounded explanation，屆時 explanation grounding 必須由 `not_applicable` 轉為實測 100%，且每個數值都能回指 IR、rule result 或 manifest。
