# Quickstart: IntelliDbgKit PI Core Debug Hub

## 1) Prerequisites

- Host: `python3`, `jq`, `git`, `serialwrap`, `gdb`, `bpftrace`
- Target: `ubus-cli` + 可用 TraceZone
- 測試資料: `docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx`

## 2) Environment

```bash
export IDK_PROJECT="IntelliDbgKit"
export IDK_VAULT="/path/to/obsidian_vault"
export IDK_TARGET="board-01"
```

## 3) Tool Catalog（Phase 1A 現況）

```bash
python3 -m src.cli.main tools list
python3 -m src.cli.main tools show hlapi.ingest
python3 -m src.cli.main tools doctor
```

Expected:

- 可列出工具 `description/examples/help`
- 可顯示工具健康狀態 `healthy/degraded/blocked`
- 可確認 alias 與 wrapper 映射資訊

## 4) Import HLAPI Baseline

```bash
python3 -m src.cli.commands.hlapi_ingest \
  --source /home/paul_chen/IntelliDbgKit/docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx \
  --start-sheet QoS_LLAPI \
  --project "$IDK_PROJECT" \
  --vault "$IDK_VAULT"
```

Expected:

- testcase notes + lineage index
- source row 保留

## 4.1) Minimal HLAPI Discovery Prototype

```bash
python3 -m src.cli.commands.hlapi_discovery \
  --run-id run-sample \
  --target-id "$IDK_TARGET" \
  --input /tmp/idk-discovery-input.txt \
  --output /tmp/idk-discovery-output.json
```

## 5) Run Skill Workflows

```bash
idk workflow run trace-capture-flow --run-id <run_id>
idk workflow run root-cause-flow --run-id <run_id>
idk workflow run patch-proposal-flow --run-id <run_id>
```

> 註：`idk run start` 與完整 workflow runtime 屬後續 phase，Phase 1A 先完成 ToolCard/命令註冊核心。

## 6) Analyze Multi-Agent Consensus

```bash
idk analyze consensus --run-id <run_id> --agents codex,copilot,gemini
```

Expected:

- `consensus record`
- `dissent or veto record`

## 7) Execute Memory Promotion

```bash
idk workflow run memory-promote-flow --run-id <run_id>
```

Promotion condition:

- `repro_count >= 2`
- `consensus_score >= threshold`

## 8) Compression Roundtrip Check

```bash
idk verify compression --run-id <run_id> --roundtrip
```

## 9) Serve GUI

```bash
idk gui serve --run-id <run_id>
```

GUI minimum:

- HLAPI->LLAPI timeline
- TraceZone flow
- node drilldown to evidence

## 10) CI-safe Outputs

```bash
idk report evidence-bundle --run-id <run_id>
idk patch suggest --run-id <run_id>
```

Policy:

- Evidence bundle 必須產出
- Patch proposal 必須產出
- Auto merge 固定關閉
