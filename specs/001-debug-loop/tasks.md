# Tasks: IntelliDbgKit PI Core Debug Hub

**Input**: Design documents from `specs/001-debug-loop/`  
**Prerequisites**: `spec.md`, `plan.md`, `data-model.md`, `research.md`, `contracts/`  
**Tests**: 每個 phase 均需包含 contract/integration 測試。  
**Organization**: 依核心能力分 phase；避免插件跨邊界直寫。

## Format: `[ID] [P?] [Domain] Description`

- **[P]**: 可平行執行。
- **[Domain]**: `BOOT/CORE/MEM/COMP/WF/AGENT/GUI/HLAPI/CI`。

---

## Phase 0: Repository Bootstrap

- [x] T000 [BOOT] 建立 `src/`, `tests/`, `gui/` 基本目錄。
- [x] T000A [BOOT] 建立 Python 測試最小框架（`unittest` 可執行）。
- [x] T000B [BOOT] 匯入 `contracts/*.json` 驗證測試骨架。
- [x] T000C [BOOT] 建立開發用 `Makefile` 或等價命令入口。
- [ ] T000D [P] [BOOT] CI 加入 contract/schema syntax 檢查。

**Checkpoint**: 可在空實作狀態執行最小測試與 schema 驗證。

---

## Phase 1: PI Core Boundary

- [x] T001 [CORE] 建立 PI core 目錄與邊界守衛：`src/core/`
- [x] T002 [CORE] 實作 `state_machine.py` 與轉移審計。
- [x] T003 [CORE] 實作 `event_bus.py` 與 schema 驗證入口。
- [x] T004 [CORE] 實作 `veto_gate.py` 基礎判斷器。
- [x] T005 [P] [CORE] Contract test：`tests/contract/test_event_schema.py`
- [x] T006 [P] [CORE] Integration test：`tests/integration/test_core_boundary_guard.py`

**Checkpoint**: 插件不能直接寫入 core state。

---

## Phase 1A: CLI ToolCard Core

- [x] T006A [CORE] 建立 `src/cli/tool_card.py`（description/examples/help 契約）。
- [x] T006B [CORE] 建立 `src/cli/command_registry.py`（命令註冊、alias 映射、health 狀態）。
- [x] T006C [CORE] 建立 `src/cli/main.py`（`idk tools list/show/doctor` 最小可用）。
- [x] T006D [P] [CORE] 整合既有 `hlapi_ingest`、`hlapi_discovery` 到同一命令目錄。
- [x] T006E [P] [CORE] Unit test：`tests/unit/test_cli_tool_registry.py`
- [x] T006F [P] [CORE] Integration test：`tests/integration/test_cli_tools_commands.py`

**Checkpoint**: 所有已註冊工具皆可透過 `description/examples/help` 被 Agent 與人類一致調用。

---

## Phase 2: Memory Lifecycle

- [ ] T007 [MEM] 實作 `memory_store.py`（raw/working/candidate/long）。
- [ ] T008 [MEM] 實作 `promotion_engine.py`（雙條件升級）。
- [ ] T009 [MEM] 實作 long-memory 寫入與回鏈索引。
- [ ] T010 [P] [MEM] Contract test：`tests/contract/test_memory_promotion_schema.py`
- [ ] T011 [P] [MEM] Integration test：`tests/integration/test_memory_promotion_gate.py`

**Checkpoint**: 未達雙條件不得升級 long-memory。

---

## Phase 3: Compression and Lexicon

- [ ] T012 [COMP] 實作四層壓縮流程：`src/memory/compression_codec.py`
- [ ] T013 [COMP] 實作語意壓縮查表：`src/memory/lexicon.py`
- [ ] T014 [COMP] 實作反譯流程與 round-trip 驗證。
- [ ] T015 [P] [COMP] Contract test：`tests/contract/test_compression_lexicon_schema.py`
- [ ] T016 [P] [COMP] Integration test：`tests/integration/test_compression_roundtrip.py`

**Checkpoint**: 壓縮後可反譯且保留證據索引。

---

## Phase 4: Workflow and Skill Runtime

- [ ] T017 [WF] 實作 `workflow_runtime.py`。
- [ ] T018 [WF] 新增 flows：`trace-capture`, `root-cause`, `patch-proposal`, `patch-verify`, `memory-promote`。
- [ ] T019 [WF] 實作 guard/block 機制與 blocked report。
- [ ] T020 [P] [WF] Contract test：`tests/contract/test_workflow_schema.py`
- [ ] T021 [P] [WF] Integration test：`tests/integration/test_workflow_blocking.py`

**Checkpoint**: speckit 工具能力可作為 skill/workflow 一級調度。

---

## Phase 5: Multi-Agent Consensus and Veto

- [ ] T022 [AGENT] 實作 agent dispatcher：`src/core/agent_dispatcher.py`
- [ ] T023 [AGENT] 實作 weighted consensus：`src/core/consensus_engine.py`
- [ ] T024 [AGENT] 實作 veto reason 與補觀測建議。
- [ ] T025 [P] [AGENT] Unit test：`tests/unit/test_consensus_scoring.py`
- [ ] T026 [P] [AGENT] Integration test：`tests/integration/test_consensus_veto_path.py`

**Checkpoint**: 缺關鍵證據時必須 veto，不得輸出假確定結論。

---

## Phase 6: Debug Stack and HLAPI Ingestion

- [ ] T027 [HLAPI] TraceZone/UART/GDB/eBPF collector 接入。
- [x] T028 [HLAPI] `xlsx_loader.py` 與 `hlapi_writer.py` 正規化匯入。
- [x] T029 [HLAPI] HLAPI discovery 最小原型接入。
- [x] T030 [P] [HLAPI] Unit test：`tests/unit/test_xlsx_to_markdown_mapping.py`
- [x] T031 [P] [HLAPI] Integration test：`tests/integration/test_hlapi_discovery_minimal.py`

**Checkpoint**: `QoS_LLAPI` 起各 sheet 可完整匯入並保留 lineage。

---

## Phase 7: GUI Timeline and Drilldown

- [ ] T032 [GUI] 實作 timeline feed API。
- [ ] T033 [GUI] 實作 graph/drilldown API。
- [ ] T034 [GUI] GUI 顯示 HLAPI->LLAPI->TraceZone flow。
- [x] T032A [GUI] POC: timeline feed mock API：`gui/poc/mock-api.js`
- [x] T033A [GUI] POC: graph/drilldown mock API：`gui/poc/app.js`
- [x] T034A [GUI] POC: HLAPI->LLAPI->Trace flow 回放：`gui/poc/index.html`
- [x] T034B [GUI] POC: HLAPI 同階欄位展開（Security siblings）：`gui/poc/mock-data/hlapi-context.json`
- [x] T034C [GUI] POC: ODL->source 同級語句與 loop 折疊：`gui/poc/app.js`
- [ ] T035 [P] [GUI] Integration test：`gui/tests/timeline_replay.spec.ts`
- [ ] T036 [P] [GUI] Integration test：`gui/tests/node_drilldown.spec.ts`

**Checkpoint**: GUI 可回鏈 evidence/consensus/obsidian note。

---

## Phase 8: CI Evidence Delivery

- [ ] T037 [CI] 產生 evidence bundle：`src/report/evidence_bundle.py`
- [ ] T038 [CI] 產生 patch proposal：`src/report/patch_proposal.py`
- [ ] T039 [CI] CI workflow 僅輸出 proposal，不執行 merge。
- [ ] T040 [P] [CI] Integration test：`tests/integration/test_ci_delivery_policy.py`

**Checkpoint**: 每次 CI 皆輸出 evidence bundle + patch proposal，auto-merge 固定 0。

---

## Dependencies and Execution Order

1. Phase 0 完成前，不可開始其他 phase。
2. Phase 1 完成前，不可開始 Phase 4~8。
3. Phase 2 與 Phase 3 可平行，但 Phase 4 需依賴兩者。
4. Phase 5 依賴 Phase 1 + Phase 4。
5. Phase 6 依賴 Phase 1；Phase 7 依賴 Phase 1 + Phase 6。
6. Phase 8 依賴 Phase 5 + Phase 6。

## Current Sprint (Start Now)

- [ ] S1-1 完成 T000~T000D（bootstrap 與測試骨架）。
- [x] S1-2 完成 T001、T003（core boundary + event bus 最小實作）。
- [x] S1-3 完成 T005、T006（contract + boundary integration tests）。
- [ ] S1-4 產出第一版 run artifact（最小 `TraceEvent` 流）。
- [x] S1-5 完成 T006A~T006F（CLI ToolCard Core）。
