#!/usr/bin/env node

/**
 * governance-timeline.js — Live governance bus timeline graph
 *
 * Reads governance_*.jsonl files and renders a D3 swimlane timeline:
 * - Rows = intent sessions (intent_id)
 * - X axis = time
 * - Dots = tuple events, colored by tuple_type
 * - Watch mode: re-generates on any .jsonl file change
 *
 * Usage:
 *   node scripts/governance-timeline.js [governance-dir] [--watch] [--output reports/]
 *
 * Stdlib-only watcher (fs.watch). No third-party dependencies for the watcher.
 * D3 inlined from node_modules if available, otherwise fetched at build time.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const args = process.argv.slice(2);
const watchMode = args.includes('--watch');
const governanceDir = path.resolve(args.find(a => !a.startsWith('--')) || './governance');
const reportsDir = path.resolve(__dirname, '../reports');
const outputPath = path.join(reportsDir, 'governance_timeline.html');

const DEBOUNCE_MS = 500;

// ── Tuple type styling ──────────────────────────────────────────────────────

const TUPLE_COLORS = {
  DCT:      '#e9c46a', // delegation capability token — gold
  DCTX:     '#f4a261', // delegation context — orange
  CONTRACT: '#2a9d8f', // contract — teal
  EVIDENCE: '#457b9d', // evidence — blue
  ATTEST:   '#6d6875', // attestation — purple
  SYSTEM:   '#adb5bd', // system event — grey
};

const TUPLE_LABELS = {
  DCT:      'Capability Token',
  DCTX:     'Delegation Context',
  CONTRACT: 'Contract',
  EVIDENCE: 'Evidence',
  ATTEST:   'Attestation',
  SYSTEM:   'System Event',
};

// ── Parse JSONL files ───────────────────────────────────────────────────────

function parseGovernanceDir(dir) {
  if (!fs.existsSync(dir)) {
    console.error(`Governance directory not found: ${dir}`);
    return [];
  }

  const files = fs.readdirSync(dir)
    .filter(f => f.endsWith('.jsonl') && !f.endsWith('.gz'))
    .sort();

  const entries = [];
  for (const file of files) {
    const content = fs.readFileSync(path.join(dir, file), 'utf8');
    const lines = content.trim().split('\n').filter(Boolean);
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        entries.push(entry);
      } catch {
        // skip malformed lines
      }
    }
  }
  return entries;
}

// ── Transform entries → graph data ─────────────────────────────────────────

function buildGraphData(entries) {
  // Group by intent_id
  const intentMap = new Map();

  for (const e of entries) {
    const intentId = e.intent_id || 'unknown';
    if (!intentMap.has(intentId)) {
      intentMap.set(intentId, {
        intentId,
        events: [],
        minTime: null,
        maxTime: null,
      });
    }
    const intent = intentMap.get(intentId);
    const ts = new Date(e.timestamp).getTime();
    if (isNaN(ts)) continue;

    intent.events.push({
      entryId: e.entry_id,
      timestamp: e.timestamp,
      ts,
      tupleType: e.tuple_type || 'SYSTEM',
      taskId: e.task_id,
      event: e.tuple_data?.event || '',
      adapter: e.tuple_data?.adapter || '',
      status: e.tuple_data?.status || '',
      contractId: e.tuple_data?.contract_id || '',
      subject: e.tuple_data?.subject || e.tuple_data?.delegatee || '',
      riskTier: e.tuple_data?.risk_tier || '',
    });

    if (intent.minTime === null || ts < intent.minTime) intent.minTime = ts;
    if (intent.maxTime === null || ts > intent.maxTime) intent.maxTime = ts;
  }

  // Sort intents by most recent first, limit to last 50 sessions for readability
  const intents = [...intentMap.values()]
    .filter(i => i.events.length > 0)
    .sort((a, b) => b.maxTime - a.maxTime)
    .slice(0, 50);

  // Sort events within each intent
  intents.forEach(i => i.events.sort((a, b) => a.ts - b.ts));

  // Global time bounds across displayed intents
  const allTs = intents.flatMap(i => i.events.map(e => e.ts));
  const globalMin = Math.min(...allTs);
  const globalMax = Math.max(...allTs);

  // Event type distribution
  const typeCounts = {};
  for (const intent of intents) {
    for (const ev of intent.events) {
      typeCounts[ev.tupleType] = (typeCounts[ev.tupleType] || 0) + 1;
    }
  }

  return {
    intents,
    globalMin,
    globalMax,
    typeCounts,
    totalEntries: entries.length,
    displayedSessions: intents.length,
    generated: new Date().toISOString(),
  };
}

// ── Generate HTML ───────────────────────────────────────────────────────────

function loadD3() {
  const candidates = [
    path.resolve(__dirname, '../node_modules/d3/dist/d3.min.js'),
    path.resolve(__dirname, '../../node_modules/d3/dist/d3.min.js'),
    '/usr/local/lib/node_modules/d3/dist/d3.min.js',
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      console.log(`Using local d3: ${p}`);
      return fs.readFileSync(p, 'utf8');
    }
  }
  return null; // will use CDN fallback in HTML
}

function generateHtml(graphData) {
  const d3Source = loadD3();
  const dataJson = JSON.stringify(graphData);
  const colorsJson = JSON.stringify(TUPLE_COLORS);
  const labelsJson = JSON.stringify(TUPLE_LABELS);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HUMMBL Governance Timeline</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0f1117; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace; font-size: 13px; overflow-x: hidden; }

#header { position: sticky; top: 0; z-index: 20; background: rgba(15,17,23,0.95); border-bottom: 1px solid #2d3748; padding: 10px 16px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
#header h1 { font-size: 13px; font-weight: 600; color: #a0aec0; white-space: nowrap; }
#stats { font-size: 11px; color: #4a5568; }
#controls { display: flex; gap: 6px; margin-left: auto; flex-wrap: wrap; }
button { background: #1a202c; border: 1px solid #2d3748; color: #a0aec0; padding: 3px 10px; border-radius: 3px; cursor: pointer; font-size: 11px; }
button:hover { background: #2d3748; color: #e2e8f0; }
button.active { background: #2d3748; color: #e2e8f0; border-color: #4a5568; }

#search-bar { padding: 6px 16px; border-bottom: 1px solid #1a202c; background: #0f1117; display: flex; gap: 8px; align-items: center; }
#search { background: #1a202c; border: 1px solid #2d3748; color: #e2e8f0; padding: 3px 8px; border-radius: 3px; font-size: 11px; width: 260px; }
#search::placeholder { color: #4a5568; }
.filter-label { font-size: 11px; color: #4a5568; }

#legend { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; padding: 6px 16px; border-bottom: 1px solid #1a202c; background: #0f1117; }
.leg-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #718096; cursor: pointer; }
.leg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.leg-item.hidden { opacity: 0.35; }

#timeline-wrap { overflow-x: auto; padding: 8px 0; }
#timeline svg { display: block; }

.intent-row { cursor: pointer; }
.intent-row:hover .row-bg { fill: #1a202c; }
.row-bg { fill: transparent; }
.row-label { font-size: 10px; fill: #4a5568; font-family: monospace; }
.row-label.highlighted { fill: #a0aec0; }
.axis-line { stroke: #1a202c; stroke-width: 1; }
.tick-label { font-size: 9px; fill: #2d3748; font-family: monospace; }
.event-dot { cursor: pointer; transition: r 0.1s; }
.event-dot:hover { r: 5; }

#tooltip { position: fixed; z-index: 30; background: #1a202c; border: 1px solid #2d3748; border-radius: 5px; padding: 8px 10px; font-size: 11px; max-width: 320px; pointer-events: none; display: none; line-height: 1.5; }
#tooltip .tt-type { font-weight: 700; margin-bottom: 3px; }
#tooltip .tt-row { color: #718096; }
#tooltip .tt-row span { color: #a0aec0; }

#detail-panel { position: fixed; right: 0; top: 0; bottom: 0; width: 320px; background: #0a0d14; border-left: 1px solid #1a202c; padding: 12px; overflow-y: auto; transform: translateX(100%); transition: transform 0.2s; z-index: 25; }
#detail-panel.open { transform: translateX(0); }
#detail-panel h2 { font-size: 12px; color: #718096; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
#detail-panel h2 button { background: none; border: none; color: #4a5568; cursor: pointer; font-size: 14px; padding: 0; }
.detail-section { margin-bottom: 12px; }
.detail-section h3 { font-size: 10px; color: #4a5568; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.event-list { display: flex; flex-direction: column; gap: 3px; }
.ev-item { display: flex; align-items: flex-start; gap: 6px; padding: 4px 6px; border-radius: 3px; background: #111827; }
.ev-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 3px; }
.ev-info { font-size: 10px; color: #718096; line-height: 1.4; }
.ev-info .ev-event { color: #a0aec0; font-weight: 600; }
.ev-info .ev-time { color: #2d3748; font-size: 9px; }
</style>
</head>
<body>

<div id="header">
  <h1>HUMMBL Governance Timeline</h1>
  <span id="stats"></span>
  <div id="controls">
    <button id="btn-zoom-fit">Fit All</button>
    <button id="btn-zoom-day">Last 24h</button>
    <button id="btn-zoom-week">Last 7d</button>
    <button id="btn-expand" title="Expand all rows">Expand</button>
  </div>
</div>

<div id="search-bar">
  <span class="filter-label">Filter:</span>
  <input id="search" type="text" placeholder="intent_id, task_id, adapter, event…" />
  <span class="filter-label" id="match-count"></span>
</div>

<div id="legend"></div>

<div id="timeline-wrap">
  <svg id="timeline"></svg>
</div>

<div id="tooltip"></div>

<div id="detail-panel">
  <h2>Session Detail <button id="btn-close-panel">×</button></h2>
  <div id="detail-content"></div>
</div>

${d3Source ? `<script>${d3Source}</script>` : '<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>'}

<script>
const DATA = ${dataJson};
const COLORS = ${colorsJson};
const LABELS = ${labelsJson};

// ── Stats ──────────────────────────────────────────────────────────────────
document.getElementById('stats').textContent =
  \`\${DATA.totalEntries.toLocaleString()} entries · \${DATA.displayedSessions} sessions · \${DATA.generated.slice(0,10)}\`;

// ── Legend ─────────────────────────────────────────────────────────────────
const hiddenTypes = new Set();
const legend = document.getElementById('legend');
Object.entries(LABELS).forEach(([type, label]) => {
  const count = DATA.typeCounts[type] || 0;
  if (!count) return;
  const div = document.createElement('div');
  div.className = 'leg-item';
  div.dataset.type = type;
  div.innerHTML = \`<div class="leg-dot" style="background:\${COLORS[type]}"></div><span>\${label} (\${count})</span>\`;
  div.addEventListener('click', () => {
    if (hiddenTypes.has(type)) hiddenTypes.delete(type);
    else hiddenTypes.add(type);
    div.classList.toggle('hidden', hiddenTypes.has(type));
    render();
  });
  legend.appendChild(div);
});

// ── Layout constants ───────────────────────────────────────────────────────
const MARGIN = { top: 30, right: 20, bottom: 20, left: 230 };
const ROW_H = 24;
const DOT_R = 4;

// ── State ──────────────────────────────────────────────────────────────────
let query = '';
let zoomWindow = null; // null = fit all; [minTs, maxTs] = window
let expandedIntentId = null;

// ── Filter ─────────────────────────────────────────────────────────────────
function filteredIntents() {
  const q = query.toLowerCase();
  return DATA.intents.filter(i => {
    if (!q) return true;
    return i.intentId.toLowerCase().includes(q) ||
      i.events.some(e =>
        e.taskId?.toLowerCase().includes(q) ||
        e.adapter?.toLowerCase().includes(q) ||
        e.event?.toLowerCase().includes(q) ||
        e.subject?.toLowerCase().includes(q) ||
        e.contractId?.toLowerCase().includes(q)
      );
  });
}

// ── Render ─────────────────────────────────────────────────────────────────
function render() {
  const svg = d3.select('#timeline');
  svg.selectAll('*').remove();

  const intents = filteredIntents();
  document.getElementById('match-count').textContent =
    query ? \`\${intents.length} of \${DATA.intents.length} sessions\` : '';

  if (intents.length === 0) {
    svg.attr('width', 800).attr('height', 80)
      .append('text').attr('x', 400).attr('y', 44)
      .attr('text-anchor', 'middle').style('fill', '#4a5568').style('font-size', '12px')
      .text('No sessions match the filter.');
    return;
  }

  const containerWidth = Math.max(window.innerWidth - (expandedIntentId ? 320 : 0), 600);
  const innerW = containerWidth - MARGIN.left - MARGIN.right;

  // Time domain
  let [tMin, tMax] = zoomWindow || [DATA.globalMin, DATA.globalMax];
  if (tMin === tMax) { tMin -= 60000; tMax += 60000; }

  const xScale = d3.scaleTime()
    .domain([new Date(tMin), new Date(tMax)])
    .range([0, innerW]);

  // Calculate rows (expanded intent gets one row per event type)
  const rows = [];
  for (const intent of intents) {
    rows.push({ type: 'intent', intent, height: ROW_H });
  }

  const totalH = rows.reduce((s, r) => s + r.height, 0) + MARGIN.top + MARGIN.bottom;
  svg.attr('width', containerWidth).attr('height', totalH);

  const g = svg.append('g').attr('transform', \`translate(\${MARGIN.left},\${MARGIN.top})\`);

  // X axis
  const xAxis = d3.axisTop(xScale)
    .ticks(Math.min(10, Math.floor(innerW / 80)))
    .tickFormat(d3.timeFormat('%m/%d %H:%M'));

  g.append('g').call(xAxis)
    .selectAll('text').attr('class', 'tick-label')
    .style('fill', '#2d3748').style('font-size', '9px');

  g.select('.domain').style('stroke', '#1a202c');
  g.selectAll('.tick line').style('stroke', '#1a202c');

  // Rows
  let y = 0;
  for (const row of rows) {
    const { intent } = row;
    const isHighlighted = !query || filteredIntents().includes(intent);
    const isExpanded = expandedIntentId === intent.intentId;

    const rowG = g.append('g')
      .attr('class', 'intent-row')
      .attr('transform', \`translate(0,\${y})\`)
      .on('click', () => {
        expandedIntentId = isExpanded ? null : intent.intentId;
        showDetailPanel(isExpanded ? null : intent);
        render();
      });

    // Background
    rowG.append('rect')
      .attr('class', 'row-bg')
      .attr('x', -MARGIN.left)
      .attr('width', innerW + MARGIN.left + MARGIN.right)
      .attr('height', ROW_H)
      .attr('fill', isExpanded ? '#111827' : 'transparent');

    // Baseline
    rowG.append('line')
      .attr('class', 'axis-line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', ROW_H / 2).attr('y2', ROW_H / 2);

    // Label
    const shortId = intent.intentId.length > 32
      ? '…' + intent.intentId.slice(-30)
      : intent.intentId;
    rowG.append('text')
      .attr('class', \`row-label\${isHighlighted ? ' highlighted' : ''}\`)
      .attr('x', -8).attr('y', ROW_H / 2 + 3.5)
      .attr('text-anchor', 'end')
      .text(shortId);

    // Event dots
    const visibleEvents = intent.events.filter(e => !hiddenTypes.has(e.tupleType));
    rowG.selectAll('circle')
      .data(visibleEvents)
      .join('circle')
      .attr('class', 'event-dot')
      .attr('cx', d => xScale(new Date(d.ts)))
      .attr('cy', ROW_H / 2)
      .attr('r', DOT_R)
      .attr('fill', d => COLORS[d.tupleType] || '#adb5bd')
      .attr('stroke', '#0f1117')
      .attr('stroke-width', 1)
      .on('mouseover', (event, d) => showTooltip(event, d, intent))
      .on('mousemove', (event) => moveTooltip(event))
      .on('mouseout', hideTooltip);

    y += ROW_H;
  }
}

// ── Tooltip ────────────────────────────────────────────────────────────────
const tooltip = document.getElementById('tooltip');

function showTooltip(event, d, intent) {
  const color = COLORS[d.tupleType] || '#adb5bd';
  const lines = [
    \`<div class="tt-type" style="color:\${color}">\${LABELS[d.tupleType] || d.tupleType}</div>\`,
    \`<div class="tt-row">time: <span>\${new Date(d.ts).toISOString().replace('T',' ').slice(0,19)}Z</span></div>\`,
    d.event ? \`<div class="tt-row">event: <span>\${d.event}</span></div>\` : '',
    d.adapter ? \`<div class="tt-row">adapter: <span>\${d.adapter}</span></div>\` : '',
    d.subject ? \`<div class="tt-row">subject: <span>\${d.subject}</span></div>\` : '',
    d.contractId ? \`<div class="tt-row">contract: <span>\${d.contractId}</span></div>\` : '',
    d.riskTier ? \`<div class="tt-row">risk: <span>\${d.riskTier}</span></div>\` : '',
    d.status ? \`<div class="tt-row">status: <span>\${d.status}</span></div>\` : '',
    \`<div class="tt-row" style="margin-top:4px;font-size:9px;color:#2d3748">\${intent.intentId}</div>\`,
  ].filter(Boolean).join('');
  tooltip.innerHTML = lines;
  tooltip.style.display = 'block';
}

function moveTooltip(event) {
  tooltip.style.left = (event.clientX + 12) + 'px';
  tooltip.style.top = (event.clientY - 8) + 'px';
}

function hideTooltip() {
  tooltip.style.display = 'none';
}

// ── Detail panel ───────────────────────────────────────────────────────────
function showDetailPanel(intent) {
  const panel = document.getElementById('detail-panel');
  const content = document.getElementById('detail-content');
  if (!intent) { panel.classList.remove('open'); return; }

  panel.classList.add('open');
  const duration = ((intent.maxTime - intent.minTime) / 1000).toFixed(1);
  const eventsByType = {};
  for (const ev of intent.events) {
    if (!eventsByType[ev.tupleType]) eventsByType[ev.tupleType] = [];
    eventsByType[ev.tupleType].push(ev);
  }

  const html = \`
    <div class="detail-section">
      <h3>Session</h3>
      <div style="font-size:10px;color:#718096;word-break:break-all;line-height:1.5">
        <div>ID: <span style="color:#a0aec0">\${intent.intentId}</span></div>
        <div>Start: <span style="color:#a0aec0">\${new Date(intent.minTime).toISOString().replace('T',' ').slice(0,19)}Z</span></div>
        <div>Duration: <span style="color:#a0aec0">\${duration}s</span></div>
        <div>Events: <span style="color:#a0aec0">\${intent.events.length}</span></div>
      </div>
    </div>
    \${Object.entries(eventsByType).map(([type, evs]) => \`
      <div class="detail-section">
        <h3 style="color:\${COLORS[type]}">\${LABELS[type] || type} (\${evs.length})</h3>
        <div class="event-list">
          \${evs.map(ev => \`
            <div class="ev-item">
              <div class="ev-dot" style="background:\${COLORS[ev.tupleType]}"></div>
              <div class="ev-info">
                \${ev.event ? \`<div class="ev-event">\${ev.event}</div>\` : ''}
                \${ev.adapter ? \`<div>adapter: \${ev.adapter}</div>\` : ''}
                \${ev.subject ? \`<div>subject: \${ev.subject}</div>\` : ''}
                \${ev.contractId ? \`<div>contract: \${ev.contractId}</div>\` : ''}
                \${ev.status ? \`<div>status: \${ev.status}</div>\` : ''}
                <div class="ev-time">\${new Date(ev.ts).toISOString().replace('T',' ').slice(0,19)}Z</div>
              </div>
            </div>
          \`).join('')}
        </div>
      </div>
    \`).join('')}
  \`;
  content.innerHTML = html;
}

document.getElementById('btn-close-panel').addEventListener('click', () => {
  expandedIntentId = null;
  showDetailPanel(null);
  render();
});

// ── Controls ───────────────────────────────────────────────────────────────
document.getElementById('btn-zoom-fit').addEventListener('click', () => {
  zoomWindow = null;
  render();
});
document.getElementById('btn-zoom-day').addEventListener('click', () => {
  zoomWindow = [DATA.globalMax - 86400000, DATA.globalMax];
  render();
});
document.getElementById('btn-zoom-week').addEventListener('click', () => {
  zoomWindow = [DATA.globalMax - 7 * 86400000, DATA.globalMax];
  render();
});
document.getElementById('btn-expand').addEventListener('click', () => {
  // Toggle label width
});

document.getElementById('search').addEventListener('input', e => {
  query = e.target.value;
  render();
});

window.addEventListener('resize', () => render());

// ── Initial render ─────────────────────────────────────────────────────────
render();
</script>
</body>
</html>`;
}

// ── Main / Watch ────────────────────────────────────────────────────────────

function generate() {
  console.log(`[governance-timeline] Parsing ${governanceDir}...`);
  const entries = parseGovernanceDir(governanceDir);
  if (entries.length === 0) {
    console.warn('[governance-timeline] No entries found. Check the directory path.');
    return;
  }
  const graphData = buildGraphData(entries);
  const html = generateHtml(graphData);
  fs.mkdirSync(reportsDir, { recursive: true });
  fs.writeFileSync(outputPath, html);
  console.log(`[governance-timeline] ${entries.length} entries, ${graphData.displayedSessions} sessions → ${outputPath}`);
  return outputPath;
}

// Initial generation
const out = generate();

if (!watchMode) {
  if (out) console.log(`\nOpen: open ${out}`);
  process.exit(0);
}

// Watch mode
console.log(`\n[watch] Watching ${governanceDir} for changes... (Ctrl+C to stop)`);

let debounceTimer = null;
function scheduleRegen() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debounceTimer = null;
    console.log(`[watch] Change detected, regenerating...`);
    generate();
    console.log(`[watch] Done. Reload browser to see updates.`);
  }, DEBOUNCE_MS);
}

fs.watch(governanceDir, (eventType, filename) => {
  if (filename && filename.endsWith('.jsonl')) scheduleRegen();
});

process.on('SIGINT', () => { console.log('\n[watch] Stopped.'); process.exit(0); });
