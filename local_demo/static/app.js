const $ = selector => document.querySelector(selector);
const state = {datasets: [], previous: [], pending: null, detail: null, busy: false};

function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
async function api(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(response.status === 429 ? 'Chat is busy or its request limit was reached. Please try later. You can still browse datasets.' : `Request failed (${response.status}). Please try again.`);
  return response.json();
}
function toast(message) {
  $('#toast').textContent = message; $('#toast').hidden = false;
  setTimeout(() => $('#toast').hidden = true, 2800);
}
function show(view) {
  for (const name of ['ask', 'browse', 'detail']) $(`#${name}-view`).hidden = view !== name;
  $('#nav-ask').classList.toggle('active', view === 'ask');
  $('#nav-browse').classList.toggle('active', view !== 'ask');
  $('#page-label').textContent = view === 'ask' ? 'Search' : view === 'browse' ? 'Datasets' : state.detail?.label || 'Dataset';
}
function datasetCard(dataset) {
  const card = el('button', null, 'dataset-card');
  card.type = 'button'; card.setAttribute('aria-label', `Open ${dataset.label}`);
  const top = el('div', null, 'card-top');
  top.append(el('span', dataset.site, 'site-label'), el('span', '↗', 'arrow'));
  const bottom = el('div', null, 'card-bottom');
  bottom.append(el('span', dataset.platforms.join(' / ')), el('span', `${dataset.fake_files} synthetic files · ${dataset.synthetic_rows.toLocaleString()} generated rows`));
  card.append(top, el('h3', dataset.label), el('p', dataset.description), bottom);
  card.addEventListener('click', () => openDataset(dataset.id));
  return card;
}
async function loadCatalog() {
  const data = await api('/api/datasets'); state.datasets = data.datasets;
  for (const selector of ['#home-cards', '#browse-cards']) {
    const node = $(selector); node.replaceChildren(...state.datasets.map(datasetCard));
  }
  $('#dataset-total').textContent = `${state.datasets.length} dataset groups`;
  $('#sidebar-datasets').replaceChildren(...state.datasets.map(d => {
    const b = el('button', d.label, 'dataset-nav');
    b.append(el('small', d.platforms.join(' / ')));
    b.addEventListener('click', () => openDataset(d.id)); return b;
  }));
}
async function status() {
  try {
    const data = await api('/api/health');
    const hosted = !data.local_only;
    const ready = data.model.reachable && data.model.installed;
    $('#status-dot').classList.toggle('ready', ready);
    $('#model-status').textContent = ready ? 'gpt-oss-20b available' : hosted && data.model.enabled ? 'Hosted model configured · not yet verified' : 'Dataset search available';
    $('#deployment-label').textContent = hosted ? 'Hosted on Render · model by Cloudflare' : 'Runs on this computer';
    $('#deployment-heading').textContent = hosted ? 'DATASET FINDER' : 'LOCAL DEMO';
    $('#reload').hidden = hosted;
    $('#hosted-notice').hidden = !hosted;
  } catch { $('#model-status').textContent = 'Server unavailable'; }
}
async function openDocument(id, kind, files = []) {
  try {
    const filter = files.length ? '?files=' + encodeURIComponent(files.join(',')) : '';
    const doc = await api(`/api/datasets/${id}/readme/${kind}${filter}`);
    const title = {notes:'Dataset notes',catalog:'How the fake data were made',synthetic:'How the fake data were made',original:'Original README',tracker:'Spreadsheet entry'}[kind] || 'README';
    $('#document-title').textContent = `${state.datasets.find(d => d.id === id)?.label || id} — ${doc.title || title}`;
    $('#document-scope').textContent = doc.scope_note || '';
    $('#document-text').replaceChildren();
    if (doc.html) {
      // Server produces escaped HTML from local DOCX; never insert model/user HTML.
      $('#document-text').innerHTML = doc.html;
    } else $('#document-text').append(markdownDocument(doc.text));
    if (kind === 'notes') {
      const details = el('div'); details.append(smallButton('Read generation notes', () => openDocument(id, 'synthetic')));
      $('#document-text').append(disclosure('How the fake data were made', details));
    }
    if (!$('#document-dialog').open) $('#document-dialog').showModal();
    $('#document-text').scrollTop = 0;
  } catch(error) { toast(error.message); }
}
function smallButton(label, action, cls = 'quiet-button') {
  const b = el('button', label, cls); b.type = 'button'; b.addEventListener('click', action); return b;
}
function link(label, url, cls = 'quiet-button') {
  const a = el('a', label, cls); a.href = url; return a;
}
function table(columns, rows, cls = '') {
  const wrap = el('div', null, 'table-scroll');
  const t = el('table', null, cls); const head = el('thead'); const tr = el('tr');
  columns.forEach(c => tr.append(el('th', c))); head.append(tr);
  const body = el('tbody');
  rows.forEach(row => { const r = el('tr'); columns.forEach(c => r.append(el('td', row[c] === '' ? 'NA' : row[c]))); body.append(r); });
  t.append(head, body); wrap.append(t); return wrap;
}
function markdownDocument(text) {
  const content = el('div'); const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim(); if (!line) continue;
    if (line.startsWith('```')) {
      const language = line.slice(3), source = []; i++;
      for (; i < lines.length && !lines[i].trim().startsWith('```'); i++) source.push(lines[i]);
      const pre = el('pre', null, 'document-code'); pre.append(el('code', source.join('\n')));
      content.append(disclosure(language === 'mermaid' ? 'View flowchart source' : 'View code', pre));
    } else if (line.startsWith('|') && lines[i + 1]?.match(/^\s*\|[\s:|-]+\|\s*$/)) {
      const cells = s => s.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
      const columns = cells(line), rows = []; i += 2;
      for (; i < lines.length && lines[i].trim().startsWith('|'); i++) {
        const values = cells(lines[i]); rows.push(Object.fromEntries(columns.map((c, j) => [c, values[j] || ''])));
      } i--;
      const grid = table(columns, rows);
      for (const cell of grid.querySelectorAll('td, th')) { const value = cell.textContent; cell.replaceChildren(); appendInline(cell, value); }
      content.append(grid);
    } else if (/^#{1,4} /.test(line)) content.append(el(line.startsWith('# ') ? 'h2' : 'h3', line.replace(/^#+ /, '')));
    else {
      const p = el('p');
      appendInline(p, line.replace(/^- /, '• '));
      content.append(p);
    }
  }
  return content;
}
function appendInline(parent, text) {
  for (const token of text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g)) {
    if (token.startsWith('`')) parent.append(el('code', token.slice(1,-1), 'column-name'));
    else if (token.startsWith('**')) parent.append(el('strong', token.slice(2,-2)));
    else parent.append(document.createTextNode(token));
  }
}
function disclosure(label, child, cls = '') {
  const details = el('details', null, `disclosure ${cls}`); details.append(el('summary', label), child); return details;
}
function pathDisclosure(file) {
  if (!file.location) return null;
  const body = el('div', null, 'path-body'); body.append(el('code', file.location, 'source-location'));
  for (const name of file.source_files || []) body.append(el('code', name, 'column-name'), document.createTextNode(' '));
  body.append(smallButton('Copy path', () => navigator.clipboard.writeText(file.location).then(() => toast('Path copied')).catch(() => toast('Select and copy the path'))));
  if (file.alternative_location) {
    const alt = el('div'); alt.append(el('code', file.alternative_location, 'source-location'));
    body.append(disclosure('Alternative path', alt));
  }
  return disclosure('Show file path', body, 'path-disclosure');
}
function dictionaryBody(items) {
  const body = el('div');
  for (const item of items) {
    const entry = el('div', null, 'dictionary-entry'); entry.append(el('strong', item.name));
    if (item.description) entry.append(el('p', item.description));
    if (item.location) entry.append(el('code', item.location, 'source-location'));
    if (item.status || !item.location) entry.append(el('p', item.status || 'Location not documented.', 'note'));
    body.append(entry);
  }
  if (!items.length) body.append(el('p', 'Dictionary location is not documented.', 'note'));
  return body;
}
function dictionaryDisclosure(items) { return disclosure('Show dictionary', dictionaryBody(items)); }
function columnTable(record, file) {
  const rows = record.column_descriptions.filter(r => r.File === file.file).map(r => ({
    Column:r.Column, Meaning:r.Meaning, Type:r['Source R class'] || r['Demo type']}));
  return table(['Column','Meaning','Type'], rows, 'field-table');
}
async function sampleRows(id, file, area, withColumns = false) {
  area.replaceChildren(el('p', 'Loading fake rows…', 'note'));
  try {
    const data = await api(`/api/datasets/${id}/files/${encodeURIComponent(file.file)}/preview?limit=5`);
    area.replaceChildren(el('p', 'FAKE DATA · First 5 generated rows. These are not real patient records.', 'sample-note'), table(data.columns, data.rows, 'preview-table'));
    if (withColumns) {
      const record = state.detail?.dataset_id === id ? state.detail : await api(`/api/datasets/${id}`);
      area.append(el('h4', 'Column explanations'), columnTable(record, file));
    }
  } catch (error) { area.replaceChildren(el('p', error.message, 'answer-warning')); }
}
function answerFile(section, file) {
  const card = el('div', null, 'answer-file'); const title = el('p', null, 'file-schema');
  title.append(el('strong', file.name));
  if (file.show_columns) {
    title.append(document.createTextNode(': '));
    file.columns.forEach((name, i) => { if (i) title.append(document.createTextNode(', ')); title.append(el('code', name, 'column-name')); });
  }
  card.append(title);
  if (file.show_types && file.types?.length) card.append(el('p', `Types: ${file.types.join(', ')}`, 'note'));
  const links = el('div', null, 'resource-links'); const path = pathDisclosure(file);
  if (path) links.append(path);
  if (file.dictionaries?.length || file.file) links.append(dictionaryDisclosure(file.dictionaries || []));
  if (file.readme_kind) links.append(smallButton('Original laboratory README', () => openDocument(section.dataset.id, file.readme_kind)));
  card.append(links);
  if (file.preview_available === false) card.append(el('p', 'Documentation only · No laboratory sample rows are loaded.', 'note'));
  if (file.file) {
    const preview = el('div', null, 'preview-area');
    const button = smallButton('Show 5 fake rows', () => {
      if (!preview.hasChildNodes()) { sampleRows(section.dataset.id, file, preview, true); button.textContent = 'Hide fake rows'; }
      else { preview.hidden = !preview.hidden; button.textContent = preview.hidden ? 'Show 5 fake rows' : 'Hide fake rows'; }
    }, 'text-button');
    card.append(button, preview);
    if (file.show_preview) { sampleRows(section.dataset.id, file, preview, true); button.textContent = 'Hide fake rows'; }
  }
  return card;
}
function formattedFact(fact) {
  if (fact.format === 'markdown') {
    const content = markdownDocument(fact.text); content.className = 'document-excerpt';
    if (fact.category === 'original') return disclosure('Read relevant README excerpt', content);
    return content;
  }
  if (fact.text.includes('\nSource location: ')) {
    const [description, path] = fact.text.split('\nSource location: ');
    const content = el('div'); content.append(el('p', description, 'fact'), pathDisclosure({location:path.split('\n')[0]}));
    return content;
  }
  const p = el('p', null, `fact ${fact.category}`);
  if (fact.category === 'original') return disclosure('Read relevant README excerpt', el('p', fact.text, 'fact'));
  const colon = fact.text.indexOf(':');
  if (colon > -1 && colon < 60) { p.append(el('strong', fact.text.slice(0, colon + 1)), document.createTextNode(' ' + fact.text.slice(colon + 1).trim())); }
  else p.textContent = fact.text;
  return p;
}
function renderAnswer(result, box) {
  box.replaceChildren();
  const header = el('div', null, 'answer-header');
  const engineName = result.engine === 'hosted_llm' ? 'Hosted LLM' : result.engine === 'local_llm' ? 'Local LLM' : result.engine === 'guide' ? 'Guide' : 'Dataset search';
  header.append(el('span', 'Dataset Finder', 'assistant-name'), el('span', `${engineName} · ${result.elapsed_seconds}s`, 'engine-label'));
  box.append(header);
  if (result.warning) box.append(el('p', result.warning, 'answer-warning'));
  box.append(el('p', result.intro || result.answer, 'answer-intro'));
  if (result.comparison) {
    const summary = el('div', null, 'comparison-summary');
    for (const line of result.comparison.details) summary.append(markdownDocument(line));
    summary.append(el('p', result.comparison.caution, 'note')); box.append(summary);
  }
  for (const message of result.messages || []) box.append(el('p', message, 'guide-message'));
  if (result.actions?.length) {
    const actions = el('div', null, 'suggested-actions');
    for (const action of result.actions) actions.append(smallButton(action.label, () => {
      if (action.view === 'browse') show('browse');
      else if (action.query) { $('#question').value = action.query; ask(action.query); }
    }));
    box.append(actions);
  }
  for (const section of result.compact ? [] : result.datasets) {
    const block = el('section', null, 'answer-section');
    const heading = el('h3', section.dataset.label);
    heading.append(smallButton('View dataset', () => openDataset(section.dataset.id)));
    block.append(heading);
    for (const fact of section.facts) if (!(section.date_summary && fact.category === 'dates')) block.append(formattedFact(fact));
    if (section.date_summary) {
      block.append(table(section.date_summary.columns, section.date_summary.rows, 'date-table'),
        el('p', section.date_summary.note, 'note'), el('p', section.date_summary.warning, 'answer-warning'));
    }
    if (result.intent === 'dictionary') block.append(dictionaryBody(section.dictionaries || []));
    else for (const file of section.files || []) block.append(answerFile(section, file));
    if (section.offer_preview && section.files?.some(f => f.file)) block.append(el('p', 'Want to see sample rows? The fake examples above show the file structure.', 'note'));
    if (section.additional_note) block.append(el('p', section.additional_note, 'fact'));
    const links = el('div', null, 'answer-links');
    if (result.intent === 'location' || result.intent === 'overview') {
      links.append(smallButton('See monthly columns', () => ask(`Show ${section.dataset.label} monthly columns`), ''),
                   smallButton('Show fake rows', () => ask(`Show sample rows for ${section.dataset.label} monthly counts`), ''));
    }
    const documentationOnly = section.files?.length && section.files.every(f => f.preview_available === false);
    if (result.intent !== 'project' && !documentationOnly) links.append(smallButton('Dataset notes', () => openDocument(section.dataset.id, 'notes', (section.files || []).map(f => f.file).filter(Boolean)), ''));
    const originals = section.dataset.original_documents || [{kind:'original',label:'Original README'}];
    if (originals.length > 1) {
      const choices = el('div');
      for (const doc of originals) choices.append(smallButton(doc.label, () => openDocument(section.dataset.id, doc.kind)));
      links.append(disclosure('Original READMEs', choices));
    } else links.append(smallButton('Original README', () => openDocument(section.dataset.id, 'original'), ''));
    if (result.intent === 'project') links.append(smallButton('Open full MAJOR IBD project README', () => openDocument(section.dataset.id, 'ibd_project'), ''));
    if (section.dataset.has_tracker) links.append(smallButton('Spreadsheet entry', () => openDocument(section.dataset.id, 'tracker'), ''));
    block.append(links); box.append(block);
  }
}
async function ask(query) {
  if (state.busy || !query.trim()) return;
  show('ask'); state.busy = true; $('#ask-button').disabled = true; $('#ask-button').textContent = 'Searching…';
  $('#initial-catalog').hidden = true;
  const user = el('div', null, 'user-message'); user.append(el('p', query));
  const box = el('article', null, 'agent-message'); box.append(el('p', 'Finding the relevant dataset information…', 'thinking'));
  $('#conversation').append(user, box);
  box.scrollIntoView({behavior:'smooth', block:'start'});
  try {
    const result = await api('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query, previous_dataset_ids:state.previous, pending_topic:state.pending, use_llm:true})});
    state.previous = result.context_dataset_ids ?? result.datasets.map(s => s.dataset.id);
    state.pending = result.pending_topic || null;
    renderAnswer(result, box); await status();
  } catch(error) { box.replaceChildren(el('p', error.message, 'answer-warning')); }
  finally { state.busy = false; $('#ask-button').disabled = false; $('#ask-button').textContent = 'Search datasets →'; }
}
function filesAndColumnsPanel(record) {
  const panel = el('div'), picker = el('div', null, 'file-picker'), area = el('div');
  function select(file) {
    [...picker.children].forEach(button => button.classList.toggle('active', button.dataset.file === file.file));
    const detail = record.file_details.find(item => item.file === file.file);
    const card = el('div', null, 'panel-box'), header = el('div', null, 'file-heading');
    header.append(el('h3', detail.name), el('span', 'SYNTHETIC DATA', 'fake-label'));
    card.append(header, el('p', `${file.rows.toLocaleString()} generated rows. ${file.row_meaning}`));
    card.append(el('code', file.file, 'column-name'));
    if (detail.location) card.append(pathDisclosure(detail));
    const actions = el('div', null, 'file-actions');
    const preview = el('div', null, 'preview-area');
    const more = smallButton('Show 10 rows', async () => {
      try {
        const data = await api(`/api/datasets/${record.dataset_id}/files/${encodeURIComponent(file.file)}/preview?limit=10`);
        preview.replaceChildren(el('p', 'FAKE DATA · First 10 generated rows, not real patient records.', 'sample-note'),
          table(data.columns, data.rows, 'preview-table'), el('h4', 'Column explanations'), columnTable(record, file));
      } catch(error) { toast(error.message); }
    });
    more.disabled = true;
    actions.append(more, link('Download synthetic CSV', `/api/datasets/${record.dataset_id}/download/${encodeURIComponent(file.file)}`));
    card.append(actions, preview); area.replaceChildren(card);
    sampleRows(record.dataset_id, file, preview, true).finally(() => { more.disabled = false; });
  }
  function selectDocumented(file) {
    [...picker.children].forEach(button => button.classList.toggle('active', button.dataset.file === file.id));
    const card = el('div', null, 'panel-box'), heading = el('div', null, 'file-heading');
    heading.append(el('h3', file.name), el('span', 'DOCUMENTATION ONLY', 'documented-label'));
    card.append(heading, el('p', file.description), el('p', file.row_meaning), el('p', 'Owner: ' + file.owner));
    for (const name of file.source_files) card.append(el('code', name, 'column-name'), document.createTextNode(' '));
    card.append(pathDisclosure(file), el('p', 'No real laboratory records or fake laboratory examples are loaded. The source files stay on the documented server.', 'note'),
      el('h4', 'Column explanations'), table(['Column','Meaning'], file.column_descriptions, 'field-table'),
      disclosure('Processing script', el('code', file.processing_script, 'source-location')),
      smallButton('Read original laboratory README', () => openDocument(record.dataset_id, file.readme_kind)));
    area.replaceChildren(card);
  }
  for (const file of record.files) {
    const detail = record.file_details.find(item => item.file === file.file);
    const button = smallButton(detail.name, () => select(file), ''); button.dataset.file = file.file; picker.append(button);
  }
  for (const file of record.documented_files || []) {
    const button = smallButton(file.name, () => selectDocumented(file), ''); button.dataset.file = file.id; picker.append(button);
  }
  panel.append(picker, area, link('Download full column dictionary', `/api/datasets/${record.dataset_id}/download/column_dictionary.csv`));
  const sources = el('div', null, 'panel-box'); sources.append(el('h3', 'Source locations and processing code'));
  const shownPaths = new Set(record.file_details.map(file => file.location));
  record.resources.filter(r => r.location && !shownPaths.has(r.location)).forEach(r => {
    const row = el('div', null, 'source-row'); row.append(el('h3', r.name), pathDisclosure(r));
    sources.append(row);
  }); panel.append(disclosure('Other source locations and processing scripts', sources));
  select(record.files.find(f => /monthly/i.test(f.file) && !/nlp/i.test(f.file)) || record.files[0]); return panel;
}
function readmesPanel(record) {
  const panel = el('div');
  const documents = [{kind:'notes',label:'Dataset notes',description:'A short guide to the prepared example rows and columns.'},
    ...(record.original_documents || [{kind:'original',label:"Sara's original documentation",description:'Original team documentation.',file:'README_original.docx'}])];
  for (const doc of documents) {
    const kind = doc.kind;
    const card = el('div', null, 'panel-box readme-card'); const info = el('div');
    info.append(el('h3', doc.label), el('p', doc.description));
    const actions = el('div', null, 'file-actions'); actions.append(smallButton('Read document', () => openDocument(record.dataset_id, kind)));
    if (doc.file) actions.append(link(doc.file.endsWith('.md') ? 'Download original Markdown' : doc.file.endsWith('.txt') ? 'Download README text' : 'Download original DOCX', `/api/datasets/${record.dataset_id}/download/${encodeURIComponent(doc.file)}`));
    card.append(info, actions); panel.append(card);
  }
  if (record.tracker_source) {
    const tracker = el('div', null, 'panel-box readme-card');
    tracker.append(el('h3', 'Spreadsheet entry'), smallButton('Read entry', () => openDocument(record.dataset_id, 'tracker'))); panel.append(tracker);
  }
  const technical = el('div'); technical.append(el('p', 'How the synthetic example files were generated.', 'note'),
    smallButton('Read generation notes', () => openDocument(record.dataset_id, 'synthetic')));
  panel.append(disclosure('How the fake data were made', technical)); return panel;
}
function dictionariesPanel(record) {
  const panel = el('div');
  for (const dictionary of record.dictionaries || []) {
    const card = el('div', null, 'panel-box'); card.append(el('h3', dictionary.name), el('p', dictionary.description));
    if (dictionary.location) card.append(el('code', dictionary.location, 'source-location'));
    if (dictionary.status || !dictionary.location) card.append(el('p', dictionary.status || 'Not documented', 'note'));
    panel.append(card);
  }
  panel.append(el('p', 'Generated code examples are not verified clinical dictionaries. Source dictionaries have not been copied into this demo.', 'note'));
  return panel;
}
async function openDataset(id) {
  try {
    const record = await api(`/api/datasets/${id}`); state.detail = record;
    state.previous = [id]; state.pending = null; show('detail');
    const node = $('#detail-view'); node.replaceChildren();
    node.append(smallButton('← Back to datasets', () => show('browse'), 'back-button'));
    const heading = el('div', null, 'page-heading');
    heading.append(el('span', 'DATASET DETAILS', 'eyebrow'), el('h1', record.label), el('p', record.description));
    const meta = el('div', null, 'detail-meta');
    for (const [label,value] of [['Site',record.site],['Storage',record.storage_platform.join(' / ')],['Contact',record.contact]]) {
      const cell = el('div'); cell.append(el('small',label),el('span',value)); meta.append(cell);
    } heading.append(meta); node.append(heading);
    const tabs = el('nav', null, 'detail-tabs'); tabs.setAttribute('aria-label','Dataset information'); const area = el('div');
    const views = {'Files and columns':filesAndColumnsPanel, READMEs:readmesPanel, Dictionaries:dictionariesPanel};
    function select(name) { [...tabs.children].forEach(b => b.classList.toggle('active', b.textContent === name)); area.replaceChildren(views[name](record)); }
    for (const name of Object.keys(views)) tabs.append(smallButton(name, () => select(name), ''));
    node.append(tabs, area); select('Files and columns'); window.scrollTo({top:0,behavior:'smooth'});
  } catch(error) { toast(error.message); }
}
$('#question-form').addEventListener('submit', event => {event.preventDefault(); ask($('#question').value);});
$('#question').addEventListener('keydown', event => {if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {event.preventDefault();ask(event.target.value);}});
document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click', () => {$('#question').value = button.dataset.query; ask(button.dataset.query);}));
$('#nav-ask').addEventListener('click', () => show('ask'));
$('#nav-browse').addEventListener('click', () => show('browse'));
$('#close-document').addEventListener('click', () => $('#document-dialog').close());
$('#reload').addEventListener('click', async () => {try {await api('/api/catalog/reload',{method:'POST'});await loadCatalog();toast('Dataset information refreshed');}catch(error){toast(error.message);}});
loadCatalog().then(status).catch(error => toast(error.message));
