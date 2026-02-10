# Quickstart: IntelliDbgKit Debug-Observe Core

## 1) Prerequisites

- Host 端可使用：`python3`, `jq`, `git`, `serialwrap`, `gdb`, `bpftrace`。
- Target 端可使用：`ubus-cli`，且可取得 TraceZone log。
- 測試資料來源：`docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx`。

## 2) Workspace Variables

```bash
export IDK_PROJECT="IntelliDbgKit"
export IDK_VAULT="/path/to/obsidian_vault"
export IDK_TARGET="board-01"
```

## 3) Initialize Run (CLI-first)

```bash
idk run start \
  --project "$IDK_PROJECT" \
  --target "$IDK_TARGET" \
  --collectors tracezone,uart,gdb,ebpf \
  --phase TEST_LOOP
```

Expected artifacts:

- `vault/<project>/<run>/notes/run-summary.md`
- `vault/<project>/<run>/assets/events.raw.jsonl`
- `vault/<project>/<run>/index/run.json`

## 4) Import HLAPI Testcases from XLSX

```bash
idk ingest hlapi-xlsx \
  --source docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx \
  --start-sheet QoS_LLAPI \
  --vault "$IDK_VAULT" \
  --project "$IDK_PROJECT"
```

Expected artifacts:

- `vault/<project>/<run>/notes/testcases/<sheet>.md`
- `vault/<project>/<run>/index/hlapi-testcases.json`
- 每筆測項含 `source_sheet/source_row` lineage。

## 5) Execute One P1 Test Case

```bash
idk test run \
  --run-id <run_id> \
  --case-id <hlapi_case_id> \
  --provider uart \
  --command-mode intent
```

## 6) Analyze and Build Consensus

```bash
idk analyze root-cause --run-id <run_id>
idk analyze consensus --run-id <run_id> --agents codex,copilot,gemini
```

Expected outputs:

- `root-cause card`
- `consensus record`
- `dissent records`（如有）

## 7) Generate Patch Proposal (No Auto-Merge)

```bash
idk patch suggest --run-id <run_id> --output vault
```

Expected outputs:

- `vault/<project>/<run>/notes/patch-proposal.md`
- `vault/<project>/<run>/index/evidence-bundle.json`

## 8) Replay in GUI

```bash
idk gui serve --run-id <run_id>
```

GUI minimum view:

- HLAPI→LLAPI 時序
- TraceZone func flow
- 節點下鑽（symbol/source/evidence）

## 9) Minimal HLAPI Discovery Prototype

```bash
idk discover hlapi \
  --run-id <run_id> \
  --target "$IDK_TARGET" \
  --provider uart \
  --object-prefix Device.
```

Expected outputs:

- 新增 `HLAPIDiscoveryRecord`
- 回填到 testcase/索引關聯

## 10) Consistency Check

```bash
idk verify consistency --run-id <run_id>
```

Pass criteria:

- 行為結果：100%
- 控制流拓樸：100%
- 統計類指標：>=80%
