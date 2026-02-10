# Tasks: IntelliDbgKit Debug-Observe Core

**Input**: Design documents from `specs/001-debug-loop/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`  
**Tests**: 必須包含 contract/integration 測試，驗證閉環與一致性門檻。  
**Organization**: 依 user story 分組，確保可獨立交付。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行。
- **[Story]**: `US1/US2/US3/US4/US5`。

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 建立核心目錄骨架：`src/orchestrator`, `src/bus`, `src/adapters`, `src/plugins`, `src/knowledge`, `src/ingestion`, `src/cli`
- [ ] T002 建立 GUI 骨架：`gui/src/timeline`, `gui/src/graph`, `gui/src/drilldown`, `gui/src/api`
- [ ] T003 [P] 建立測試骨架：`tests/unit`, `tests/contract`, `tests/integration`
- [ ] T004 [P] 建立 schema 載入與驗證框架：`src/bus/schema_registry.py`

---

## Phase 2: Foundational (Blocking)

- [ ] T005 實作 `TraceEvent` schema 驗證器：`src/bus/validators.py`
- [ ] T006 實作 `CommandIntent/ExecResult` 基礎型別：`src/adapters/command_intent.py`
- [ ] T007 實作 plugin manifest 註冊與相容檢查：`src/plugins/registry.py`
- [ ] T008 實作 run 狀態機：`src/orchestrator/state_machine.py`
- [ ] T009 實作 artifact writer（vault + index）：`src/knowledge/vault_writer.py`
- [ ] T010 建立敏感資訊遮罩器：`src/knowledge/masking.py`
- [ ] T011 [P] Contract test：`tests/contract/test_event_schema.py`
- [ ] T012 [P] Contract test：`tests/contract/test_plugin_manifest.py`

**Checkpoint**: T005~T012 完成後才能進入 user story 實作。

---

## Phase 3: User Story 1 - CLI 除錯閉環 (Priority: P1) 🎯 MVP

**Goal**: 完成單次 run 的收集、分析、報告與 patch 建議閉環。

**Independent Test**: 執行單一 HLAPI 測項，產生 run summary + root-cause + patch proposal。

### Tests for User Story 1

- [ ] T013 [P] [US1] Integration test：`tests/integration/test_cli_debug_loop.py`
- [ ] T014 [P] [US1] Integration test：`tests/integration/test_state_machine_transitions.py`

### Implementation for User Story 1

- [ ] T015 [US1] 實作 run controller：`src/orchestrator/run_controller.py`
- [ ] T016 [US1] 實作 CLI 命令 `run/test/analyze/patch/report`：`src/cli/commands/*.py`
- [ ] T017 [US1] 實作 TraceZone collector：`src/plugins/tracezone_collector/collector.py`
- [ ] T018 [US1] 實作 UART(serialwrap) collector：`src/plugins/uart_collector/collector.py`
- [ ] T019 [US1] 實作 GDB collector：`src/plugins/gdb_collector/collector.py`
- [ ] T020 [US1] 實作 eBPF collector：`src/plugins/ebpf_collector/collector.py`
- [ ] T021 [US1] 實作 root-cause 卡片輸出：`src/report/root_cause_card.py`
- [ ] T022 [US1] 實作 patch proposal 生成：`src/report/patch_proposal.py`

---

## Phase 4: User Story 2 - Wrapper/Adapter 統一介面 (Priority: P1)

**Goal**: 以單一 `CommandIntent` 介面統一多 provider 執行邏輯。

**Independent Test**: 相同 intent 可在 UART 與 SSH provider 取得一致語意結果。

### Tests for User Story 2

- [ ] T023 [P] [US2] Contract test：`tests/contract/test_command_intent_schema.py`
- [ ] T024 [P] [US2] Integration test：`tests/integration/test_provider_mapping.py`

### Implementation for User Story 2

- [ ] T025 [US2] 實作 adapter base：`src/adapters/base.py`
- [ ] T026 [P] [US2] 實作 `uart_adapter.py`
- [ ] T027 [P] [US2] 實作 `ssh_adapter.py`
- [ ] T028 [P] [US2] 實作 `adb_adapter.py`
- [ ] T029 [P] [US2] 實作 `telnet_adapter.py`
- [ ] T030 [US2] 實作 provider capability matrix：`src/adapters/capability_matrix.py`

---

## Phase 5: User Story 3 - GUI 回放與下鑽 (Priority: P2)

**Goal**: 提供 HLAPI→LLAPI + TraceZone flow 回放與節點下鑽。

**Independent Test**: GUI 可對單次 run 進行時間線播放並顯示節點關聯證據。

### Tests for User Story 3

- [ ] T031 [P] [US3] Integration test：`gui/tests/timeline_replay.spec.ts`
- [ ] T032 [P] [US3] Integration test：`gui/tests/node_drilldown.spec.ts`

### Implementation for User Story 3

- [ ] T033 [US3] 實作 timeline feed API：`src/orchestrator/api_timeline.py`
- [ ] T034 [US3] 實作 graph/drilldown API：`src/orchestrator/api_graph.py`
- [ ] T035 [US3] GUI timeline 元件：`gui/src/timeline/*`
- [ ] T036 [US3] GUI graph + drilldown 元件：`gui/src/graph/*`, `gui/src/drilldown/*`

---

## Phase 6: User Story 4 - HLAPI 測試匯入與 Discovery 原型 (Priority: P2)

**Goal**: 將 xlsx 轉成 markdown/index，並完成 target 自動 discovery 最小原型。

**Independent Test**: 指定 xlsx 轉換成功；discovery 新增記錄可回鏈到 run。

### Tests for User Story 4

- [ ] T037 [P] [US4] Unit test：`tests/unit/test_xlsx_to_markdown_mapping.py`
- [ ] T038 [P] [US4] Integration test：`tests/integration/test_hlapi_discovery_minimal.py`

### Implementation for User Story 4

- [ ] T039 [US4] 實作 xlsx 載入器：`src/ingestion/xlsx_loader.py`
- [ ] T040 [US4] 實作 markdown 寫入器：`src/ingestion/hlapi_markdown_writer.py`
- [ ] T041 [US4] 實作 discovery collector：`src/plugins/hlapi_discovery/collector.py`
- [ ] T042 [US4] 實作 lineage indexer：`src/knowledge/lineage_indexer.py`

---

## Phase 7: User Story 5 - 多 Agent 共識分析 (Priority: P3)

**Goal**: 主控代理平行調度多代理並輸出共識與異議。

**Independent Test**: 兩組衝突證據可收斂並保留 dissent。

### Tests for User Story 5

- [ ] T043 [P] [US5] Unit test：`tests/unit/test_consensus_scoring.py`
- [ ] T044 [P] [US5] Integration test：`tests/integration/test_multi_agent_consensus.py`

### Implementation for User Story 5

- [ ] T045 [US5] 實作多代理 dispatcher：`src/orchestrator/agent_dispatcher.py`
- [ ] T046 [US5] 實作共識引擎：`src/orchestrator/consensus_engine.py`
- [ ] T047 [US5] 實作證據交換結構：`src/orchestrator/evidence_bus.py`

---

## Phase 8: Polish & CI Integration

- [ ] T048 建立 evidence bundle 輸出：`src/report/evidence_bundle.py`
- [ ] T049 建立 CI job 範本（僅 patch proposal）：`.github/workflows/idk-debug-loop.yml`
- [ ] T050 更新文件：`specs/001-debug-loop/quickstart.md`, `docs/`
- [ ] T051 一致性驗證工具：`src/orchestrator/consistency_checker.py`

## Dependencies & Execution Order

- `Phase 1 -> Phase 2` 完成前，禁止進入任何 User Story。
- US1 與 US2 完成後可平行展開 US3/US4。
- US5 依賴 US1（事件/證據）與 US2（協調介面）。
- Polish 階段依賴所有目標 story 完成。
