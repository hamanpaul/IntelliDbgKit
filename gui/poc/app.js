import { MockDebugApi } from "./mock-api.js";

const api = new MockDebugApi();

const timelineEl = document.getElementById("timeline");
const detailsEl = document.getElementById("details");
const graphEl = document.getElementById("graph");
const hintEl = document.getElementById("graphHint");
const statsEl = document.getElementById("timelineStats");
const tpl = document.getElementById("timelineItemTpl");

const runSelect = document.getElementById("runSelect");
const phaseSelect = document.getElementById("phaseSelect");
const toolSelect = document.getElementById("toolSelect");
const searchInput = document.getElementById("searchInput");
const applyFilterBtn = document.getElementById("applyFilterBtn");

const playBtn = document.getElementById("playBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const speedSelect = document.getElementById("speedSelect");

const pathSelect = document.getElementById("pathSelect");

function newMindStore() {
  return {
    nodes: new Map(),
    itemToChild: new Map(),
    childToLink: new Map(),
    nextId: 1
  };
}

const state = {
  runs: [],
  runId: "",
  runMeta: null,
  graph: { nodes: [], edges: [] },
  timeline: [],
  activeIndex: 0,
  activeEventId: "",
  filters: {
    phase: "ALL",
    tool: "ALL",
    keyword: ""
  },
  timerId: null,
  hlapiContext: null,
  selectedPath: "",
  mind: newMindStore(),
  drag: {
    active: false,
    nodeId: "",
    offsetX: 0,
    offsetY: 0,
    clientX: 0,
    clientY: 0,
    width: 0,
    height: 0,
    lastX: 0,
    lastY: 0,
    rafId: 0
  }
};

function statusBadge(status) {
  if (status === "ok") return '<span class="badge b-ok">OK</span>';
  if (status === "warn") return '<span class="badge b-warn">WARN</span>';
  return '<span class="badge b-danger">ERR</span>';
}

function consensusBadge(consensus) {
  if (consensus === "pass") return '<span class="badge b-ok">CONSENSUS:PASS</span>';
  if (consensus === "veto") return '<span class="badge b-danger">CONSENSUS:VETO</span>';
  return '<span class="badge b-info">CONSENSUS:PENDING</span>';
}

function runBadge(status) {
  if (status === "pass") return '<span class="badge b-ok">RUN:PASS</span>';
  if (status === "warn") return '<span class="badge b-warn">RUN:WARN</span>';
  return '<span class="badge b-info">RUN:UNKNOWN</span>';
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function selectedEvent() {
  return state.timeline[state.activeIndex] || null;
}

function previousEvent() {
  if (state.activeIndex <= 0) return null;
  return state.timeline[state.activeIndex - 1] || null;
}

function selectedPathContext() {
  return (state.hlapiContext?.path_contexts || []).find((item) => item.path === state.selectedPath) || null;
}

function basename(path) {
  if (!path) return "-";
  const tokens = String(path).split("/");
  return tokens[tokens.length - 1] || path;
}

function nodeLabel(nodeId) {
  const node = state.graph.nodes.find((item) => item.id === nodeId);
  return node ? node.label : nodeId;
}

function limitItems(values, limit = 8) {
  const data = (values || []).filter(Boolean);
  if (data.length <= limit) return data;
  return [...data.slice(0, limit), `... +${data.length - limit}`];
}

function createTextItem(id, label) {
  return { id, label, expandable: false };
}

function createExpandItem(id, label, type, payload = {}) {
  return { id, label, type, payload, expandable: true };
}

function eventStepNo(eventId) {
  const index = state.timeline.findIndex((event) => event.id === eventId);
  return index >= 0 ? index + 1 : 0;
}

function formatEventTag(eventId) {
  if (!eventId) return "-";
  const step = eventStepNo(eventId);
  if (!step) return eventId;
  return `Step ${step} (${eventId})`;
}

function formatRuntimeFlowLabel(event) {
  if (!event) return "Call Flow Focus (no active event)";
  const prev = previousEvent();
  const tag = formatEventTag(event.id);
  if (!prev) return `Call Flow Focus: ${tag}`;
  return `Call Flow Focus: ${tag} (from ${formatEventTag(prev.id)})`;
}

function formatNodeList(nodeIds = []) {
  if (!nodeIds.length) return "(none)";
  return nodeIds.map((nodeId) => nodeLabel(nodeId)).join(" -> ");
}

function buildBackboneFlowNodeIds() {
  const ordered = [];
  const seen = new Set();
  state.timeline.forEach((event) => {
    (event.flow || []).forEach((nodeId) => {
      if (seen.has(nodeId)) return;
      seen.add(nodeId);
      ordered.push(nodeId);
    });
  });
  return ordered;
}

function diffFlowNodes(prevNodeIds = [], currNodeIds = []) {
  const prevSet = new Set(prevNodeIds);
  const currSet = new Set(currNodeIds);
  const entered = currNodeIds.filter((nodeId) => !prevSet.has(nodeId));
  const exited = prevNodeIds.filter((nodeId) => !currSet.has(nodeId));
  const kept = currNodeIds.filter((nodeId) => prevSet.has(nodeId));
  return { entered, exited, kept };
}

function newNodeId() {
  const id = `n${state.mind.nextId}`;
  state.mind.nextId += 1;
  return id;
}

function makeNode({ title, items, parentId, depth, kind }) {
  return {
    id: newNodeId(),
    title,
    items,
    parentId,
    depth,
    kind,
    manualPos: null,
    scrollTop: 0,
    scrollLeft: 0
  };
}

function itemLinkKey(parentId, itemId) {
  return `${parentId}::${itemId}`;
}

function clamp(value, min, max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

function estimateNodeSize(node) {
  const labels = [node.title, ...node.items.map((item) => item.label || "")];
  const maxChars = Math.max(16, ...labels.map((label) => String(label).length));
  const width = Math.round(Math.min(560, Math.max(300, 210 + maxChars * 3.2)));
  const lineCount = node.items.length + 1;
  const maxHeight = node.kind === "source" ? 620 : 500;
  const height = Math.round(Math.min(maxHeight, Math.max(112, 50 + lineCount * 24)));
  return { w: width, h: height };
}

function rectsOverlap(a, b, gap = 10) {
  if (a.x + a.w + gap <= b.x) return false;
  if (b.x + b.w + gap <= a.x) return false;
  if (a.y + a.h + gap <= b.y) return false;
  if (b.y + b.h + gap <= a.y) return false;
  return true;
}

function renderRunOptions() {
  runSelect.innerHTML = "";
  state.runs.forEach((run) => {
    const option = document.createElement("option");
    option.value = run.run_id;
    option.textContent = `${run.run_id} / ${run.target_id}`;
    runSelect.appendChild(option);
  });
  runSelect.value = state.runId;
}

function renderFilterOptions() {
  const phaseSet = new Set(["ALL"]);
  const toolSet = new Set(["ALL"]);
  state.timeline.forEach((event) => {
    phaseSet.add(event.phase);
    toolSet.add(event.tool);
  });

  phaseSelect.innerHTML = "";
  Array.from(phaseSet).forEach((phase) => {
    const option = document.createElement("option");
    option.value = phase;
    option.textContent = phase;
    phaseSelect.appendChild(option);
  });
  phaseSelect.value = state.filters.phase;

  toolSelect.innerHTML = "";
  Array.from(toolSet).forEach((tool) => {
    const option = document.createElement("option");
    option.value = tool;
    option.textContent = tool;
    toolSelect.appendChild(option);
  });
  toolSelect.value = state.filters.tool;
}

function renderTimeline() {
  timelineEl.innerHTML = "";
  state.timeline.forEach((event, index) => {
    const node = tpl.content.firstElementChild.cloneNode(true);
    const button = node.querySelector(".timeline-btn");
    node.querySelector(".time").textContent = `${event.time} / ${event.phase}`;
    node.querySelector(".title").textContent = event.title;
    node.querySelector(".meta").textContent = `${event.tool} • ${formatEventTag(event.id)}`;
    button.addEventListener("click", () => setActive(index));
    if (index === state.activeIndex) button.classList.add("active");
    timelineEl.appendChild(node);
  });
}

function renderPathOptions() {
  const paths = state.hlapiContext?.path_contexts || [];
  pathSelect.innerHTML = "";
  paths.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.path;
    option.textContent = item.path;
    pathSelect.appendChild(option);
  });
  if (!state.selectedPath && paths.length) {
    state.selectedPath = paths[0].path;
  }
  pathSelect.value = state.selectedPath;
}

function buildRootNode() {
  const context = selectedPathContext();
  const siblingItems = (context?.siblings || []).map((name) =>
    createExpandItem(`sibling:${name}`, name, "sibling", { name })
  );

  const items = [];
  if (siblingItems.length) {
    items.push(...siblingItems);
  } else {
    items.push(createTextItem("no-sibling", "(no sibling HLAPI)"));
  }

  items.push(createExpandItem("runtime-flow", "Call Flow Focus (auto expanded)", "runtime_flow"));

  if (context?.entry_function) {
    items.push(createExpandItem(`odl-entry:${context.entry_function}`, `ODL Entry: ${context.entry_function}`, "odl_entry"));
  } else if (context?.odl_file) {
    items.push(createExpandItem(`odl-file:${basename(context.odl_file)}`, `ODL File: ${basename(context.odl_file)}`, "odl_entry"));
  }

  if (context?.source_mapping?.source_function) {
    items.push(
      createExpandItem(
        `source-fn:${context.source_mapping.source_function}`,
        `Source: ${context.source_mapping.source_function}()`,
        "source_fn",
        { fn: context.source_mapping.source_function }
      )
    );
  }

  return {
    id: "root",
    title: state.selectedPath || "HLAPI Path",
    items,
    parentId: null,
    depth: 0,
    kind: "root",
    manualPos: null,
    scrollTop: 0,
    scrollLeft: 0
  };
}

function buildChildNode(parentNode, item) {
  const context = selectedPathContext();
  if (!context) return null;

  if (item.type === "sibling") {
    const peerItems = limitItems((context.siblings || []).filter((name) => name !== item.payload.name), 6).map((name) =>
      createExpandItem(`peer:${item.payload.name}:${name}`, `${name}`, "sibling", { name })
    );

    const items = [
      createTextItem(`path:${item.payload.name}`, `Path: ${state.selectedPath}`),
      createTextItem(`odl:${item.payload.name}`, `ODL: ${basename(context.odl_file)}`),
      createTextItem(`scope:${item.payload.name}`, `Scope: ${context.object_scope || context.entry_function || "-"}`)
    ];

    if (context.entry_function) {
      items.push(createExpandItem(`odl-entry:${item.payload.name}`, `ODL Entry: ${context.entry_function}`, "odl_entry"));
    }
    if (context.source_mapping?.source_function) {
      items.push(
        createExpandItem(
          `src-fn:${item.payload.name}:${context.source_mapping.source_function}`,
          `Source: ${context.source_mapping.source_function}()`,
          "source_fn",
          { fn: context.source_mapping.source_function }
        )
      );
    }
    items.push(...peerItems);

    return makeNode({
      title: `Param: ${item.payload.name}`,
      items,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      kind: "sibling"
    });
  }

  if (item.type === "odl_entry") {
    const items = [
      createTextItem("odl-file", `File: ${context.odl_file || "-"}`),
      createTextItem("odl-entry-line", `EntryLine: ${context.odl_entry_line || context.odl_line || "-"}`),
      createTextItem("odl-stats-line", `StatsLine: ${context.odl_stats_line || "-"}`),
      createTextItem("scope", `Scope: ${context.object_scope || context.entry_function || "-"}`)
    ];
    if (context.source_mapping?.source_function) {
      items.push(
        createExpandItem(
          `source-fn:${context.source_mapping.source_function}`,
          `Source: ${context.source_mapping.source_function}()`,
          "source_fn",
          { fn: context.source_mapping.source_function }
        )
      );
    }
    return makeNode({
      title: "ODL Mapping",
      items,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      kind: "odl"
    });
  }

  if (item.type === "source_fn") {
    const functionName = item.payload.fn || context.source_mapping?.source_function || "";
    let outline = [];
    if (functionName === context.source_mapping?.source_function) {
      outline = context.source_outline || [];
    } else {
      const matched = (context.sibling_functions || []).find((fn) => fn.name === functionName);
      outline = matched?.outline || [];
    }

    const items = outline.map((entry, index) => {
      if (entry.kind === "loop") {
        return createExpandItem(
          `loop:${functionName}:${index}`,
          `${entry.text}`,
          "loop",
          { children: entry.children || [] }
        );
      }
      return createTextItem(`line:${functionName}:${index}`, entry.text);
    });

    (context.sibling_functions || [])
      .filter((fn) => fn.name !== functionName)
      .slice(0, 4)
      .forEach((fn) => {
        items.push(createExpandItem(`source-fn:${fn.name}`, `Fn: ${fn.name}()`, "source_fn", { fn: fn.name }));
      });

    if (!items.length) {
      items.push(createTextItem(`no-outline:${functionName}`, "(no source outline)"));
    }

    return makeNode({
      title: `Source: ${functionName || "unknown"}`,
      items,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      kind: "source"
    });
  }

  if (item.type === "loop") {
    const loopItems = (item.payload.children || []).map((line, index) => createTextItem(`loop-line:${index}`, line));
    if (!loopItems.length) {
      loopItems.push(createTextItem("loop-empty", "(empty loop)"));
    }
    return makeNode({
      title: "Loop Expand",
      items: loopItems,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      kind: "loop"
    });
  }

  if (item.type === "runtime_flow") {
    const event = selectedEvent();
    if (!event) {
      return makeNode({
        title: "Call Flow Focus",
        items: [createTextItem("runtime-none", "(no active event)")],
        parentId: parentNode.id,
        depth: parentNode.depth + 1,
        kind: "runtime"
      });
    }

    const prev = previousEvent();
    const prevFlow = prev?.flow || [];
    const currFlow = event.flow || [];
    const diff = diffFlowNodes(prevFlow, currFlow);
    const backbone = buildBackboneFlowNodeIds();

    const items = [
      createTextItem("runtime-event", `Event: ${formatEventTag(event.id)}`),
      createTextItem("runtime-prev", `From: ${prev ? formatEventTag(prev.id) : "(start of run)"}`),
      createTextItem("runtime-phase", `Phase/Tool: ${event.phase} / ${event.tool}`)
    ];

    items.push(createTextItem("runtime-now", `Current Flow: ${formatNodeList(currFlow)}`));
    items.push(createTextItem("runtime-diff-entered", `Transition + Entered: ${formatNodeList(diff.entered)}`));
    items.push(createTextItem("runtime-diff-exited", `Transition - Exited: ${formatNodeList(diff.exited)}`));
    items.push(createTextItem("runtime-diff-kept", `Transition = Kept: ${formatNodeList(diff.kept)}`));
    items.push(createTextItem("runtime-guide", "Legend: + entered this step, - exited from previous, = continuous."));

    if (backbone.length) {
      const firstNodeId = backbone[0];
      items.push(
        createExpandItem(
          "flow-step:0",
          `Step 1: ${nodeLabel(firstNodeId)} (${firstNodeId})`,
          "flow_step",
          {
            backbone,
            index: 0
          }
        )
      );
    }

    items.push(createTextItem("backbone-title", `Backbone (${backbone.length} nodes):`));
    backbone.forEach((nodeId, index) => {
      const inCurr = currFlow.includes(nodeId);
      const inPrev = prevFlow.includes(nodeId);
      let marker = ".";
      if (inCurr && inPrev) marker = "=";
      else if (inCurr) marker = "+";
      else if (inPrev) marker = "-";
      items.push(createTextItem(`backbone-line:${event.id}:${index}`, `${marker} ${index + 1}. ${nodeLabel(nodeId)} (${nodeId})`));
    });

    return makeNode({
      title: "Call Flow Focus",
      items,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      kind: "runtime"
    });
  }

  if (item.type === "flow_step") {
    const flow = item.payload?.backbone || [];
    const index = Number(item.payload?.index || 0);
    const nodeId = flow[index];
    if (!nodeId) return null;

    const prevNodeId = index > 0 ? flow[index - 1] : null;
    const nextNodeId = index + 1 < flow.length ? flow[index + 1] : null;

    const related = state.timeline
      .filter((event) => (event.flow || []).includes(nodeId))
      .map((event) => formatEventTag(event.id))
      .join(", ");

    const items = [
      createTextItem("flow-step-node", `Node: ${nodeLabel(nodeId)} (${nodeId})`),
      createTextItem("flow-step-marker", "Focus State: color highlight (entered/kept/exited)"),
      createTextItem("flow-step-prev", `From Node: ${prevNodeId ? `${nodeLabel(prevNodeId)} (${prevNodeId})` : "(flow start)"}`),
      createTextItem("flow-step-next", `To Node: ${nextNodeId ? `${nodeLabel(nextNodeId)} (${nextNodeId})` : "(flow end)"}`),
      createTextItem("flow-step-related", `Seen In: ${related || "(none)"}`)
    ];

    if (nextNodeId) {
      items.push(
        createExpandItem(
          `flow-step:${index + 1}`,
          `Step ${index + 2}: ${nodeLabel(nextNodeId)} (${nextNodeId})`,
          "flow_step",
          {
            backbone: flow,
            index: index + 1
          }
        )
      );
    }

    const node = makeNode({
      title: `Flow Step ${index + 1}`,
      items,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      kind: "flow-step"
    });
    node.flowNodeId = nodeId;
    node.stepIndex = index;
    return node;
  }

  return null;
}

function initMindTree() {
  state.mind = newMindStore();
  const root = buildRootNode();
  state.mind.nodes.set(root.id, root);
  updateRuntimeFlowItemLabel();
  syncRuntimeFlowNode();
}

function updateRuntimeFlowItemLabel() {
  const root = state.mind.nodes.get("root");
  if (!root) return;
  const runtimeItem = root.items.find((item) => item.id === "runtime-flow");
  if (!runtimeItem) return;
  runtimeItem.label = formatRuntimeFlowLabel(selectedEvent());
}

function ensureRuntimeFlowExpanded() {
  const root = state.mind.nodes.get("root");
  if (!root) return;
  const runtimeItem = root.items.find((item) => item.id === "runtime-flow" && item.expandable);
  if (!runtimeItem) return;
  const runtimeLinkKey = itemLinkKey(root.id, runtimeItem.id);
  if (state.mind.itemToChild.has(runtimeLinkKey)) return;
  const runtimeNode = buildChildNode(root, runtimeItem);
  if (!runtimeNode) return;
  state.mind.nodes.set(runtimeNode.id, runtimeNode);
  state.mind.itemToChild.set(runtimeLinkKey, runtimeNode.id);
  state.mind.childToLink.set(runtimeNode.id, runtimeLinkKey);
}

function removeMindSubtree(nodeId) {
  const childIds = [];
  state.mind.nodes.forEach((node) => {
    if (node.parentId === nodeId) {
      childIds.push(node.id);
    }
  });
  childIds.forEach((id) => removeMindSubtree(id));

  const removeKeys = [];
  state.mind.itemToChild.forEach((childId, linkKey) => {
    if (childId === nodeId || linkKey.startsWith(`${nodeId}::`)) {
      removeKeys.push(linkKey);
    }
  });
  removeKeys.forEach((key) => state.mind.itemToChild.delete(key));
  state.mind.childToLink.delete(nodeId);
  state.mind.nodes.delete(nodeId);
}

function toggleMindItem(parentId, itemId) {
  const parent = state.mind.nodes.get(parentId);
  if (!parent) return;
  const item = parent.items.find((entry) => entry.id === itemId);
  if (!item || !item.expandable) return;
  if (parentId === "root" && itemId === "runtime-flow") return;

  const linkKey = itemLinkKey(parentId, itemId);
  if (state.mind.itemToChild.has(linkKey)) {
    const childId = state.mind.itemToChild.get(linkKey);
    removeMindSubtree(childId);
    state.mind.itemToChild.delete(linkKey);
    state.mind.childToLink.delete(childId);
    drawGraph();
    return;
  }

  const childNode = buildChildNode(parent, item);
  if (!childNode) return;
  state.mind.nodes.set(childNode.id, childNode);
  state.mind.itemToChild.set(linkKey, childNode.id);
  state.mind.childToLink.set(childNode.id, linkKey);
  drawGraph();
}

function collapseNode(nodeId) {
  if (nodeId === "root") return;
  const linkKey = state.mind.childToLink.get(nodeId);
  if (!linkKey) return;
  if (linkKey === itemLinkKey("root", "runtime-flow")) return;
  const childId = state.mind.itemToChild.get(linkKey);
  if (!childId) return;
  removeMindSubtree(childId);
  state.mind.itemToChild.delete(linkKey);
  state.mind.childToLink.delete(childId);
  drawGraph();
}

function syncRuntimeFlowNode() {
  ensureRuntimeFlowExpanded();
  const root = state.mind.nodes.get("root");
  if (!root) return;
  const runtimeItem = root.items.find((item) => item.id === "runtime-flow" && item.expandable);
  if (!runtimeItem) return;

  const runtimeLinkKey = itemLinkKey(root.id, runtimeItem.id);
  const runtimeId = state.mind.itemToChild.get(runtimeLinkKey);
  if (!runtimeId) return;

  let chainParent = state.mind.nodes.get(runtimeId);
  while (chainParent) {
    const nextStepItem = chainParent.items.find((entry) => entry.expandable && entry.type === "flow_step");
    if (!nextStepItem) break;

    const chainKey = itemLinkKey(chainParent.id, nextStepItem.id);
    if (state.mind.itemToChild.has(chainKey)) {
      const childId = state.mind.itemToChild.get(chainKey);
      chainParent = childId ? state.mind.nodes.get(childId) : null;
      continue;
    }

    const child = buildChildNode(chainParent, nextStepItem);
    if (!child) break;
    state.mind.nodes.set(child.id, child);
    state.mind.itemToChild.set(chainKey, child.id);
    state.mind.childToLink.set(child.id, chainKey);
    chainParent = child;
  }
}

function applyRuntimeFlowLabelInPlace() {
  const btn = graphEl.querySelector('button[data-parent-id="root"][data-mind-item="runtime-flow"]');
  if (!btn) return;
  const expanded = btn.classList.contains("expanded");
  btn.textContent = `${expanded ? "▾" : "▸"} ${formatRuntimeFlowLabel(selectedEvent())}`;
}

function applyRuntimeSummaryInPlace() {
  const runtimeBlock = graphEl.querySelector('.mind-block[data-kind="runtime"]');
  if (!runtimeBlock) return;
  const event = selectedEvent();
  if (!event) return;
  const prev = previousEvent();
  const diff = diffFlowNodes(prev?.flow || [], event.flow || []);

  const setItemText = (itemId, text) => {
    const el = runtimeBlock.querySelector(`.mind-item-text[data-item-id="${itemId}"]`);
    if (el) el.textContent = text;
  };

  setItemText("runtime-event", `Event: ${formatEventTag(event.id)}`);
  setItemText("runtime-prev", `From: ${prev ? formatEventTag(prev.id) : "(start of run)"}`);
  setItemText("runtime-phase", `Phase/Tool: ${event.phase} / ${event.tool}`);
  setItemText("runtime-now", `Current Flow: ${formatNodeList(event.flow || [])}`);
  setItemText("runtime-diff-entered", `Transition + Entered: ${formatNodeList(diff.entered)}`);
  setItemText("runtime-diff-exited", `Transition - Exited: ${formatNodeList(diff.exited)}`);
  setItemText("runtime-diff-kept", `Transition = Kept: ${formatNodeList(diff.kept)}`);

  const backbone = buildBackboneFlowNodeIds();
  const currSet = new Set(event.flow || []);
  const prevSet = new Set(prev?.flow || []);
  const lineEls = runtimeBlock.querySelectorAll('.mind-item-text[data-item-id^="backbone-line:"]');
  lineEls.forEach((el, index) => {
    const nodeId = backbone[index];
    if (!nodeId) return;
    const inCurr = currSet.has(nodeId);
    const inPrev = prevSet.has(nodeId);
    let marker = ".";
    if (inCurr && inPrev) marker = "=";
    else if (inCurr) marker = "+";
    else if (inPrev) marker = "-";
    el.textContent = `${marker} ${index + 1}. ${nodeLabel(nodeId)} (${nodeId})`;
  });
}

function applyFlowFocusClasses() {
  const event = selectedEvent();
  const prev = previousEvent();
  const currSet = new Set(event?.flow || []);
  const prevSet = new Set(prev?.flow || []);
  const blocks = graphEl.querySelectorAll(".mind-block[data-flow-node-id]");

  blocks.forEach((block) => {
    const nodeId = block.dataset.flowNodeId || "";
    const inCurr = currSet.has(nodeId);
    const inPrev = prevSet.has(nodeId);
    block.classList.remove("flow-entered", "flow-kept", "flow-exited", "flow-idle");
    if (inCurr && inPrev) {
      block.classList.add("flow-kept");
    } else if (inCurr) {
      block.classList.add("flow-entered");
    } else if (inPrev) {
      block.classList.add("flow-exited");
    } else {
      block.classList.add("flow-idle");
    }
  });
}

function refreshFlowViewInPlace() {
  applyRuntimeFlowLabelInPlace();
  applyRuntimeSummaryInPlace();
  applyFlowFocusClasses();
}

function layoutMindNodes() {
  const nodes = Array.from(state.mind.nodes.values());
  const byDepth = new Map();
  const depthMaxWidth = new Map();
  nodes.forEach((node) => {
    const size = estimateNodeSize(node);
    node.autoSize = size;
    if (!byDepth.has(node.depth)) byDepth.set(node.depth, []);
    byDepth.get(node.depth).push(node);
    depthMaxWidth.set(node.depth, Math.max(depthMaxWidth.get(node.depth) || 0, size.w));
  });

  const depths = Array.from(byDepth.keys()).sort((a, b) => a - b);
  const leftPad = 24;
  const topPad = 18;
  const colGap = 76;
  const gapY = 18;

  let maxWidth = 0;
  let maxHeight = 0;
  const autoPos = new Map();
  const depthBaseX = new Map();

  let offsetX = leftPad;
  depths.forEach((depth) => {
    depthBaseX.set(depth, offsetX);
    offsetX += (depthMaxWidth.get(depth) || 340) + colGap;
  });

  depths.forEach((depth) => {
    const list = byDepth.get(depth);
    let y = topPad;
    list.forEach((node) => {
      const width = node.autoSize?.w || 340;
      const height = node.autoSize?.h || 120;
      autoPos.set(node.id, {
        x: depthBaseX.get(depth) || leftPad,
        y,
        w: width,
        h: height
      });
      y += height + gapY;
    });
  });

  nodes.forEach((node) => {
    const fallback = autoPos.get(node.id) || {
      x: leftPad,
      y: topPad,
      w: node.autoSize?.w || 340,
      h: node.autoSize?.h || 120
    };
    const x = node.manualPos ? node.manualPos.x : fallback.x;
    const y = node.manualPos ? node.manualPos.y : fallback.y;
    node.layout = {
      x,
      y,
      w: fallback.w,
      h: fallback.h
    };
    maxWidth = Math.max(maxWidth, node.layout.x + node.layout.w + 40);
    maxHeight = Math.max(maxHeight, node.layout.y + node.layout.h + 40);
  });

  const root = state.mind.nodes.get("root");
  if (root && root.layout && !root.manualPos) {
    const d1 = byDepth.get(1) || [];
    if (d1.length) {
      const minY = Math.min(...d1.map((node) => node.layout.y));
      const maxY = Math.max(...d1.map((node) => node.layout.y + node.layout.h));
      root.layout.y = Math.max(topPad, Math.round((minY + maxY - root.layout.h) / 2));
      maxHeight = Math.max(maxHeight, root.layout.y + root.layout.h + 40);
    }
  }

  const placed = [];
  const ordered = Array.from(state.mind.nodes.values())
    .filter((node) => node.id !== "root")
    .sort((a, b) => (a.layout.x - b.layout.x) || (a.layout.y - b.layout.y));

  ordered.forEach((node) => {
    let guard = 0;
    while (placed.some((other) => rectsOverlap(node.layout, other.layout)) && guard < 200) {
      node.layout.y += 18;
      guard += 1;
    }
    placed.push(node);
    maxHeight = Math.max(maxHeight, node.layout.y + node.layout.h + 40);
  });

  if (root && root.layout) {
    maxHeight = Math.max(maxHeight, root.layout.y + root.layout.h + 40);
  }

  return { width: Math.max(maxWidth, 860), height: Math.max(maxHeight, 520) };
}

function routeMindEdge(start, end) {
  // 連線路由策略：
  // - 優先使用單一三次貝茲曲線，讓心智圖展開後視覺連續
  // - 當 child 與 parent 幾乎同 x（或反向）時，改用中線控制點，避免急折返
  const dx = end.x - start.x;
  if (dx <= 8) {
    const midX = Math.round((start.x + end.x) / 2);
    return `M ${start.x} ${start.y} C ${midX} ${start.y}, ${midX} ${end.y}, ${end.x} ${end.y}`;
  }
  const bend = Math.round(Math.max(28, Math.min(180, dx * 0.42)));
  const c1x = start.x + bend;
  const c2x = end.x - bend;
  return `M ${start.x} ${start.y} C ${c1x} ${start.y}, ${c2x} ${end.y}, ${end.x} ${end.y}`;
}

function resolveMindAnchors(board) {
  // 以「board 世界座標」解析所有錨點：
  // - itemOutAnchors: 每個可展開項目的輸出端（右側中點）
  // - blockInAnchors: 每個子 block 的輸入端（header 左側中線）
  // 這裡直接取渲染後 DOM 幾何，可自然納入捲軸、字體、動態尺寸變化。
  const boardRect = board.getBoundingClientRect();
  const itemOutAnchors = new Map();
  const blockInAnchors = new Map();

  const blocks = board.querySelectorAll(".mind-block[data-node-id]");
  blocks.forEach((block) => {
    const nodeId = block.dataset.nodeId;
    if (!nodeId) return;

    const blockRect = block.getBoundingClientRect();
    const header = block.querySelector(".mind-block-header");
    let inY = (blockRect.top - boardRect.top) + Math.min(24, blockRect.height / 2);
    if (header) {
      const headerRect = header.getBoundingClientRect();
      inY = (headerRect.top - boardRect.top) + (headerRect.height / 2);
    }

    blockInAnchors.set(nodeId, {
      x: blockRect.left - boardRect.left,
      y: inY
    });

    const itemButtons = block.querySelectorAll(`button[data-parent-id="${nodeId}"][data-mind-item]`);
    itemButtons.forEach((button) => {
      const itemId = button.dataset.mindItem;
      if (!itemId) return;
      const rect = button.getBoundingClientRect();
      itemOutAnchors.set(itemLinkKey(nodeId, itemId), {
        x: rect.right - boardRect.left,
        y: (rect.top - boardRect.top) + (rect.height / 2)
      });
    });
  });

  return { itemOutAnchors, blockInAnchors };
}

function drawMindEdges(board, svg) {
  // 每次重繪先清空線層，再以 linkKey(parent::item)->childId 重建，
  // 可避免展開/收折/拖曳後殘留舊 path。
  svg.innerHTML = "";
  const anchors = resolveMindAnchors(board);

  state.mind.itemToChild.forEach((childId, linkKey) => {
    const start = anchors.itemOutAnchors.get(linkKey);
    const end = anchors.blockInAnchors.get(childId);
    if (!start || !end) return;

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", routeMindEdge(start, end));
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "#4a6989");
    path.setAttribute("stroke-width", "1.6");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");
    path.setAttribute("opacity", "0.95");
    svg.appendChild(path);

    const head = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    head.setAttribute("cx", String(start.x));
    head.setAttribute("cy", String(start.y));
    head.setAttribute("r", "2");
    head.setAttribute("fill", "#6ca7da");
    svg.appendChild(head);

    const tail = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    tail.setAttribute("cx", String(end.x));
    tail.setAttribute("cy", String(end.y));
    tail.setAttribute("r", "2");
    tail.setAttribute("fill", "#6ca7da");
    svg.appendChild(tail);
  });
}

function drawGraph() {
  // 重新渲染前先保存每個 block 的捲動位置，避免使用者展開內容後視窗跳回頂端。
  const prevBlocks = graphEl.querySelectorAll(".mind-block[data-node-id]");
  prevBlocks.forEach((block) => {
    const node = state.mind.nodes.get(block.dataset.nodeId);
    if (!node) return;
    node.scrollTop = block.scrollTop;
    node.scrollLeft = block.scrollLeft;
  });

  if (!state.mind.nodes.size) {
    initMindTree();
  }

  graphEl.innerHTML = "";
  const board = document.createElement("div");
  board.className = "mindmap-board";
  const layout = layoutMindNodes();
  board.style.width = `${layout.width}px`;
  board.style.height = `${layout.height}px`;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.classList.add("mind-svg");
  svg.setAttribute("width", String(layout.width));
  svg.setAttribute("height", String(layout.height));
  svg.setAttribute("viewBox", `0 0 ${layout.width} ${layout.height}`);
  board.appendChild(svg);

  state.mind.nodes.forEach((node) => {
    const block = document.createElement("section");
    block.className = `mind-block ${node.kind === "root" ? "root" : ""}`;
    block.dataset.nodeId = node.id;
    block.dataset.kind = node.kind;
    if (node.flowNodeId) {
      block.dataset.flowNodeId = node.flowNodeId;
    }
    block.style.left = `${node.layout.x}px`;
    block.style.top = `${node.layout.y}px`;
    block.style.height = `${node.layout.h}px`;

    const header = document.createElement("div");
    header.className = "mind-block-header";
    const title = document.createElement("h3");
    title.textContent = node.title;
    header.appendChild(title);
    if (node.id !== "root" && node.kind !== "runtime") {
      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.className = "mind-collapse-btn";
      closeBtn.dataset.collapseNode = node.id;
      closeBtn.textContent = "−";
      header.appendChild(closeBtn);
    }
    block.appendChild(header);

    const list = document.createElement("ul");
    node.items.forEach((item) => {
      const row = document.createElement("li");
      if (item.expandable) {
        const key = itemLinkKey(node.id, item.id);
        const expanded = state.mind.itemToChild.has(key);
        const event = selectedEvent();
        const isRuntimeFlowRootItem = item.type === "runtime_flow" && !!event;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `mind-item-btn${expanded ? " expanded" : ""}${isRuntimeFlowRootItem ? " flow-active" : ""}`;
        btn.dataset.parentId = node.id;
        btn.dataset.mindItem = item.id;
        btn.dataset.itemId = item.id;
        btn.textContent = `${expanded ? "▾" : "▸"} ${item.label}`;
        row.appendChild(btn);
      } else {
        const span = document.createElement("span");
        span.className = "mind-item-text";
        span.dataset.itemId = item.id;
        span.textContent = item.label;
        row.appendChild(span);
      }
      list.appendChild(row);
    });
    block.appendChild(list);
    board.appendChild(block);

    if (node.scrollTop) {
      block.scrollTop = node.scrollTop;
    }
    if (node.scrollLeft) {
      block.scrollLeft = node.scrollLeft;
    }
    block.addEventListener("scroll", () => {
      node.scrollTop = block.scrollTop;
      node.scrollLeft = block.scrollLeft;
      drawMindEdges(board, svg);
    });
  });

  graphEl.appendChild(board);
  // 第一輪：DOM 掛載後立即繪製
  drawMindEdges(board, svg);
  window.requestAnimationFrame(() => {
    if (!board.isConnected || !svg.isConnected) return;
    // 第二輪：等瀏覽器完成 reflow/repaint 後再校正一次，減少首次展開錯位。
    drawMindEdges(board, svg);
  });
  refreshFlowViewInPlace();
}

function hasOverlapWithOthers(nodeId, x, y, w, h) {
  const probe = { x, y, w, h };
  for (const node of state.mind.nodes.values()) {
    if (node.id === nodeId || !node.layout) continue;
    const other = {
      x: node.layout.x,
      y: node.layout.y,
      w: node.layout.w,
      h: node.layout.h
    };
    if (rectsOverlap(probe, other, 8)) {
      return true;
    }
  }
  return false;
}

function resolveNonOverlapPosition(nodeId, x, y, w, h, maxX, maxY) {
  let candidateX = clamp(x, 0, maxX);
  let candidateY = clamp(y, 0, maxY);

  if (!hasOverlapWithOthers(nodeId, candidateX, candidateY, w, h)) {
    return { x: candidateX, y: candidateY };
  }

  let attempts = 0;
  while (attempts < 420) {
    candidateY += 18;
    if (candidateY > maxY) {
      candidateY = 0;
      candidateX = clamp(candidateX + 26, 0, maxX);
    }
    if (!hasOverlapWithOthers(nodeId, candidateX, candidateY, w, h)) {
      return { x: candidateX, y: candidateY };
    }
    attempts += 1;
  }
  return null;
}

function startNodeDrag(nodeId, event, blockElement) {
  const node = state.mind.nodes.get(nodeId);
  if (!node || !node.layout) return;

  const board = graphEl.querySelector(".mindmap-board");
  if (!board) return;

  const rect = board.getBoundingClientRect();
  state.drag.active = true;
  state.drag.nodeId = nodeId;
  state.drag.offsetX = event.clientX - rect.left - node.layout.x;
  state.drag.offsetY = event.clientY - rect.top - node.layout.y;
  state.drag.clientX = event.clientX;
  state.drag.clientY = event.clientY;
  // block 寬度採用渲染後實際值（fit-content），
  // 才能讓拖曳邊界與防重疊判斷與畫面一致。
  const rectNode = blockElement?.getBoundingClientRect();
  state.drag.width = Math.round(rectNode?.width || node.layout.w);
  state.drag.height = Math.round(rectNode?.height || node.layout.h);
  state.drag.lastX = node.layout.x;
  state.drag.lastY = node.layout.y;
  graphEl.classList.add("dragging");
}

function applyNodeDragPosition() {
  if (!state.drag.active || !state.drag.nodeId) return;
  const node = state.mind.nodes.get(state.drag.nodeId);
  if (!node) return;

  const board = graphEl.querySelector(".mindmap-board");
  if (!board) return;

  const rect = board.getBoundingClientRect();
  const width = state.drag.width || node.layout?.w || 340;
  const height = state.drag.height || node.layout?.h || 120;
  const maxX = Math.max(0, board.clientWidth - width - 4);
  const maxY = Math.max(0, board.clientHeight - height - 4);

  const x = clamp(Math.round(state.drag.clientX - rect.left - state.drag.offsetX), 0, maxX);
  const y = clamp(Math.round(state.drag.clientY - rect.top - state.drag.offsetY), 0, maxY);

  const position = resolveNonOverlapPosition(node.id, x, y, width, height, maxX, maxY);
  if (!position) {
    return;
  }

  node.manualPos = { x: position.x, y: position.y };
  state.drag.lastX = position.x;
  state.drag.lastY = position.y;
  drawGraph();
}

function queueNodeDrag(event) {
  if (!state.drag.active) return;
  state.drag.clientX = event.clientX;
  state.drag.clientY = event.clientY;
  if (state.drag.rafId) return;
  state.drag.rafId = window.requestAnimationFrame(() => {
    state.drag.rafId = 0;
    applyNodeDragPosition();
  });
}

function stopNodeDrag() {
  if (!state.drag.active) return;
  state.drag.active = false;
  state.drag.nodeId = "";
  state.drag.width = 0;
  state.drag.height = 0;
  if (state.drag.rafId) {
    window.cancelAnimationFrame(state.drag.rafId);
    state.drag.rafId = 0;
  }
  graphEl.classList.remove("dragging");
}

async function renderEventDetails() {
  const event = selectedEvent();
  if (!event) {
    detailsEl.innerHTML = '<div class="badge b-warn">NO EVENT</div>';
    return;
  }

  const detail = await api.getEventDetail(state.runId, event.id);
  const eventTag = formatEventTag(detail.id);
  const prev = previousEvent();
  const diff = diffFlowNodes(prev?.flow || [], detail.flow || []);
  detailsEl.innerHTML = `
    <div>${statusBadge(detail.status)}${consensusBadge(detail.consensus)}</div>
    <div>${runBadge(state.runs.find((run) => run.run_id === state.runId)?.status || "unknown")}</div>
    <div><b>Run</b> <span class="mono">${escapeHtml(state.runMeta.run_id)}</span></div>
    <div><b>Target</b> <span class="mono">${escapeHtml(state.runMeta.target_id)}</span></div>
    <div><b>Summary</b> ${escapeHtml(state.runMeta.summary || "")}</div>
    <hr>
    <div><b>Event</b> <span class="mono">${escapeHtml(eventTag)}</span></div>
    <div><b>Time</b> ${escapeHtml(detail.time)}</div>
    <div><b>Tool</b> ${escapeHtml(detail.tool)}</div>
    <div><b>Title</b> ${escapeHtml(detail.title)}</div>
    <div><b>Symbol</b> <span class="mono">${escapeHtml(detail.symbol)}</span></div>
    <div><b>Address</b> <span class="mono">${escapeHtml(detail.address)}</span></div>
    <div><b>Evidence</b> <span class="mono">${escapeHtml((detail.evidence || []).join(", "))}</span></div>
    <div><b>Flow</b> <span class="mono">${escapeHtml((detail.flow || []).join(" -> "))}</span></div>
    <div><b>From</b> <span class="mono">${escapeHtml(prev ? formatEventTag(prev.id) : "(start of run)")}</span></div>
    <div><b>Transition +</b> <span class="mono">${escapeHtml(formatNodeList(diff.entered))}</span></div>
    <div><b>Transition -</b> <span class="mono">${escapeHtml(formatNodeList(diff.exited))}</span></div>
    <div><b>Transition =</b> <span class="mono">${escapeHtml(formatNodeList(diff.kept))}</span></div>
  `;
}

async function renderNodeDetails(nodeId) {
  const detail = await api.getNodeDetail(state.runId, nodeId);
  if (!detail) return;

  detailsEl.innerHTML = `
    <div><span class="badge b-info">NODE DRILLDOWN</span></div>
    <div><b>Node</b> <span class="mono">${escapeHtml(detail.id)}</span></div>
    <div><b>Label</b> ${escapeHtml(detail.label)}</div>
    <div><b>Type</b> ${escapeHtml(detail.type)}</div>
    <div><b>Related Events</b> ${detail.relatedEvents.length}</div>
    <hr>
    <div class="mono">
      ${detail.relatedEvents
        .map((event) => `${escapeHtml(event.time)} ${escapeHtml(formatEventTag(event.id))} ${escapeHtml(event.tool)} ${escapeHtml(event.consensus)}`)
        .join("<br>")}
    </div>
  `;
}

function updateStats() {
  statsEl.textContent = `${state.timeline.length} events`;
}

function updateHint() {
  const event = selectedEvent();
  if (!event) {
    hintEl.textContent = `HLAPI: ${state.selectedPath || "-"} / no active event`;
    return;
  }
  const prev = previousEvent();
  const from = prev ? ` / from ${formatEventTag(prev.id)}` : "";
  hintEl.textContent = `HLAPI: ${state.selectedPath || "-"} / ${formatEventTag(event.id)} / ${event.phase}${from}`;
}

async function setActive(index) {
  if (!state.timeline.length) {
    state.activeIndex = 0;
    state.activeEventId = "";
    updateRuntimeFlowItemLabel();
    renderTimeline();
    refreshFlowViewInPlace();
    updateStats();
    updateHint();
    await renderEventDetails();
    return;
  }

  state.activeIndex = Math.max(0, Math.min(index, state.timeline.length - 1));
  state.activeEventId = state.timeline[state.activeIndex].id;
  updateRuntimeFlowItemLabel();
  renderTimeline();
  refreshFlowViewInPlace();
  updateStats();
  updateHint();
  await renderEventDetails();
}

function tickNext() {
  if (!state.timeline.length) return;
  const next = (state.activeIndex + 1) % state.timeline.length;
  setActive(next);
}

function startPlay() {
  if (state.timerId) return;
  const interval = Number(speedSelect.value);
  playBtn.textContent = "Pause";
  state.timerId = setInterval(tickNext, interval);
}

function stopPlay() {
  if (!state.timerId) return;
  clearInterval(state.timerId);
  state.timerId = null;
  playBtn.textContent = "Play";
}

async function refreshTimeline() {
  const payload = await api.getTimeline(state.runId, state.filters);
  state.timeline = payload.events;
  renderFilterOptions();

  let index = 0;
  if (state.activeEventId) {
    const found = state.timeline.findIndex((event) => event.id === state.activeEventId);
    if (found >= 0) index = found;
  }
  await setActive(index);
}

async function loadRun(runId) {
  stopPlay();
  stopNodeDrag();
  state.runId = runId;
  state.runMeta = await api.getRun(runId);
  {
    const paths = state.hlapiContext?.path_contexts || [];
    const runDefaultPath = state.runMeta?.default_path || "";
    const hasRunDefaultPath = runDefaultPath && paths.some((item) => item.path === runDefaultPath);
    const hasSelectedPath = state.selectedPath && paths.some((item) => item.path === state.selectedPath);
    if (hasRunDefaultPath) {
      state.selectedPath = runDefaultPath;
    } else if (!hasSelectedPath) {
      state.selectedPath = paths[0]?.path || "";
    }
  }
  renderPathOptions();
  state.graph = await api.getGraph(runId);
  state.activeIndex = 0;
  state.activeEventId = "";
  await refreshTimeline();
  initMindTree();
  drawGraph();
}

function bindEvents() {
  playBtn.addEventListener("click", () => {
    if (state.timerId) {
      stopPlay();
      return;
    }
    startPlay();
  });

  prevBtn.addEventListener("click", () => {
    stopPlay();
    if (!state.timeline.length) return;
    const prev = state.activeIndex === 0 ? state.timeline.length - 1 : state.activeIndex - 1;
    setActive(prev);
  });

  nextBtn.addEventListener("click", () => {
    stopPlay();
    tickNext();
  });

  speedSelect.addEventListener("change", () => {
    if (!state.timerId) return;
    stopPlay();
    startPlay();
  });

  runSelect.addEventListener("change", () => loadRun(runSelect.value));

  applyFilterBtn.addEventListener("click", async () => {
    state.filters.phase = phaseSelect.value;
    state.filters.tool = toolSelect.value;
    state.filters.keyword = searchInput.value.trim();
    await refreshTimeline();
  });

  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      applyFilterBtn.click();
    }
  });

  pathSelect.addEventListener("change", () => {
    stopNodeDrag();
    state.selectedPath = pathSelect.value;
    initMindTree();
    drawGraph();
    updateHint();
  });

  graphEl.addEventListener("mousedown", (event) => {
    if (event.target.closest("button[data-mind-item]")) return;
    if (event.target.closest("button[data-collapse-node]")) return;
    const block = event.target.closest(".mind-block[data-node-id]");
    if (!block) return;
    event.preventDefault();
    startNodeDrag(block.dataset.nodeId, event, block);
  });

  window.addEventListener("mousemove", (event) => {
    queueNodeDrag(event);
  });

  window.addEventListener("mouseup", () => {
    stopNodeDrag();
  });

  graphEl.addEventListener("click", (event) => {
    const collapseButton = event.target.closest("button[data-collapse-node]");
    if (collapseButton) {
      collapseNode(collapseButton.dataset.collapseNode);
      return;
    }
    const button = event.target.closest("button[data-mind-item]");
    if (!button) return;
    toggleMindItem(button.dataset.parentId, button.dataset.mindItem);
  });
}

async function bootstrap() {
  bindEvents();

  state.hlapiContext = await api.getHlapiContext();
  state.selectedPath = state.hlapiContext?.path_contexts?.[0]?.path || "";
  renderPathOptions();

  state.runs = await api.listRuns();
  if (!state.runs.length) {
    detailsEl.innerHTML = '<div class="badge b-danger">NO MOCK RUNS</div>';
    initMindTree();
    drawGraph();
    return;
  }

  state.runId = state.runs[0].run_id;
  renderRunOptions();
  await loadRun(state.runId);
}

bootstrap();
