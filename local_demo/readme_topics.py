"""Register data described inside project READMEs as searchable source excerpts.

Registrations name headings and file-table rows, not inferred facts or new schemas.
The same adapter can describe a registry, linked cohort, labels or another input.
"""
import re
import time

from .readme_resources import section, source, fact, tables, clean


def words(text):
    return re.findall(r'[a-z0-9_]+', text.lower())


def excerpt(document, spec):
    text = section(document, spec['heading'])
    if spec.get('paragraph_prefix'):
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
                             excerpt(document, selection), kind, selection['heading'], True)
                        for i, selection in enumerate(selections)]
                 for view, selections in spec.get('views', {}).items()}
        topic = {**spec, 'overview_text': overview, 'prepared_views': views,
                 'source': source(record, kind, spec['overview']['heading']), 'files':[], 'linkage_files':[]}
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
            row = next((row for headers, rows in tables(document) for row in rows
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
                'show_columns':True, 'readme_kind':kind, 'preview_available':False,
                'dictionaries':[], 'source':source(record,kind,selection['heading']),
            })
        prepared.append(topic)
        record['documented_files'].extend(topic['files'])
        record['resources'].extend({
            'name':f['name'], 'kind':spec.get('resource_type','Project data'),
            'location':f['location'], 'description':overview, 'source_kind':kind,
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
    if re.search(r'where|location|\bpaths?\b|file names?|filenames?',q): return 'location'
    if re.search(r'columns?|schema|fields?',q): return 'columns'
    if re.search(r'how many|sample size|cohort size|patient count',q): return 'statistics'
    if re.search(r'outcomes?|labels?|defined?|definition|partial response',q) and not re.search(r'\b(?:do|have|available)\b',q): return 'outcomes'
    return 'overview'


def match_topic(catalog, query, previous):
    q=' '+' '.join(words(query))+' '
    view=requested_view(query)
    matches=[]
    for dataset_id, record in catalog.records.items():
        for topic in record.get('readme_topics',[]):
            named=any(' '+' '.join(words(alias))+' ' in q for alias in [topic['name'],*topic['aliases']])
            context_link=(view=='linkage' and previous==[dataset_id]
                          and len(record.get('readme_topics',[]))==1 and ' ehr ' in q)
            if not (named or context_link): continue
            # Reject unsupported tasks, extra sites or subgroups. Let the main
            # interpreter handle these instead of silently ignoring qualifiers.
            known=set(words(' '.join([record['label'],record['dataset_name'],topic['name'],
                *topic['aliases'],topic['overview_text'],
                *(f['text'] for facts in topic['prepared_views'].values() for f in facts)])))
            operations=set('a an the i we you our this these those them their it its is are do does did have has '
                           'what which where how can could would should want wanted please tell show see find '
                           'get me about with to of for from in on and or also available availability data dataset '
                           'datasets resource resources records information details help explain through use using '
                           'look looks like structure files file path paths location original readme documented '
                           'connect connected connection link linked linkage merge merged merging join alignment '
                           'identifiers identifier existing ehr registry labels label outcomes outcome fields field '
                           'columns column schema counts count patients patient many size sample fake synthetic '
                           'rows preview first five 5 10 14 52 week weeks wk wks numbers number cohorts cohort '
                           'baseline treatment matching match map mapping normalized broader stricter sensitivity '
                           'current recommended definition definitions'.split())
            if re.search(r'\b(?:run|compute|calculate|fit|train|execute|perform)\b',query,re.I): continue
            if set(words(query))-known-operations: continue
            matches.append((record,topic,view))
    return matches[0] if len(matches)==1 else None


def topic_answer(catalog, query, previous):
    started=time.monotonic()
    matched=match_topic(catalog,query,previous or [])
    if not matched: return None
    record,topic,view=matched
    spec=topic['overview']
    overview=fact(record,topic['id']+'_answer_overview','readme_topic',topic['overview_text'],
                  topic['readme_kind'],spec['heading'],True)
    facts=topic['prepared_views'].get(view,[overview]) if view!='location' else []
    files=topic['linkage_files'] if view=='linkage' else topic['files'] if view in {'overview','location'} else []
    intro={'linkage':'Here is how the README describes linking these data.',
           'location':'Here are the documented source files.',
           'columns':'Here are the fields described in the README.',
           'statistics':'Here are the documented cohorts.',
           'outcomes':'Here are the outcomes described in the README.'}.get(view,topic['name'])
    if re.search(r'fake|synthetic|sample rows|preview',query,re.I):
        intro='Here is the documentation. Fake sample rows are not available for these files.'
    sources=[f['source'] for f in facts]+[f['source'] for f in files]
    actions=[]
    if view!='linkage' and 'linkage' in topic['prepared_views']:
        target=' with '+topic['link_target'] if topic.get('link_target') else ''
        actions.append({'label':'How to link'+target,'query':f"How do I link {topic['name']}{target}?"})
    if view!='location':
        actions.append({'label':'Show file locations',
                        'query':f"Where are the {topic['name']} files?"})
    return {'query':query,'engine':'catalog','model':None,'intent':'readme_topic',
            'interpretation':'verified_readme_topic','intro':intro,
            'answer':'\n\n'.join([intro,*[f['text'] for f in facts],*[f['name'] for f in files]]),
            'datasets':[{'dataset':catalog.summary(record),'facts':facts,'files':files,
                         'dictionaries':[],'offer_preview':False,'additional_note':None,'date_summary':None}],
            'sources':list({(s['kind'],s.get('heading')):s for s in sources}.values()),
            'context_dataset_ids':[record['dataset_id']],'pending_topic':None,
            'warning':None,'compact':False,'actions':actions,'elapsed_seconds':round(time.monotonic()-started,2)}
