# Data Model: IntelliDbgKit PI Core Debug Hub

## 1. Core Domain

### 1.1 ProjectRun

| Field | Type | Required | Description |
|---|---|---|---|
| run_id | string | Y | 單次執行 ID |
| project_name | string | Y | 專案名稱 |
| target_id | string | Y | 目標板識別 |
| started_at | datetime | Y | 啟動時間 |
| finished_at | datetime | N | 結束時間 |
| state | enum | Y | 狀態機節點 |
| trigger | string | Y | 觸發來源 |
| summary_note | string | N | run 摘要 note 路徑 |

**State enum**: `BOOTSTRAP, TEST_LOOP, MONITOR, DETECT, CONDITION_ANALYSIS, REPRODUCE, DEBUG_ON, ANALYZE, ADV_TOOL_DECISION, AUTO_ACTION, REPRO_TRACE, RUNTIME_PATCH_TEST, REPORT, FAILED`

### 1.2 TraceEvent

| Field | Type | Required | Description |
|---|---|---|---|
| event_id | string | Y | 事件 ID |
| run_id | string | Y | 關聯 run |
| ts_ns | int64 | Y | 奈秒時間戳 |
| phase | string | Y | 流程階段 |
| source | enum | Y | `host/target` |
| tool | string | Y | tracezone/gdb/ebpf/uart 等 |
| target_id | string | Y | 來源 target |
| symbol | string | N | 關聯符號 |
| address | string | N | 位址 |
| severity | enum | Y | `info/warn/error/critical` |
| payload | object | Y | 原始或正規化內容 |
| semantic_tags | array<string> | N | 語意標籤 |
| compression_refs | array<object> | N | 壓縮引用 |
| links | array<object> | N | event/evidence/note 關聯 |

### 1.3 CommandIntent

| Field | Type | Required | Description |
|---|---|---|---|
| intent_id | string | Y | 語意命令 ID |
| action | string | Y | 動作 |
| object_path | string | N | TR-181 路徑 |
| parameter | string | N | 參數 |
| value | string/number/bool | N | 目標值 |
| constraints | object | N | timeout/retry/provider 等 |
| preferred_provider | string | N | 建議 provider |

### 1.4 ExecResult

| Field | Type | Required | Description |
|---|---|---|---|
| intent_id | string | Y | 對應 intent |
| provider | enum | Y | `uart/adb/ssh/telnet/local` |
| rc | int | Y | return code |
| stdout | string | N | 標準輸出 |
| stderr | string | N | 錯誤輸出 |
| latency_ms | int | Y | 耗時 |
| normalized | object | N | 正規化結果 |
| error_code | string | N | 結構化錯誤 |

## 2. Memory Domain

### 2.1 MemoryRecord

| Field | Type | Required | Description |
|---|---|---|---|
| memory_id | string | Y | 記憶記錄 ID |
| run_id | string | Y | 來源 run |
| memory_tier | enum | Y | `raw/working/candidate/long` |
| content | string | Y | 記憶內容 |
| evidence_refs | array<string> | Y | 關聯證據 |
| created_at | datetime | Y | 建立時間 |
| promoted_from | string | N | 升級來源 tier |

### 2.2 MemoryPromotionDecision

| Field | Type | Required | Description |
|---|---|---|---|
| decision_id | string | Y | 判定 ID |
| candidate_memory_id | string | Y | 候選記憶 ID |
| repro_count | int | Y | 重現次數 |
| consensus_score | number | Y | 共識分數 |
| threshold | number | Y | 升級門檻 |
| approved | boolean | Y | 是否核准升級 |
| reasons | array<string> | Y | 判定理由 |
| evaluated_at | datetime | Y | 判定時間 |

## 3. Compression Domain

### 3.1 CompressionLexiconEntry

| Field | Type | Required | Description |
|---|---|---|---|
| lexicon_id | string | Y | 字典條目 ID |
| token | string | Y | 壓縮 token（例如 `[tc_ndev_ev]`） |
| original_pattern | string | Y | 原字串樣板 |
| reverse_rule | string | Y | 反譯規則 |
| tier | enum | Y | `dedup/aggregate/summary/semantic` |
| created_at | datetime | Y | 建立時間 |

### 3.2 CompressionStepResult

| Field | Type | Required | Description |
|---|---|---|---|
| run_id | string | Y | 關聯 run |
| step | enum | Y | `dedup/aggregate/summary/semantic` |
| input_count | int | Y | 輸入事件數 |
| output_count | int | Y | 輸出事件數 |
| lossless | boolean | Y | 是否保持證據可逆 |
| roundtrip_ok | boolean | Y | 反譯是否通過 |

## 4. Workflow Domain

### 4.1 WorkflowDefinition

| Field | Type | Required | Description |
|---|---|---|---|
| workflow_id | string | Y | 工作流 ID |
| version | string | Y | 版本 |
| name | string | Y | 顯示名稱 |
| trigger | string | Y | 觸發條件 |
| steps | array<object> | Y | 步驟清單 |
| guards | array<object> | N | 守門條件 |
| outputs | array<string> | Y | 預期輸出 |

### 4.2 WorkflowRun

| Field | Type | Required | Description |
|---|---|---|---|
| workflow_run_id | string | Y | 執行 ID |
| workflow_id | string | Y | 工作流 ID |
| run_id | string | Y | 關聯 project run |
| status | enum | Y | `running/success/blocked/failed` |
| blocked_reason | string | N | 阻塞原因 |
| started_at | datetime | Y | 啟動時間 |
| finished_at | datetime | N | 完成時間 |

## 5. Analysis Domain

### 5.1 EvidenceRecord

| Field | Type | Required | Description |
|---|---|---|---|
| evidence_id | string | Y | 證據 ID |
| run_id | string | Y | 關聯 run |
| agent_id | string | Y | 來源代理 |
| claim | string | Y | 主張 |
| confidence | number | Y | 信心分數 |
| refs | array<string> | Y | 參照鏈結 |
| conflicts | array<string> | N | 衝突證據 |

### 5.2 VetoReason

| Field | Type | Required | Description |
|---|---|---|---|
| code | string | Y | 否決碼 |
| message | string | Y | 否決訊息 |
| required_evidence | array<string> | N | 缺失證據項 |

### 5.3 ConsensusRecord

| Field | Type | Required | Description |
|---|---|---|---|
| consensus_id | string | Y | 共識 ID |
| run_id | string | Y | 關聯 run |
| topic | string | Y | 收斂主題 |
| winning_claim | string | N | 最終主張 |
| weighted_score | number | N | 收斂分數 |
| evidence_refs | array<string> | Y | 支持證據 |
| dissenting_claims | array<object> | N | 異議清單 |
| vetoed | boolean | Y | 是否否決 |
| veto_reasons | array<object> | N | 否決原因 |

### 5.4 PatchProposal

| Field | Type | Required | Description |
|---|---|---|---|
| proposal_id | string | Y | 建議 ID |
| run_id | string | Y | 關聯 run |
| summary | string | Y | 修正摘要 |
| diff_preview | string | N | patch 片段 |
| related_consensus | string | Y | 關聯共識 |
| risk_level | enum | Y | `low/medium/high` |
| evidence_min_set | array<string> | Y | 最小證據集 |
| merge_policy | enum | Y | 固定 `manual-review-only` |

## 6. HLAPI Domain

### 6.1 HLAPITestCase

| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | Y | 測項 ID |
| source_file | string | Y | 來源檔案 |
| source_sheet | string | Y | 來源 sheet |
| source_row | int | Y | 來源 row |
| object_path | string | N | 物件路徑 |
| parameter_name | string | N | 參數名稱 |
| hlapi_command | string | N | 指令 |
| llapi_support | string | N | 支援狀態 |
| test_steps | string | N | 測試步驟 |
| command_output | string | N | 輸出摘要 |
| result_status | enum | N | `pass/fail/not-supported/skip/unknown` |
| comment | string | N | 備註 |

### 6.2 HLAPIDiscoveryRecord

| Field | Type | Required | Description |
|---|---|---|---|
| discovery_id | string | Y | 探勘 ID |
| run_id | string | Y | 關聯 run |
| target_id | string | Y | 關聯 target |
| collected_at | datetime | Y | 探勘時間 |
| collector | string | Y | 探勘來源 |
| object_path | string | Y | 發現路徑 |
| parameter_name | string | N | 發現參數 |
| access_mode | enum | Y | `read/write/rw` |
| probe_command | string | Y | 探測命令 |
| support_state | enum | Y | `supported/partial/not-supported/unknown` |
| evidence_refs | array<string> | N | 證據關聯 |

## 7. Relationships

- `ProjectRun (1) -> (N) TraceEvent`
- `ProjectRun (1) -> (N) WorkflowRun`
- `ProjectRun (1) -> (N) EvidenceRecord`
- `ProjectRun (1) -> (N) ConsensusRecord`
- `ProjectRun (1) -> (N) MemoryRecord`
- `MemoryRecord (candidate) (1) -> (N) MemoryPromotionDecision`
- `ConsensusRecord (1) -> (N) PatchProposal`
- `TraceEvent (N) <-> (N) CompressionLexiconEntry`
- `HLAPITestCase (N) <-> (N) TraceEvent`

## 8. Validation Rules

1. 插件不可直接寫入 `ProjectRun.state` 與 `MemoryRecord(memory_tier=long)`。
2. `PatchProposal.merge_policy` 必須固定 `manual-review-only`。
3. `MemoryPromotionDecision.approved=true` 必須同時滿足：
   - `repro_count >= 2`
   - `consensus_score >= threshold`
4. `CompressionStepResult.roundtrip_ok` 必須為 true 才能進入下一步分析。
5. veto 發生時 `ConsensusRecord.winning_claim` 可為空，但 `veto_reasons` 不可空。
6. `HLAPITestCase` 必須保留 file/sheet/row lineage 欄位。

## 9. Obsidian Mapping

- Run note: `vault/<project>/<run_id>/notes/run-summary.md`
- Root cause card: `vault/<project>/<run_id>/notes/root-cause/<consensus_id>.md`
- Trace index: `vault/<project>/<run_id>/notes/trace-index.md`
- Long memory: `vault/<project>/knowledge/long-memory/*.md`
- Assets: `vault/<project>/<run_id>/assets/*`
- Machine index: `vault/<project>/<run_id>/index/*.json`

每個 note 必須包含：`run_id`, `target_id`, `phase`, `links`, `created_at`。
