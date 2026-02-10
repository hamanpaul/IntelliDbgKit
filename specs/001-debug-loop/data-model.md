# Data Model: IntelliDbgKit Debug-Observe Core

## 1. Core Entities

### 1.1 ProjectRun

| Field | Type | Required | Description |
|---|---|---|---|
| run_id | string | Y | 單次執行唯一 ID |
| project_name | string | Y | 專案名稱（對應 vault 第一層） |
| target_id | string | Y | 測試目標板識別 |
| started_at | datetime | Y | 啟動時間 |
| finished_at | datetime | N | 結束時間 |
| state | enum | Y | 當前狀態機節點 |
| trigger | string | Y | 測試觸發來源 |
| summary_note | string | N | 對應 Obsidian run 摘要路徑 |

**State enum**: `BOOTSTRAP, TEST_LOOP, MONITOR, DETECT, CONDITION_ANALYSIS, REPRODUCE, DEBUG_ON, ANALYZE, ADV_TOOL_DECISION, AUTO_ACTION, REPRO_TRACE, RUNTIME_PATCH_TEST, REPORT, FAILED`

### 1.2 TraceEvent

| Field | Type | Required | Description |
|---|---|---|---|
| event_id | string | Y | 事件唯一 ID |
| run_id | string | Y | 關聯 run |
| ts_ns | int64 | Y | 奈秒時間戳 |
| phase | enum | Y | 所屬流程階段 |
| source | enum | Y | `host` 或 `target` |
| tool | string | Y | tracezone/gdb/ebpf/uart/... |
| target_id | string | Y | 來源 target |
| symbol | string | N | 關聯符號 |
| address | string | N | 位址（hex） |
| severity | enum | Y | `info/warn/error/critical` |
| payload | object | Y | 工具原始/正規化內容 |
| links | array | N | 關聯 event/evidence/note |

### 1.3 CommandIntent

| Field | Type | Required | Description |
|---|---|---|---|
| intent_id | string | Y | 命令語意 ID |
| action | string | Y | 語意動作（例: set_param, query_param） |
| object_path | string | N | TR-181/DM 目標 |
| parameter | string | N | 參數名 |
| value | string/number/bool | N | 欲設定值 |
| constraints | object | N | 執行條件（timeout/retry/provider scope） |
| preferred_provider | string | N | 建議 provider |

### 1.4 ExecResult

| Field | Type | Required | Description |
|---|---|---|---|
| intent_id | string | Y | 對應 CommandIntent |
| provider | enum | Y | `uart/adb/ssh/telnet/local` |
| rc | int | Y | return code |
| stdout | string | N | 標準輸出 |
| stderr | string | N | 錯誤輸出 |
| latency_ms | int | Y | 執行耗時 |
| normalized | object | N | 正規化結果 |
| error_code | string | N | 結構化錯誤碼 |

### 1.5 SourceMapNode / SourceMapEdge

**SourceMapNode**

| Field | Type | Required | Description |
|---|---|---|---|
| node_id | string | Y | 節點 ID |
| layer | enum | Y | `HLAPI/LLAPI/Driver/Kernel/Tooling` |
| symbol | string | N | 函式/符號 |
| file | string | N | 原始碼路徑 |
| line | int | N | 行號 |
| dm_path | string | N | 物件路徑 |

**SourceMapEdge**

| Field | Type | Required | Description |
|---|---|---|---|
| edge_id | string | Y | 邊 ID |
| from_node | string | Y | 起點 |
| to_node | string | Y | 終點 |
| edge_type | enum | Y | `call/state/data/bus` |
| confidence | number | Y | 0.0 - 1.0 |

### 1.6 HLAPITestCase

| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | Y | 測試案例 ID |
| source_file | string | Y | xlsx 檔案路徑 |
| source_sheet | string | Y | 來源 sheet |
| source_row | int | Y | 來源列號 |
| object_path | string | N | Object/DataModel |
| parameter_name | string | N | Parameter |
| hlapi_command | string | N | HLAPI 指令 |
| llapi_support | string | N | LLAPI 支援狀態 |
| test_steps | string | N | 測試步驟 |
| command_output | string | N | 結果輸出摘要 |
| result_status | enum | N | `pass/fail/not-supported/skip/unknown` |
| comment | string | N | 備註 |
| tags | array<string> | N | 模組/版本/板型 |

### 1.7 HLAPIDiscoveryRecord

| Field | Type | Required | Description |
|---|---|---|---|
| discovery_id | string | Y | 探勘記錄 ID |
| run_id | string | Y | 關聯 run |
| target_id | string | Y | 關聯 target |
| collected_at | datetime | Y | 探勘時間 |
| collector | string | Y | discovery provider |
| object_path | string | Y | 發現物件 |
| parameter_name | string | N | 發現參數 |
| access_mode | enum | Y | `read/write/rw` |
| probe_command | string | Y | 探測命令 |
| observed_value | string | N | 探測值 |
| support_state | enum | Y | `supported/partial/not-supported/unknown` |
| evidence_refs | array<string> | N | 追溯證據 |

### 1.8 EvidenceRecord / ConsensusRecord

**EvidenceRecord**

| Field | Type | Required | Description |
|---|---|---|---|
| evidence_id | string | Y | 證據 ID |
| run_id | string | Y | 關聯 run |
| agent_id | string | Y | 來源 agent |
| claim | string | Y | 主張 |
| confidence | number | Y | 0.0 - 1.0 |
| refs | array<string> | Y | event/note/source-map 參照 |
| conflicts | array<string> | N | 衝突 evidence |

**ConsensusRecord**

| Field | Type | Required | Description |
|---|---|---|---|
| consensus_id | string | Y | 共識 ID |
| run_id | string | Y | 關聯 run |
| topic | string | Y | 收斂主題 |
| winning_claim | string | Y | 最終結論 |
| weighted_score | number | Y | 最終分數 |
| evidence_refs | array<string> | Y | 支持證據 |
| dissenting_claims | array<object> | N | 異議列表 |

### 1.9 PatchProposal

| Field | Type | Required | Description |
|---|---|---|---|
| proposal_id | string | Y | 建議 ID |
| run_id | string | Y | 關聯 run |
| summary | string | Y | 修正摘要 |
| diff_preview | string | N | patch 片段 |
| related_consensus | string | Y | 關聯共識 |
| risk_level | enum | Y | `low/medium/high` |
| merge_policy | enum | Y | 固定為 `manual-review-only` |

## 2. Relationships

- `ProjectRun (1) -> (N) TraceEvent`
- `ProjectRun (1) -> (N) EvidenceRecord`
- `ProjectRun (1) -> (N) ConsensusRecord`
- `ProjectRun (1) -> (N) HLAPIDiscoveryRecord`
- `HLAPITestCase (N) <-> (N) SourceMapNode`（透過 object/parameter/symbol 關聯）
- `ConsensusRecord (1) -> (N) PatchProposal`
- `TraceEvent (N) <-> (N) SourceMapNode`（symbol/address/time-slice 對齊）

## 3. Validation Rules

1. 所有 `TraceEvent.run_id` 必須存在對應 `ProjectRun`。
2. `ProjectRun` 進入 `REPORT` 前，至少要有一筆 `ConsensusRecord` 或 `未收斂標記`。
3. `PatchProposal.merge_policy` 必須固定 `manual-review-only`。
4. 重製一致性驗證必須分層輸出：
   - behavior_score = 1.0
   - control_flow_score = 1.0
   - telemetry_score >= 0.8
5. `HLAPITestCase` 必須保留 `source_file/source_sheet/source_row` lineage 欄位。
6. `EvidenceRecord.refs` 至少 1 條且需可解析到既有 artifact。

## 4. Obsidian Mapping

- Run note: `vault/<project>/<run_id>/notes/run-summary.md`
- Root cause card: `vault/<project>/<run_id>/notes/root-cause/<consensus_id>.md`
- Trace index: `vault/<project>/<run_id>/notes/trace-index.md`
- Assets: `vault/<project>/<run_id>/assets/*`
- Machine index: `vault/<project>/<run_id>/index/*.json`

每個 note 必須包含至少以下 metadata：`run_id`, `target_id`, `phase`, `links`, `created_at`。

## 5. State Transitions

1. `BOOTSTRAP -> TEST_LOOP`: 環境與 collector 初始化成功。
2. `TEST_LOOP -> MONITOR`: 測試啟動後開始監控。
3. `MONITOR -> DETECT`: 偵測到異常或測試失敗。
4. `DETECT -> CONDITION_ANALYSIS`: 梳理觸發條件與復現前置。
5. `CONDITION_ANALYSIS -> REPRODUCE`: 啟動穩定重製。
6. `REPRODUCE -> DEBUG_ON`: 達到重製條件後開啟除錯工具。
7. `DEBUG_ON -> ANALYZE`: 完成資料採集進入分析。
8. `ANALYZE -> ADV_TOOL_DECISION`: 判斷是否升級工具層。
9. `ADV_TOOL_DECISION -> AUTO_ACTION`: 執行 auto-build/upgrade/connect。
10. `AUTO_ACTION -> REPRO_TRACE`: 修正後重製追蹤。
11. `REPRO_TRACE -> RUNTIME_PATCH_TEST`: 進行 runtime 改值驗證。
12. `RUNTIME_PATCH_TEST -> REPORT`: 產生結論、證據包與 patch proposal。
