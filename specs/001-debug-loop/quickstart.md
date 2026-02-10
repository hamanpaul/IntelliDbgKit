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

## 3) Start a Run

```bash
idk run start \
  --project "$IDK_PROJECT" \
  --target "$IDK_TARGET" \
  --collectors tracezone,uart,gdb,ebpf
```

Expected:

- `vault/<project>/<run>/notes/run-summary.md`
- `vault/<project>/<run>/assets/events.raw.jsonl`
- `vault/<project>/<run>/index/run.json`

## 4) Import HLAPI Baseline

```bash
idk ingest hlapi-xlsx \
  --source docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx \
  --start-sheet QoS_LLAPI \
  --project "$IDK_PROJECT" \
  --vault "$IDK_VAULT"
```

Expected:

- testcase notes + lineage index
- source row 保留

## 5) Run Skill Workflows

```bash
idk workflow run trace-capture-flow --run-id <run_id>
idk workflow run root-cause-flow --run-id <run_id>
idk workflow run patch-proposal-flow --run-id <run_id>
```

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
