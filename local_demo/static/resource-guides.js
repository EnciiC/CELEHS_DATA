// README resource guides use a separate view from clinical synthetic files.
function resourceCard(resource) {
  const card = el('button', null, 'dataset-card resource-card'); card.type = 'button';
  card.setAttribute('aria-label', `Open ${resource.label}`);
  const top = el('div', null, 'card-top');
  top.append(el('span', resource.resource_type, 'site-label'), el('span', '↗', 'arrow'));
  const bottom = el('div', null, 'card-bottom');
  bottom.append(el('span', resource.storage), el('span', 'README guide · ' + resource.contact));
  card.append(top, el('h3', resource.label), el('p', resource.description), bottom);
  card.addEventListener('click', () => openResource(resource.id)); return card;
}
function resourceCategoryLabel(id) {
  return {datasets:'Datasets', derived:'Derived & reference data', models:'Models'}[id];
}
function categoryDescription(id) {
  return {datasets:'Clinical datasets, notes and annotations, and guides to external datasets.',
    derived:'Relation tables, matrices, knowledge graphs and terminology files. Public reference releases are included here.',
    models:'Saved model weights and checkpoints, with instructions for using them. No model entries have been documented yet.'}[id];
}
function chooseResourceCategory(id) {
  state.category=id;renderInventory();show('browse');window.scrollTo({top:0,behavior:'smooth'});
}
function renderResourceSidebar() {
  const sidebar=$('#sidebar-resources');sidebar.replaceChildren();
  for(const category of ['datasets','derived','models']){
    const count=state.resources.filter(r=>r.category===category).length+(category==='datasets'?state.datasets.length:0);
    const button=el('button',null,'resource-group-button');button.type='button';
    button.append(el('span',resourceCategoryLabel(category)),el('span',String(count),'resource-count'));
    button.classList.toggle('active',state.category===category);button.setAttribute('aria-pressed',String(state.category===category));
    button.addEventListener('click',()=>chooseResourceCategory(category));sidebar.append(button);
  }
  const category=state.category;
  const entries=[...(category==='datasets'?state.datasets.map(d=>({id:d.id,label:d.label,storage:d.platforms.join(' / '),clinical:true})):[]),
    ...state.resources.filter(r=>r.category===category)];
  const list=el('div',null,'sidebar-resource-list');list.setAttribute('aria-label',resourceCategoryLabel(category)+' entries');
  for(const resource of entries){
    const button=el('button',resource.label,'dataset-nav');button.type='button';button.dataset.resource=resource.id;
    button.append(el('small',resource.storage));
    button.addEventListener('click',()=>resource.clinical?openDataset(resource.id):openResource(resource.id));list.append(button);
  }
  if(!entries.length)list.append(el('p','No model READMEs added yet.','sidebar-empty'));
  sidebar.append(list);
}
function renderInventory() {
  for (const selector of ['#home-cards','#browse-cards']) {
    const node = $(selector);
    const clinical = state.category === 'datasets' ? state.datasets.map(datasetCard) : [];
    const guides = state.resources.filter(r => r.category === state.category).map(resourceCard);
    node.replaceChildren(...clinical, ...guides);
    if (!clinical.length && !guides.length) {
      const message = el('div', null, 'panel-box empty-resources');
      message.append(el('h3', 'No model resources documented yet'),
        el('p', 'No O2 model-checkpoint README is loaded. The model answering chat questions is separate from the lab resource inventory.'));
      node.append(message);
    }
  }
  for (const selector of ['#home-categories','#browse-categories']) {
    const nav = $(selector); if (!nav) continue;
    nav.replaceChildren(...['datasets','derived','models'].map(id => {
      const count = state.resources.filter(r => r.category === id).length + (id === 'datasets' ? state.datasets.length : 0);
      const button = smallButton(`${resourceCategoryLabel(id)} (${count})`, () => {state.category=id;renderInventory();}, '');
      button.classList.toggle('active', state.category === id); button.setAttribute('aria-pressed', String(state.category===id));
      return button;
    }));
  }
  $('#dataset-total').textContent = `${state.datasets.length+state.resources.length} documented entries`;
  $('#category-description').textContent=categoryDescription(state.category);
  renderResourceSidebar();
}
function resourceLocationView(resource) {
  const body = el('div');
  for (const location of resource.locations || []) {
    const row = el('div', null, 'resource-location'); row.append(el('strong', location.label));
    row.append(el('code', location.value, 'source-location'));
    if (location.kind === 'external' && /^https:\/\//.test(location.value)) row.append(link('Open external workspace', location.value));
    else row.append(smallButton('Copy path', () => navigator.clipboard.writeText(location.value).then(() => toast('Path copied')).catch(() => toast('Select and copy the path'))));
    body.append(row);
  }
  return disclosure('Show location', body);
}
function resourceBlocks(blocks) {
  const body = el('div');
  for (const block of blocks || []) {
    body.append(el('h4', block.title));
    if (block.text) body.append(markdownDocument(block.text));
    if (block.items?.length) {
      const list = el(block.kind === 'steps' ? 'ol' : 'ul');
      for (const text of block.items) {const item=el('li');item.append(markdownDocument(text));list.append(item);}
      body.append(list);
    }
  }
  return body;
}
async function openResourceReadme(id) {
  try {
    const doc = await api(`/api/resources/${id}/readme`);
    $('#document-title').textContent = doc.title;
    $('#document-scope').textContent = doc.scope_note;
    $('#document-text').replaceChildren(markdownDocument(doc.text));
    $('#document-dialog').showModal();
  } catch(error) {toast(error.message);}
}
function resourceFollowups(resource) {
  const actions = el('div', null, 'resource-followups');
  for (const [label, question] of [
    ['How to start', `How do I get started with ${resource.label}?`],
    ['Files and contents', `What files are included in ${resource.label}?`],
    ['Access requirements', `What access requirements apply to ${resource.label}?`],
    ['Related code', `What code is documented for ${resource.label}?`]]) {
    actions.append(smallButton(label, () => ask(question), ''));
  }
  actions.append(smallButton('Original README', () => openResourceReadme(resource.id), ''));
  return actions;
}
function renderResourceResults(result, box) {
  if (result.inventory) {
    const rows = el('div', null, 'resource-inventory');
    for (const dataset of result.inventory.datasets || []) rows.append(smallButton(`${dataset.label} · ${dataset.platforms.join(' / ')}`, () => openDataset(dataset.id)));
    for (const resource of result.inventory.resources || []) rows.append(smallButton(`${resource.label} · ${resource.storage}`, () => openResource(resource.id)));
    box.append(rows);
  }
  for (const resource of result.resources || []) {
    const section = el('section', null, 'answer-section resource-answer');
    const heading = el('h3', resource.label); heading.append(smallButton('View resource', () => openResource(resource.id)));
    const storage = el('p', null, 'resource-storage'); storage.append(el('strong','Storage: '), document.createTextNode(resource.storage));
    section.append(heading, el('span',resource.resource_type,'site-label'), storage, resourceBlocks(resource.blocks),
      resourceLocationView(resource), resourceFollowups(resource));
    box.append(section);
  }
}
async function openResource(id) {
  try {
    const record = await api(`/api/resources/${id}`); state.category=record.category;renderInventory();state.detail=record;state.previous=[id];state.pending=null;show('detail');
    const node = $('#detail-view'); node.replaceChildren(smallButton('← Back to resources', () => show('browse'), 'back-button'));
    const heading = el('div', null, 'page-heading');
    heading.append(el('span',resourceCategoryLabel(record.category).toUpperCase(),'eyebrow'),
      el('h1',record.label));
    const meta = el('div',null,'detail-meta');
    for (const [name,value] of [['Type',record.resource_type],['Storage',record.storage],['README contact',record.contact]]) {
      const cell=el('div');cell.append(el('small',name),el('span',value));meta.append(cell);
    }
    heading.append(meta);node.append(heading);
    const nav=el('nav',null,'detail-tabs resource-tabs');nav.setAttribute('aria-label','Resource information');
    const area=el('div');
    const views={'Overview':'overview','How to start':'start','Files and contents':'files','Access':'access','Code':'code','Limitations':'limitations'};
    function select(label) {
      [...nav.children].forEach(b=>b.classList.toggle('active',b.textContent===label));
      const panel=el('div',null,'panel-box resource-guide'); panel.append(resourceBlocks(record.views[views[label]]));
      if (label==='Overview' || label==='How to start' || label==='Files and contents') panel.append(resourceLocationView(record));
      if (label==='Code') {
        const urls=JSON.stringify(record.views.code).match(/https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+/g) || [];
        for (const url of [...new Set(urls)]) panel.append(link('Open registered repository',url));
      }
      panel.append(smallButton('Read original README',()=>openResourceReadme(id)),
        link('Download original README',`/api/resources/${id}/download/readme`),
        el('p',`README dated ${record.source_date}. Server paths and contents have not been rechecked by this tool. No data payloads or generated example rows are loaded.`,'note'));
      area.replaceChildren(panel);
    }
    for(const label of Object.keys(views))nav.append(smallButton(label,()=>select(label),''));
    node.append(nav,area,resourceFollowups(record));select('Overview');window.scrollTo({top:0,behavior:'smooth'});
  }catch(error){toast(error.message);}
}
