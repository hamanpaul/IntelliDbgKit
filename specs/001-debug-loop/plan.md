# Implementation Plan: IntelliDbgKit Debug-Observe Core

**Branch**: `001-debug-loop` | **Date**: 2026-02-09 | **Spec**: `specs/001-debug-loop/spec.md`  
**Input**: Feature specification from `specs/001-debug-loop/spec.md`

## Summary

建立以 `Core Orchestrator + Unified Event Bus + Plugin Runtime` 為主體的除錯平台。  
Phase 1 以 TraceZone-first 搭配 UART/GDB/eBPF 完成 CLI 閉環；同步定義 GUI 回放介面、Obsidian 原生知識結構與 HLAPI 測試資料匯入/探勘模型。  
CI 僅輸出 evidence bundle 與 patch proposal，不自動 merge。

## Technical Context

**Language/Version**: Python 3.12（core/orchestrator/adapter）、TypeScript（GUI）  
**Primary Dependencies**: serialwrap, ubus-cli, gdb, bpftrace/libbpf, cscope/LSP backend, Copilot SDK  
**Storage**: Obsidian vault markdown + JSON index + JSONL raw events + Parquet aggregates  
**Testing**: pytest（unit/integration/contract）+ replay consistency checks + schema validation  
**Target Platform**: Host（Ubuntu/WSL）+ Target（prplOS/OpenWrt board）  
**Project Type**: CLI + GUI + plugin runtime（single repository）  
**Performance Goals**: 單次閉環分析（P1 case）15 分鐘內完成；GUI 節點下鑽 2 秒內回應  
**Constraints**: 行為/控制流一致性 100%；統計項允許 >=80%；不自動 merge；敏感資訊需遮罩  
**Scale/Scope**: 先支援單 board/單測項閉環，後續擴展多 board 與多 agent 協同

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Gate-1（可追溯性）: 所有結論必須能追溯至 `TraceEvent -> EvidenceRecord -> ConsensusRecord`，**PASS**。
- Gate-2（介面治理）: 只允許統一事件匯流排與 `CommandIntent` 對外，**PASS**。
- Gate-3（安全邊界）: CI 禁止自動 merge，敏感欄位遮罩，**PASS**。
- Gate-4（可擴充性）: 外部工具差異由 wrapper/adapter 吸收，**PASS**。
- Gate-5（知識持久化）: Obsidian 為原生主儲存而非後置匯出，**PASS**。

## Project Structure

### Documentation (this feature)

```text
specs/001-debug-loop/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── contracts/
│   ├── event-schema.json
│   ├── plugin-manifest.schema.json
│   ├── hlapi-discovery.schema.json
│   └── hlapi-testcase.schema.json
├── testing/
│   └── hlapi-markdown-normalization.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── orchestrator/
│   ├── state_machine.py
│   ├── consensus_engine.py
│   └── run_controller.py
├── bus/
│   ├── event_bus.py
│   └── schemas/
├── adapters/
│   ├── command_intent.py
│   ├── uart_adapter.py
│   ├── ssh_adapter.py
│   ├── adb_adapter.py
│   └── telnet_adapter.py
├── plugins/
│   ├── tracezone_collector/
│   ├── uart_collector/
│   ├── gdb_collector/
│   ├── ebpf_collector/
│   └── hlapi_discovery/
├── ingestion/
│   ├── xlsx_loader.py
│   └── hlapi_markdown_writer.py
├── knowledge/
│   ├── vault_writer.py
│   ├── backlink_indexer.py
│   └── masking.py
├── report/
│   ├── root_cause_card.py
│   └── patch_proposal.py
└── cli/
    ├── main.py
    └── commands/

gui/
├── src/
│   ├── timeline/
│   ├── graph/
│   ├── drilldown/
│   └── api/
└── tests/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: 以單一 repository 管理 CLI/GUI/collector/adapters，透過 shared schema 降低跨模組漂移；Obsidian 內容視為 runtime artifact，不放入程式碼子目錄。

## Phase 0: Research Focus

1. 分層一致性門檻定義（行為/控制流/統計）與誤判成本分析。
2. TraceZone-first 與 GDB/eBPF 補強策略。
3. CommandIntent 通用語意與 provider mapping 規則。
4. Obsidian 原生關聯（note/backlink/index）一致性治理。
5. 多 Agent（Copilot SDK）結構化證據交換協議。

## Phase 1: Design & Contracts

1. 固化事件 schema、plugin manifest、HLAPI discovery schema、HLAPI testcase schema。
2. 完成 data model 關聯（run/trace/source map/evidence/consensus/patch）。
3. 定義 xlsx -> markdown 正規化與 lineage 保留規則。
4. 定義 GUI 初期資料 API（HLAPI->LLAPI + TraceZone flow + drilldown）。
5. 定義 CI evidence bundle 內容與輸出格式。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 多工具 wrapper 層 | 外部工具介面不一致且參數差異大 | 直接在核心呼叫工具會造成耦合與不可維護 |
| 多 Agent 共識流程 | 降低單模型誤判風險 | 單代理結論缺乏交叉驗證與異議可追溯 |
