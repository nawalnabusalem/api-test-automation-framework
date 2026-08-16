'use strict';

const report = JSON.parse(document.getElementById('report-data').textContent);
const byId = id => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

function prettyJson(value) {
  if (value == null) return '';
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  byId('theme').textContent = theme === 'light' ? 'Dark mode' : 'Light mode';
}

function initializeTheme() {
  setTheme(localStorage.getItem('api-report-theme') || 'dark');
  byId('theme').addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('api-report-theme', nextTheme);
    setTheme(nextTheme);
  });
}

function renderCard(label, value, className = '') {
  return `<div class='card'><span class='muted'>${label}</span><b class='${className}'>${value}</b></div>`;
}

function renderHeaders(headers) {
  const rows = Object.entries(headers || {}).map(([key, value]) =>
    `<tr><th>${escapeHtml(key)}</th><td>${escapeHtml(value)}</td></tr>`
  ).join('');
  return `<table class='headers-table'>${rows || `<tr><td class='muted'>No headers captured</td></tr>`}</table>`;
}

function renderTabs(group, items) {
  const buttons = items.map((item, index) =>
    `<button class='tab ${index ? '' : 'active'}' data-group='${group}' data-tab='${group}-${index}'>${escapeHtml(item.label)}</button>`
  ).join('');
  const panels = items.map((item, index) =>
    `<div id='${group}-${index}' class='tab-content ${index ? '' : 'active'}'>${item.html}</div>`
  ).join('');
  return `<div class='tabs'>${buttons}</div>${panels}`;
}

function renderScalar(value) {
  if (value === null) return `<span class='json-null'>null</span>`;
  if (typeof value === 'string') return `<span class='json-string'>&quot;${escapeHtml(value)}&quot;</span>`;
  if (typeof value === 'number') return `<span class='json-number'>${value}</span>`;
  if (typeof value === 'boolean') return `<span class='json-boolean'>${value}</span>`;
  return `<span>${escapeHtml(value)}</span>`;
}

function renderJsonTree(value, depth = 0, key = '') {
  const keyHtml = key === '' ? '' : `<span class='json-key'>&quot;${escapeHtml(key)}&quot;</span>: `;
  if (value === null || typeof value !== 'object') {
    return `<div class='json-row'>${keyHtml}${renderScalar(value)}</div>`;
  }

  const entries = Object.entries(value);
  const isArray = Array.isArray(value);
  const openBracket = isArray ? '[' : '{';
  const closeBracket = isArray ? ']' : '}';
  const itemLabel = isArray ? 'items' : 'fields';
  const children = entries.map(([childKey, childValue]) =>
    renderJsonTree(childValue, depth + 1, childKey)
  ).join('');

  return `<details class='json-node ${depth ? '' : 'root'}' ${depth < 2 ? 'open' : ''}>
    <summary>${keyHtml}<span class='json-bracket'>${openBracket}</span><span class='json-count'>${entries.length} ${itemLabel}</span></summary>
    ${children}<div class='json-close'>${closeBracket}</div>
  </details>`;
}

function parseJsonValue(value) {
  if (typeof value !== 'string') return value;
  try { return JSON.parse(value); } catch { return value; }
}

function renderBodyView(id, value) {
  const text = prettyJson(value) || 'No body';
  return `<div class='body-actions'><button class='copy-target' data-target='${id}'>Copy JSON</button></div>
    <pre id='${id}' class='copy-source'>${escapeHtml(text)}</pre>
    <div class='json-scroll'>${renderJsonTree(parseJsonValue(value))}</div>`;
}

function renderTextView(id, text) {
  return `<div class='body-actions'><button class='copy-target' data-target='${id}'>Copy</button></div>
    <pre id='${id}' class='json-scroll'>${escapeHtml(text)}</pre>`;
}

function buildCurl(request) {
  if (!request) return '';
  const quote = value => String(value).replace(/'/g, "'\\''");
  const headers = Object.entries(request.headers || {})
    .filter(([key]) => !['content-length', 'host'].includes(key.toLowerCase()))
    .map(([key, value]) => ` -H '${quote(`${key}: ${value}`)}'`).join('');
  const body = request.body == null ? '' : ` --data '${quote(prettyJson(request.body))}'`;
  return `curl -X ${request.method || 'GET'} '${quote(request.url || '')}'${headers}${body}`;
}

function renderLogs(logs) {
  if (!logs?.length) {
    return `<div class='log-panel'><h3>Logs</h3><p class='muted'>No logs captured.</p></div>`;
  }
  const lines = logs.map(log => {
    const level = (log.level || 'INFO').toUpperCase();
    const searchText = `${level} ${log.message || ''}`.toLowerCase();
    return `<span class='log-line log-${escapeHtml(level.toLowerCase())}' data-search='${escapeHtml(searchText)}'>${escapeHtml(log.timestamp || '')} [${escapeHtml(level)}] ${escapeHtml(log.message || '')}</span>`;
  }).join('\n');
  return `<div class='log-panel'><div class='log-toolbar'><h3>Logs</h3><input class='log-search' placeholder='Search this test case logs'></div><pre class='log-output'>${lines}</pre><p class='muted log-empty' hidden>No logs match your search.</p></div>`;
}

function initializePageHeader() {
  document.title = report.title || 'API Test Report';
  byId('title').textContent = report.title || 'API Test Report';
  byId('meta').textContent = `${report.environment || 'unknown environment'} - ${report.generated_at || ''}`;
  if (report.index_url) {
    byId('back').href = report.index_url;
    byId('back').hidden = false;
  }
}

function renderSummaryCards() {
  const summary = report.summary;
  byId('cards').innerHTML = [
    renderCard('Pass rate', `${summary.pass_rate}%`, 'passed'),
    renderCard('Total', summary.total), renderCard('Passed', summary.passed, 'passed'),
    renderCard('Failed', summary.failed, 'failed'), renderCard('Errors', summary.error, 'error'),
    renderCard('Skipped', summary.skipped, 'skipped'),
    renderCard('P95 latency', `${summary.p95_latency_ms} ms`),
    renderCard('Duration', `${summary.duration_ms} ms`)
  ].join('');
}

function resultDefinitions() {
  return [['passed', 'Passed', 'pass'], ['failed', 'Failed', 'fail'], ['skipped', 'Skipped', 'skip'], ['error', 'Error', 'error']];
}

function renderProgressChart() {
  const summary = report.summary;
  const total = Number(summary.total || 0);
  let position = 0;
  const stops = resultDefinitions().map(([key, , color]) => {
    const percentage = total ? Number(summary[key] || 0) / total * 100 : 0;
    const start = position;
    position += percentage;
    return `var(--${color}) ${start}% ${position}%`;
  });
  byId('progress-total').textContent = `${total} tests`;
  byId('progress-ring').style.background = total ? `conic-gradient(${stops.join(',')})` : 'var(--control)';
  byId('ring-rate').textContent = `${summary.pass_rate}%`;
  byId('progress-legend').innerHTML = resultDefinitions().map(([key, label, color]) => {
    const count = Number(summary[key] || 0);
    const percentage = total ? count / total * 100 : 0;
    return `<div class='legend-item'><span class='legend-dot ${key}' style='background:var(--${color})'></span><strong>${label}: ${count}</strong><small>${percentage.toFixed(1)}%</small></div>`;
  }).join('');
}

function renderSuiteSummary() {
  const rows = (report.suite_summary || []).map(suite => `<tr>
    <td><button class='suite-filter' data-suite='${escapeHtml(suite.name)}'>${escapeHtml(suite.name)}</button></td>
    <td>${suite.total}</td><td class='passed'>${suite.passed}</td><td class='failed'>${suite.failed}</td>
    <td class='error'>${suite.error}</td><td>${Number(suite.duration_ms).toFixed(0)} ms</td>
  </tr>`).join('');
  byId('suite-summary').innerHTML = `<table class='summary-table'><thead><tr><th>Suite</th><th>Total</th><th class='passed'>Pass</th><th class='failed'>Fail</th><th class='error'>Error</th><th>Duration</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderRunInformation() {
  const labels = {base_url:'Base URL', branch:'Branch', commit:'Commit', python:'Python', framework:'Framework', started_at:'Started'};
  const info = report.run_info || {};
  byId('run-info').innerHTML = Object.entries(labels).map(([key, label]) =>
    `<div><dt>${label}</dt><dd>${escapeHtml(info[key] || '--')}</dd></div>`
  ).join('');
}

function populateFilterOptions() {
  const methods = [...new Set(report.tests.map(test => test.request?.method).filter(Boolean))].sort();
  const suites = [...new Set(report.tests.map(test => test.suite || 'Unassigned'))].sort();
  byId('method').innerHTML = `<option value='all'>All methods</option>${methods.map(value => `<option value='${escapeHtml(value)}'>${escapeHtml(value)}</option>`).join('')}`;
  byId('suite').innerHTML = `<option value='all'>All suites</option>${suites.map(value => `<option value='${escapeHtml(value)}'>${escapeHtml(value)}</option>`).join('')}`;
}

function readFilters() {
  return {q:byId('search').value.trim(), status:byId('status').value, method:byId('method').value, suite:byId('suite').value};
}

function syncFiltersToUrl() {
  const params = new URLSearchParams();
  Object.entries(readFilters()).forEach(([key, value]) => {
    if (value && value !== 'all') params.set(key, value);
  });
  const query = params.toString();
  history.replaceState(null, '', `${location.pathname}${query ? `?${query}` : ''}${location.hash}`);
}

function restoreFiltersFromUrl() {
  const params = new URLSearchParams(location.search);
  const values = {search:params.get('q') || '', status:params.get('status') || 'all', method:params.get('method') || 'all', suite:params.get('suite') || 'all'};
  Object.entries(values).forEach(([id, value]) => {
    const element = byId(id);
    if (id === 'search' || [...element.options].some(option => option.value === value)) element.value = value;
  });
}

function filteredTests() {
  const filters = readFilters();
  const query = filters.q.toLowerCase();
  const rank = {error:0, failed:1, skipped:2, passed:3};
  return report.tests.filter(test =>
    (filters.status === 'all' || test.status === filters.status) &&
    (filters.method === 'all' || test.request?.method === filters.method) &&
    (filters.suite === 'all' || (test.suite || 'Unassigned') === filters.suite) &&
    JSON.stringify([test.name, test.suite, test.status, test.request?.method, test.request?.url, test.response?.status_code, test.error]).toLowerCase().includes(query)
  ).sort((left, right) => (rank[left.status] ?? 9) - (rank[right.status] ?? 9) || Number(right.duration_ms || 0) - Number(left.duration_ms || 0));
}

function failureSnippet(error) {
  return String(error || '').split(/\r?\n/).map(line => line.trim()).find(Boolean) || '';
}

function renderTestRow(test) {
  const statusCode = test.response?.status_code;
  const statusClass = statusCode == null ? 'http-neutral' : Number(statusCode) >= 400 ? 'http-bad' : 'http-ok';
  const method = String(test.request?.method || '').toUpperCase();
  const preview = ['failed', 'error'].includes(test.status) ? failureSnippet(test.error) : '';
  return `<article class='test' data-status='${escapeHtml(test.status)}'><div class='test-head'>
    <span class='badge ${escapeHtml(test.status)}'>${escapeHtml(test.status)}</span>
    <strong class='test-name'><a class='detail-link' href='${escapeHtml(test.detail_url)}'>${escapeHtml(test.name)}</a><small>${escapeHtml(test.suite || 'Unassigned')}</small></strong>
    <span class='endpoint secondary muted'><span class='method-pill method-${escapeHtml(method.toLowerCase())}'>${escapeHtml(method || '--')}</span> ${escapeHtml(test.request?.url || 'No request captured')}</span>
    <span class='http-status ${statusClass}'>${escapeHtml(statusCode ?? '--')}</span><span class='duration'>${Number(test.duration_ms || 0).toFixed(0)} ms</span>
    ${preview ? `<div class='failure-preview' title='${escapeHtml(preview)}'>${escapeHtml(preview)}</div>` : ''}
  </div></article>`;
}

function renderMainDashboard() {
  const tests = filteredTests();
  byId('tests').innerHTML = tests.length ? tests.map(renderTestRow).join('') : `<div class='empty'>No tests match the current filter.</div>`;
  syncFiltersToUrl();
}

function renderRequestPanel(request) {
  return renderTabs('request', [
    {label:'Body', html:renderBodyView('request-body', request.body)},
    {label:`Headers (${Object.keys(request.headers || {}).length})`, html:`<div class='body-actions'><button class='copy-value' data-value='${escapeHtml(prettyJson(request.headers || {}))}'>Copy</button></div>${renderHeaders(request.headers)}`},
    {label:'cURL', html:renderTextView('request-curl', buildCurl(request))}
  ]);
}

function renderResponsePanel(response) {
  return renderTabs('response', [
    {label:'Body', html:renderBodyView('response-body', response.body)},
    {label:`Headers (${Object.keys(response.headers || {}).length})`, html:`<div class='body-actions'><button class='copy-value' data-value='${escapeHtml(prettyJson(response.headers || {}))}'>Copy</button></div>${renderHeaders(response.headers)}`}
  ]);
}

function renderTestInformation(test) {
  const info = test.info || {};
  const cards = `<section class='detail-summary'>${renderCard('Status', escapeHtml(test.status), test.status)}${renderCard('Suite', escapeHtml(test.suite || '--'))}${renderCard('Duration', `${Number(test.duration_ms || 0).toFixed(0)} ms`)}${renderCard('Source', escapeHtml(info.file || '--'))}${renderCard('Tags', escapeHtml((info.tags || []).join(', ') || '--'))}</section>`;
  const purpose = info.description ? `<div class='card section'><span class='muted'>Test purpose</span><p>${escapeHtml(info.description)}</p></div>` : '';
  return cards + purpose;
}

function renderTestDetail(test) {
  const request = test.request || {};
  const response = test.response || {};
  const responseClass = Number(response.status_code) >= 400 ? 'failed' : 'passed';
  const failure = test.error ? `<div class='card section'><h3 class='failed'>Failure</h3><pre>${escapeHtml(test.error)}</pre></div>` : '';
  byId('tests').innerHTML = `${renderTestInformation(test)}
    <div class='request-line'><span class='method'>${escapeHtml(request.method || '--')}</span><span class='url'>${escapeHtml(request.url || 'No request URL')}</span><span class='secondary muted'>HTTP request</span></div>
    ${failure}<section class='workspace'><div class='pm-panel'><div class='pm-title'><strong>Request</strong></div>${renderRequestPanel(request)}</div>
    <div class='pm-panel'><div class='pm-title'><strong>Response</strong><span><b class='${responseClass}'>${escapeHtml(response.status_code ?? '--')} ${escapeHtml(response.reason || '')}</b> &middot; ${escapeHtml(response.elapsed_ms ?? '--')} ms</span></div>${renderResponsePanel(response)}</div></section>
    <section class='detail-extra'>${renderLogs(test.logs)}</section>`;
}

function clearFilters() {
  byId('search').value = '';
  ['status', 'method', 'suite'].forEach(id => byId(id).value = 'all');
  renderMainDashboard();
}

function selectSuite(suite) {
  byId('suite').value = suite;
  renderMainDashboard();
  byId('toolbar').scrollIntoView({behavior:'smooth', block:'center'});
}

function activateTab(button) {
  document.querySelectorAll(`.tab[data-group='${button.dataset.group}']`).forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll(`[id^='${button.dataset.group}-'].tab-content`).forEach(panel => panel.classList.remove('active'));
  button.classList.add('active');
  byId(button.dataset.tab).classList.add('active');
}

function filterLogs(input) {
  const panel = input.closest('.log-panel');
  const query = input.value.toLowerCase();
  const lines = [...panel.querySelectorAll('.log-line')];
  lines.forEach(line => line.hidden = !line.dataset.search.includes(query));
  panel.querySelector('.log-empty').hidden = lines.some(line => !line.hidden);
}

function showCopiedState(button) {
  const original = button.textContent;
  button.textContent = 'Copied';
  setTimeout(() => button.textContent = original, 900);
}

function copyText(value, button) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(value).then(() => showCopiedState(button));
    return;
  }
  const textArea = document.createElement('textarea');
  textArea.value = value;
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand('copy');
  textArea.remove();
  showCopiedState(button);
}

function handleDocumentClick(event) {
  const target = event.target;
  if (target.matches('.suite-filter')) selectSuite(target.dataset.suite);
  if (target.matches('.tab')) activateTab(target);
  if (target.matches('.copy-target')) copyText(byId(target.dataset.target).textContent, target);
  if (target.matches('.copy-value')) copyText(target.dataset.value, target);
}

function bindDashboardEvents() {
  byId('search').addEventListener('input', renderMainDashboard);
  ['status', 'method', 'suite'].forEach(id => byId(id).addEventListener('change', renderMainDashboard));
  byId('clear-filters').addEventListener('click', clearFilters);
}

function bindSharedEvents() {
  document.addEventListener('click', handleDocumentClick);
  document.addEventListener('input', event => {
    if (event.target.matches('.log-search')) filterLogs(event.target);
  });
}

function initializeDashboard() {
  byId('expand').hidden = true;
  byId('collapse').hidden = true;
  renderSummaryCards();
  renderProgressChart();
  renderSuiteSummary();
  renderRunInformation();
  populateFilterOptions();
  restoreFiltersFromUrl();
  bindDashboardEvents();
  renderMainDashboard();
}

function initializeDetailPage() {
  renderTestDetail(report.tests[0] || {});
}

function initializeReport() {
  initializeTheme();
  initializePageHeader();
  bindSharedEvents();
  if (report.is_index) initializeDashboard();
  else initializeDetailPage();
}

initializeReport();
