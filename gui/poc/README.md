# UI POC（Mock API）

## 啟動

```bash
cd /home/paul_chen/IntelliDbgKit
make ui-poc
```

開啟 `http://localhost:8080`。

## POC 範圍

- Run 切換（`runs.json`）
- Timeline replay（phase/tool/keyword filter）
- Core block flow highlight
- Node drilldown（顯示關聯 events）
- Event detail + evidence 顯示
- HLAPI Context Layer（同階 HLAPI、ODL 入口、source outline）
- Loop 折疊展開（`details/summary`）

## Mock Data

- `gui/poc/mock-data/runs.json`
- `gui/poc/mock-data/run-20260210-001.json`
- `gui/poc/mock-data/run-20260210-002.json`
- `gui/poc/mock-data/hlapi-context.json`

## Mock API 對應

- `listRuns()`
- `getRun(runId)`
- `getGraph(runId)`
- `getTimeline(runId, filters)`
- `getEventDetail(runId, eventId)`
- `getNodeDetail(runId, nodeId)`
- `getHlapiContext()`
- `getPathContext(path)`

實作位置：`gui/poc/mock-api.js`

## 參考來源

- compile_commands: `/home/paul_chen/arc_prj/compile_commands/PR65BE4445B-S-ZA-1b5d4586.json`
- ODL:
  - `/home/paul_chen/arc_prj/att-prpl/targets/968375GWO_WL25DX_WLMLO_OPENWRT_PRPL_FASTMCASTD/fs/etc/amx/wld/wld_accesspoint.odl`
  - `/home/paul_chen/arc_prj/att-prpl/targets/968375GWO_WL25DX_WLMLO_OPENWRT_PRPL_FASTMCASTD/fs/etc/amx/wld/wld_radio.odl`
