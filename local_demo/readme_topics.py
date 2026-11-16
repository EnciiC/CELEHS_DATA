"""Register data described inside project READMEs as searchable source excerpts.

Registrations name headings and file-table rows, not inferred facts or new schemas.
The same adapter can describe a registry, linked cohort, labels or another input.
"""
import re
import time

from .readme_resources import section, source, fact, tables, clean


def words(text):
    return re.findall(r'[a-z0-9_]+', text.lower())


def file_aliases(file):
    return [file['name'], *file.get('aliases', []),
            *([file['source_file']] if file.get('source_file') else [])]


def named_files(files, query):
    q=' '+' '.join(words(query))+' '
    return [file for file in files if any(' '+' '.join(words(alias))+' ' in q
                                          for alias in file_aliases(file))]


def excerpt(document, spec):
    text = section(document, spec['heading'])
    if spec.get('line_prefix'):
        text=next((line for line in text.splitlines() if line.startswith(spec['line_prefix'])),None)
        if text is None: raise ValueError('Missing registered README line')
    elif spec.get('paragraph_prefix'):
        text = next((p for p in re.split(r'\n\s*\n', text)
                     if p.startswith(spec['paragraph_prefix'])), None)
        if text is None:
            raise ValueError('Missing registered README paragraph')
    elif spec.get('paragraphs'):
        text = '\n\n'.join(re.split(r'\n\s*\n', text)[:spec['paragraphs']])
    return text


def prepare_topics(record, docs):
    prepared = []
    for spec in record.get('readme_topics', []):
        if not re.fullmatch(r'[a-z][a-z0-9_]+', spec['id']):
            raise ValueError('Invalid README topic ID')
        kind = spec['readme_kind']
        if kind not in docs:
            raise ValueError('README topic source is not registered')
        document = docs[kind]
        overview = excerpt(document, spec['overview'])
        views = {view: [fact(record, spec['id']+'_'+view+'_'+str(i), 'readme_topic',
                             excerpt(docs[selection.get('readme_kind',kind)], selection),
                             selection.get('readme_kind',kind), selection['heading'], True)
                        for i, selection in enumerate(selections)]
                 for view, selections in spec.get('views', {}).items()}
        topic = {**spec, 'overview_text': overview, 'prepared_views': views,
                 'source': source(record, kind, spec['overview']['heading']), 'files':[], 'linkage_files':[]}
        for item in spec.get('file_specs', []):
            content = section(document, item['heading'])
            parsed = tables(content)
            column_rows = next((rows for headers, rows in parsed if 'Column' in headers), [])
            descriptions = [{'Column':clean(row['Column']), 'Meaning':row.get('Meaning',row.get('Description','')),
                             'Type':row.get('Type','')} for row in column_rows]
            listed = re.search(r'```text\s*\n(.*?)```',content,re.S)
            columns = listed[1].strip().splitlines() if listed else [row['Column'] for row in descriptions]
            if listed:
                known = {row['Column']:row for row in descriptions}
                descriptions = [known.get(col,{'Column':col,'Meaning':'','Type':''}) for col in columns]
            location = re.search(r'```text\s*\n((?://|/n/)[^\n]+)',section(document,spec['location_heading']))[1]
            fake = next((f for f in record.get('files',[]) if f['file']==item.get('file')), None)
            if item.get('file') and (fake is None or fake['columns']!=columns):
                raise ValueError('Registered synthetic columns differ from original README')
            topic['files'].append({
                **item, 'name':item['name'], 'id':spec['id']+'_'+item['id'],
                'file_group':spec.get('file_group'),
                'file':item.get('file'), 'location':location.rstrip('/')+'/'+item['source_file'],
                'source_files':[item['source_file'] + (' — '+item['worksheet']+' worksheet' if item.get('worksheet') else '')],
                'columns':columns,'column_descriptions':descriptions,
                'description':excerpt(document,item['description']) if item.get('description') else overview,
                'row_meaning':fake['row_meaning'] if fake else '',
                'readme_kind':kind,'topic_id':spec['id'],'link_target':spec.get('link_target'),
                'synthetic':bool(fake),'preview_available':bool(fake),'dictionaries':[],
                'show_columns':False,'source':source(record,kind,item['heading']),
                'outcome_facts':[fact(record,spec['id']+'_'+item['id']+'_outcome_'+str(i),'readme_topic',
                    excerpt(docs[s.get('readme_kind',kind)],s),s.get('readme_kind',kind),s['heading'],True)
                    for i,s in enumerate(item.get('outcome_views',[]))],
            })
        if spec.get('files_section'):
            text = section(document, spec['files_section'])
            for index, match in enumerate(re.finditer(r'^([^\n`]+?):\s*`((?://|/n/)[^`]+)`', text, re.M)):
                name, path = clean(match[1]), match[2]
                name = re.sub(r'^The ', '', name)
                name = name[0].upper() + name[1:]
                descriptions=spec.get('file_descriptions')
                description=excerpt(document,descriptions[index]) if descriptions else overview
                topic['files'].append({
                    'id':spec['id']+'_'+str(index), 'name':spec['name']+' — '+name,
                    'file_group':spec.get('file_group'),
                    'file':None, 'location':path, 'source_files':[path.rsplit('/',1)[-1]],
                    'columns':[], 'column_descriptions':[], 'row_meaning':'',
                    'description':description, 'readme_kind':kind, 'topic_id':spec['id'],
                    'link_target':spec.get('link_target'),
                    'synthetic':False, 'preview_available':False, 'dictionaries':[],
                    'show_columns':False, 'source':topic['source'],
                })
            if spec.get('file_descriptions') and len(spec['file_descriptions'])!=len(topic['files']):
                raise ValueError('README file descriptions and file paths differ')
        for selection in spec.get('linkage_files', []):
            linkage_kind = selection.get('readme_kind',kind)
            row = next((row for headers, rows in tables(docs[linkage_kind]) for row in rows
                        if clean(row.get(selection['key_column'], '')) == selection['row']), None)
            if row is None:
                raise ValueError('Missing registered README file-table row')
            path_match = re.search(r'`((?://|/n/)[^`]+)`',row[selection['path_column']])
            if not path_match:
                raise ValueError('Missing documented file path')
            path = path_match[1]
            topic['linkage_files'].append({
                'name':selection['row'], 'file':None, 'location':path,
                'columns':re.findall(r'`([^`]+)`',row.get(selection.get('columns_column'),'')),
                'show_columns':True, 'readme_kind':linkage_kind, 'preview_available':False,
                'dictionaries':[], 'source':source(record,linkage_kind,selection['heading']),
            })
        prepared.append(topic)
        record['documented_files'].extend(topic['files'])
        record['resources'].extend({
            'name':f['name'], 'kind':spec.get('resource_type','Project data'),
            'location':f['location'], 'description':f['description'], 'source_kind':kind,
            'file_group':f['file_group'],
        } for f in topic['files'])
    record['readme_topics'] = prepared


def topic_facts(record):
    result=[]
    for topic in record.get('readme_topics',[]):
        result.append(fact(record, topic['id']+'_overview', 'readme_topic',
                           topic['name']+': '+topic['overview_text'], topic['readme_kind'],
                           topic['overview']['heading'], True))
        for facts in topic['prepared_views'].values():
            result.extend(facts)
    return result


def requested_view(query):
    q=query.lower()
    if re.search(r'link|connect|merge|align|join|match|\bmap\b|mapping',q): return 'linkage'
    if re.search(r'fake|synthetic|sample rows|preview|first \d+ rows',q): return 'preview'
    if re.search(r'where|location|\bpaths?\b|file names?|filenames?',q): return 'location'
    if re.search(r'columns?|schema|fields?|look like|looks like',q): return 'columns'
    if re.search(r'versions?|338|337',q): return 'versions'
    if re.search(r'how many|sample size|cohort size|patient count',q): return 'statistics'
    if re.search(r'outcomes?|labels?|defined?|definition|partial response|statuses|wk\d+_remis',q) and not re.search(r'\b(?:do|have|available)\b',q): return 'outcomes'
    return 'overview'


def match_topic(catalog, query, previous):
    q=' '+' '.join(words(query))+' '
    view=requested_view(query)
    matches=[]
    for dataset_id, record in catalog.records.items():
        for topic in record.get('readme_topics',[]):
            topic_view=next((name for name,aliases in topic.get('view_keywords',{}).items()
                             if any(' '+' '.join(words(alias))+' ' in q for alias in aliases)),view)
            aliases=[topic['name'],*topic['aliases'],
                     *(alias for f in topic['files'] for alias in file_aliases(f))]
            matching_aliases = {' '.join(words(alias)) for alias in aliases
                                if ' ' + ' '.join(words(alias)) + ' ' in q}
            if topic['id'] == 'ibd_registry' and previous != [dataset_id] and not re.search(
                r'\b(?:ibd|inflammatory bowel disease)\b', q
            ):
                matching_aliases.discard('registry')
            strength = max((len(alias.split()) for alias in matching_aliases), default=0)
            named=bool(strength)
            context_link=(view=='linkage' and previous==[dataset_id]
                          and len([t for t in record.get('readme_topics',[]) if t.get('link_target')=='EHR'])==1
                          and topic.get('link_target')=='EHR' and ' ehr ' in q)
            if not (named or context_link): continue
            # Reject unsupported tasks, extra sites or subgroups. Let the main
            # interpreter handle these instead of silently ignoring qualifiers.
            known=set(words(' '.join([record['label'],record['dataset_name'],topic['name'],
                *topic['aliases'],topic['overview_text'],
                *aliases,
                *(alias for aliases in topic.get('view_keywords',{}).values() for alias in aliases),
                *(f['name']+' '+' '.join(f.get('aliases',[]))+' '+' '.join(f['columns'])+' '+f['description'] for f in topic['files']),
                *(f['text'] for facts in topic['prepared_views'].values() for f in facts)])))
            operations=set('a an the i we you our this these those them their it its is are do does did have has '
                           'what which where how can could would should want wanted please tell show see find '
                           'get me about with to of for from in on and or also available availability data dataset '
                           'datasets resource resources records information details detail more further overview describe description help explain through use using '
                           'look looks like structure files file path paths location original readme documented '
                           'connect connected connection link linked linkage merge merged merging join alignment '
                           'identifiers identifier existing ehr registry labels label outcomes outcome fields field '
                           'columns column schema counts count patients patient many size sample fake synthetic '
                           'rows preview first five 5 10 14 52 week weeks wk wks numbers number cohorts cohort '
                           'baseline treatment matching match map mapping normalized broader stricter sensitivity '
                           'current recommended definition definitions defined version versions table tables score scores workbook worksheets worksheet '
                           'both all at 3 12 30 endoscopy legacy prism mgh genetic polygenic risk grs prs '
                           'stats statistics summary examples workflow who managed manages manager contact related'.split())
            if re.search(r'\b(?:run|compute|calculate|fit|train|execute|perform)\b',query,re.I): continue
            if set(words(query))-known-operations: continue
            matches.append((strength,(record,topic,topic_view)))
    if not matches: return None
    best=max(strength for strength,_ in matches)
    winners=[match for strength,match in matches if strength==best]
    return winners[0] if len(winners)==1 else None


def topic_answer(catalog, query, previous):
    started=time.monotonic()
    matched=match_topic(catalog,query,previous or [])
    if not matched: return None
    record,topic,view=matched
    spec=topic['overview']
    overview=fact(record,topic['id']+'_answer_overview','readme_topic',topic['overview_text'],
                  topic['readme_kind'],spec['heading'],True)
    facts=topic['prepared_views'].get(view,[overview]) if view!='location' else []
    focused_files=named_files(topic['files'],query)
    if view=='overview' and len(focused_files)==1:
        file=focused_files[0]
        # A named file gets its own source description, not the parent inventory.
        facts=[{**overview,'id':overview['id']+'_'+file['id'],
                'text':file['description'],'source':file['source']}]
    if view=='outcomes':
        targets=focused_files
        if len(targets)==1 and targets[0].get('outcome_facts'):
            facts=targets[0]['outcome_facts']
    file_views = {'overview','location','columns','preview'}
    if topic['id']=='ibd_agents':
        file_views.add('statistics')
    files=topic['linkage_files'] if view=='linkage' else topic['files'] if view in file_views else []
    selected=named_files(files,query)
    if selected: files=selected
    files=[{**f,'show_columns':view in {'columns','preview'},'show_preview':view=='preview' and bool(f.get('file'))} for f in files]
    if view in {'columns','preview'} and files: facts=[]
    intro={'linkage':'Here is how the README describes linking these data.',
           'location':'Here are the documented source files.',
           'columns':'Here are the fields described in the README.',
           'statistics':'Here are the documented cohorts.',
           'outcomes':'Here are the outcomes described in the README.'}.get(view,topic['name'])
    intro=topic.get('view_intros',{}).get(view,intro)
    focus=focused_files[0] if len(focused_files)==1 else None
    if view=='overview' and focus: intro=focus['name']
    if view=='preview':
        intro=('These are generated fake rows showing the file structure.' if any(f.get('file') for f in files)
               else 'The score workbook has column descriptions. Fake sample rows have not been prepared.')
    sources=[f['source'] for f in facts]+[f['source'] for f in files]
    actions=[]
    target_name=focus['name'] if focus else topic['name']
    if focus and view not in {'columns','preview'}:
        actions.append({'label':'Show columns','query':f'Show columns for {target_name}'})
    if focus and focus.get('preview_available') and view!='preview':
        actions.append({'label':'Show 5 fake rows','query':f'Show 5 fake rows for {target_name}'})
    if view!='linkage' and 'linkage' in topic['prepared_views'] and topic.get('link_target'):
        target=' with '+topic['link_target'] if topic.get('link_target') else ''
        actions.append({'label':'How to link'+target,'query':f"How do I link {target_name}{target}?"})
    if view!='location':
        actions.append({'label':'Show file locations',
                        'query':f"Where are the {target_name} files?"})
    if topic['id']=='ibd_agents':
        if view=='statistics':
            intro='Here are the documented counts for the endoscopy output.'
        related = (['MGH treatment-response registry','Legacy PRISM treatment-response registry']
                   if view=='treatment_agent' else ['PRISM endoscopy scores'])
        if view=='treatment_agent':
            intro='Chart review agent for treatment response'
            actions=[]
        actions.extend({'label':name,'query':f'Tell me about {name}'} for name in related)
        if view!='treatment_agent':
            actions.append({'label':'Treatment-response chart review agent','query':'Tell me about the chart review agent for treatment response'})
    return {'query':query,'engine':'catalog','model':None,'intent':'readme_topic',
            'interpretation':'verified_readme_topic','intro':intro,
            'answer':'\n\n'.join([intro,*[f['text'] for f in facts],
                *[f['name']+(': '+', '.join(f['columns']) if f.get('show_columns') else '') for f in files]]),
            'datasets':[{'dataset':catalog.summary(record),'facts':facts,'files':files,
                         'dictionaries':[],'offer_preview':False,'additional_note':None,'date_summary':None}],
            'sources':list({(s['kind'],s.get('heading')):s for s in sources}.values()),
            'context_dataset_ids':[record['dataset_id']],'pending_topic':None,
            'warning':None,'compact':False,'actions':actions,'elapsed_seconds':round(time.monotonic()-started,2)}
