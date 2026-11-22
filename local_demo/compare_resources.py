"""Document-backed comparisons with explicit subjects and a shared field table."""
import re

from .resource_guides import norm
from .single_files import file_inventory
from .presentation import file_views
from .comparison import comparison_summary
from .ms import SITE_QUERY, ms_ids


COMPARE=r'\b(?:compar\w*|contrast\w*|differences?|different|differ|similarities|similar|versus|vs|interchange\w*)\b|same columns|side[ -]by[ -]side'


def entities(catalog):
    result={}
    for key,r in catalog.records.items():
        aliases=[r['label'],r['dataset_name']]
        if key=='IBD': aliases+=['IBD','inflammatory bowel disease','MGB IBD']
        if key.endswith('_AD'):
            aliases += [r['site']+' AD',r['site']+' Alzheimer data',r['site']+' Alzheimer disease',r['site']+' Alzheimer s disease']
        if key.endswith('_MS'):
            aliases += [r['site']+' multiple sclerosis', 'MS at '+r['site'], 'multiple sclerosis at '+r['site']]
        result[key]={'id':key,'name':r['label'],'kind':'dataset','aliases':aliases,'record':r}
    for key,e in catalog.library.entries.items():
        result[key]={'id':key,'name':e['label'],'kind':'resource','aliases':[e['label'],*e['aliases']],'entry':e}
    for f in file_inventory(catalog):
        result[f['id']]={'id':f['id'],'name':f['label']+' — '+f['name'],'kind':'file',
                         'aliases':list(dict.fromkeys([*f['aliases'],*f.get('card',{}).get('aliases',[])])),'item':f}
    return result


def mentions(text,index,kinds):
    q=' '+norm(text)+' '
    matches=[]
    for e in index.values():
        if e['kind'] not in kinds: continue
        spans=[(m.start(),m.end()) for alias in e['aliases'] for m in re.finditer(' '+re.escape(norm(alias))+' ',q)]
        if spans: matches.append((e,spans))
    return [(e,spans) for e,spans in matches if not all(any(
        a<=start and b>=end and b-a>end-start for other,others in matches for a,b in others)
        for start,end in spans)]


def parent_mentions(query,index):
    found=mentions(query,index,{'dataset','resource'})
    ids=list(dict.fromkeys(e['id'] for e,_ in found))
    q=norm(query)
    full_ad=[i for i in ids if i.endswith('_AD')]
    # Shared disease/site wording is expanded only when it does not name a different disease on one side.
    if re.search(r'\bad\b|alzheimer|dementia',q) and not full_ad:
        sites=[site for site in ['MGB','UPMC'] if re.search(r'\b'+site.lower()+r'\b',q)]
        ids += [site+'_AD' for site in sites or ['MGB','UPMC']]
    inferred_ms = ms_ids(q, index)
    if inferred_ms and (not ids or (len(inferred_ms) == 2 and all(key.endswith('_MS') for key in ids))):
        ids.extend(inferred_ms)
    return list(dict.fromkeys(ids))


def clauses(query,index):
    q=norm(query)
    protected=[(a-1,b-1) for e,spans in mentions(query,index,{'dataset','resource','file'}) for a,b in spans]
    cuts=[m for m in re.finditer(r'\b(?:and|versus|vs|with)\b',q)
          if not any(a<m.start() and b>m.end() for a,b in protected)]
    pieces=[]; start=0
    for cut in cuts:
        pieces.append(q[start:cut.start()].strip()); start=cut.end()
    pieces.append(q[start:].strip())
    return pieces


def clarification(query,message,options=None):
    return {'query':query,'engine':'catalog','model':None,'intent':'comparison_clarification',
        'interpretation':'comparison_clarification','intro':message,'answer':message,'datasets':[],
        'resources':[],'sources':[],'context_dataset_ids':[],'selection':None,'pending_topic':None,
        'warning':None,'compact':True,'actions':options or [{'label':'Browse resources','view':'browse'}],
        'comparison':None,'elapsed_seconds':0}


def dimension(query):
    q=query.lower()
    if re.search(r'patient count|cohort size|how many patients|sample size',q): return 'counts'
    if re.search(r'\bdates\b|date range|date coverage|time (?:range|coverage|distribution)|earliest|latest',q): return 'dates'
    if re.search(r'access|licen[cs]|permission',q): return 'access'
    if re.search(r'script|\bcode\b|repositor',q): return 'code'
    if re.search(r'where|storage|locations?|\bpaths?\b|on o2',q): return 'location'
    if re.search(r'columns?|schemas?|fields?|look like|structure|monthly.*counts?|counts?.*monthly|\b(?:raw|daily)\b',q): return 'columns'
    return 'overview'


def resolve(query,index,catalog,selection,previous):
    requested_files=re.findall(r'[\w.-]+\.(?:csv|rdata|rds|tsv|rrf|jsonl|parquet|pq|xlsx|dsv)\b',query,re.I)
    unknown=[name for name in requested_files if not any(norm(name) in norm(alias) for e in index.values() for alias in e['aliases'])]
    if unknown:
        return None,clarification(query,'I could not find documentation for '+', '.join(unknown)+'. Please choose a documented file or provide its README.')
    global_parents=parent_mentions(query,index)
    ms_pair = len(global_parents) == 2 and all(key.endswith('_MS') for key in global_parents)
    if ms_pair and len({name.lower() for name in requested_files}) == 1:
        filename = requested_files[0].lower()
        matches = [e for e in index.values() if e['kind'] == 'file' and e['item']['parent'] in global_parents
                   and filename in {name.lower() for name in e['item']['card'].get('source_files', [])}]
        if len(matches) == 2 and {e['item']['parent'] for e in matches} == set(global_parents):
            return matches, None
    selected=[]; unresolved=[]
    parts=clauses(query,index)
    for part in parts:
        local_parents=parent_mentions(part,index)
        if ms_pair:
            site_keys = [key for key in global_parents if re.search(SITE_QUERY[key.split('_')[0]], part)]
            if site_keys:
                local_parents = site_keys
        if not local_parents and re.search(r'\bad\b|alzheimer|dementia',norm(query)):
            wrappers=set('compare comparing comparison difference differences between for the data dataset datasets '
                         'monthly daily raw codified nlp counts count columns fields schema storage access dates '
                         'how are do they differ different similar what is same from in at and versus vs mgb upmc'.split())
            if not set(part.split())-wrappers:
                local_parents=[site+'_AD' for site in ['MGB','UPMC'] if re.search(r'\b'+site.lower()+r'\b',part)]
        parents=local_parents or global_parents
        files=[e for e,_ in mentions(part,index,{'file'}) if not parents or e['item']['parent'] in parents]
        if files:
            # An unqualified duplicated basename needs a site/version choice.
            groups={}
            for e in files:
                aliases=[norm(a) for a in e['aliases'] if ' '+norm(a)+' ' in ' '+part+' ']
                key=max(aliases,key=len)
                groups.setdefault(key,[]).append(e)
            for name,group in groups.items():
                if len(group)>1 and (not parents or len({e['item']['parent'] for e in group})<len(group)):
                    return None,clarification(query,'That file name has more than one documented site or version. Include the site or full path in the comparison.')
            selected += files
        elif local_parents:
            selected += [index[key] for key in local_parents]
        elif len(parts)>1 and re.search(r'\b(?:this|it|that|these|them)\b',part) and selection:
            key=selection.get('id')
            if key in index: selected.append(index[key])
        elif len(parts)>1:
            # A shared qualifier, e.g. "NLP counts for IBD", is not a second resource.
            generic=set('compare comparing comparison difference differences between for the data dataset datasets files file '
                        'monthly daily raw codified nlp counts count columns column fields schema storage access dates '
                        'locations structure and how are do they differ different similar what is same please'.split())
            if set(part.split())-generic: unresolved.append(part)
    if not selected: selected=[index[key] for key in global_parents]
    clinical_parents=[key for key in global_parents if index[key]['kind']=='dataset']
    levels=[s for s in ['raw','daily','monthly'] if re.search(r'\b'+s+r'\b',query,re.I)]
    kinds=[s for s in ['codified','nlp'] if re.search(r'\b'+s+r'\b',query,re.I)]
    explicit_filename=bool(re.search(r'\.(?:csv|rdata|rds|tsv|rrf|jsonl|parquet|pq|xlsx)\b',query,re.I))
    if len(clinical_parents)>=2 and len(clinical_parents)==len(global_parents) and dimension(query)=='columns' and len(levels)<=1 and len(kinds)<=1 and not explicit_filename and not unresolved:
        return [index[key] for key in clinical_parents],None
    if len(global_parents)==1 and index[global_parents[0]]['kind']=='dataset' and (len(levels)>1 or len(kinds)>1 or all(e['kind']=='dataset' for e in selected)) and re.search(r'\bmonthly\b|\bdaily\b|\braw\b|\bcodified\b|\bnlp\b',query,re.I):
        r=index[global_parents[0]]['record']
        levels=[s for s in ['raw','daily','monthly'] if re.search(r'\b'+s+r'\b',query,re.I)] or ['monthly']
        cards=[card for level in levels for card in file_views(r,level+' '+(' '.join(k for k in ['codified','nlp'] if re.search(r'\b'+k+r'\b',query,re.I))),'columns')]
        selected=[e for e in index.values() if e['kind']=='file' and e['item']['parent']==r['dataset_id'] and any(
            (card.get('file') and card['file']==e['item'].get('card',{}).get('file')) or
            (card.get('id') and card['id']==e['item'].get('card',{}).get('id')) for card in cards)]
    unique={e['id']:e for e in selected}
    # File selection replaces its parent when both were identified in the same clause.
    file_parents={e['item']['parent'] for e in unique.values() if e['kind']=='file'}
    for parent in file_parents: unique.pop(parent,None)
    if unresolved or len(unique)<2:
        if not unique and selection and selection.get('kind')=='comparison':
            keys=selection.get('ids',[])
            if all(key in index for key in keys): return [index[key] for key in keys],None
        if not unique and len(previous or [])>=2 and all(k in index for k in previous):
            return [index[k] for k in previous],None
        names=', '.join(e['name'] for e in unique.values())
        return None,clarification(query,('I matched '+names+', but could not identify the other comparison target from the documentation. ' if names else '')+
                                  'Please name two files or resources, including the site when needed.')
    if len(unique)>4: return None,clarification(query,'Please narrow this comparison to two to four files or resources.')
    return list(unique.values()),None


def short_columns(columns):
    shown=columns[:12]
    text=', '.join('`'+c+'`' for c in shown)
    return text+(f' … ({len(columns)} documented columns)' if len(columns)>12 else '') if columns else 'Not documented.'


def data_for(entity,catalog,query):
    kind=entity['kind']; data={'name':entity['name'],'schemas':[],'sources':[],'locations':[],'columns':[]}
    if kind=='dataset':
        r=entity['record']
        data.update(type='Clinical dataset',contents=r['description'],storage=', '.join(r['storage_platform'])+
                    ('. No O2 copy.' if r.get('has_o2_copy') is False else ''),contact=r['contact'])
        data['schemas']=file_views(r,query,'columns')
        data['counts']=('Codified: '+format(r['source_counts_from_readme']['codified_unique_patients'],',')+
            '; NLP: '+format(r['source_counts_from_readme']['nlp_unique_patients'],',')+' unique patients; groups overlap.') if r.get('source_counts_from_readme') else 'Not documented for these files.'
        data['dates']='Not documented for these files.'
        if r.get('date_summaries'):
            data['dates']='\n'.join(s['name']+': '+ '; '.join(k+': '+str(v) for k,v in s['dates'].items()) for s in r['date_summaries'])
        data['access']='See the README and contact '+r['contact']+'.'
        data['code']='\n'.join(res['name'] for res in r['resources'] if 'script' in res['kind'].lower() or 'code' in res['kind'].lower()) or 'Not documented.'
        data['sources']=[{'kind':'original','label':r['label']+' — original README','url':f"/api/datasets/{r['dataset_id']}/readme/original",'dataset_id':r['dataset_id']}]
        data['preview']=str(len(r['files']))+' prepared synthetic files.'
        data['files']='\n'.join(f['name'] for f in data['schemas'])
        if r.get('documentation_only'):
            mgb = r['site'] == 'MGB'
            stats = r['report_stats']
            data.update(counts=f"{stats['counts']} Report generated {stats['generated']}.",
                        dates=('Calendar coverage charts in the cohort report.' if mgb else
                               'Raw source inventory: codified EHR January 2004–December 2022, NLP 2011–2021. See the cohort report for filtered coverage.'),
                        access='Preprocessed files are stored on O2.', code='Preprocessing README and shared code-mapping README.',
                        disability='EDSS (primary), plus PDDS' if mgb else 'PDDS (primary) from PROMOTE, with limited EDSS coverage',
                        nlp_time='Mention days in 30.4375-day windows mapped onto calendar months using corrected t0.' if mgb else
                                 'Distinct days with asserted concepts within actual calendar months.',
                        labs='Lab codes and counts.' if mgb else 'Lab values, units and reference ranges in the raw layer. Processed files have counts.')
            data['locations'] = [r['storage_location']]
            data['sources'] = [{'dataset_id': r['dataset_id'], **doc} for doc in r['original_documents']
                               if doc['kind'] in {'ms_comparison', 'ms_report', 'ms_preprocessing', 'ms_mapping', 'ms_raw'}]
    elif kind=='resource':
        e=entity['entry']
        data.update(type=e['resource_type'],contents=e['description'],storage=e['storage'],contact=e['contact'])
        data['sources']=[catalog.library.source(e)]
        for key,view in [('access','access'),('code','code')]:
            blocks=catalog.library.view(e,view,query)['blocks']
            data[key]='\n'.join(b.get('text') or '\n'.join(b.get('items',[])) for b in blocks) or 'Not documented.'
        identity=e.get('sections',{}).get('Files and dataset identity','')
        data['counts']='\n'.join(line.removeprefix('- ') for line in identity.splitlines() if re.search(r'patient count|cohort count|patients',line,re.I)) or (
            str(e['west']['patient_count'])+' patients.' if 'west' in e else 'Not documented as a patient count.')
        data['dates']='Not documented as data coverage.'
        data['columns']=[c['Column'] for c in e.get('west',{}).get('columns',[])]
        data['preview']='No prepared synthetic preview.'
        data['files']='\n'.join(f['name'] for f in file_inventory(catalog) if f['parent']==e['id']) or 'Access guide; no individual data files listed.'
        shape=next((line.removeprefix('- ') for line in identity.splitlines() if line.startswith('- Shape:')),None)
        if shape: data['files']+='\n'+shape
        if 'guide' in e:
            sections = e['guide']['sections']
            for field in ('files','counts','dates'):
                data[field]='\n'.join(line for s in sections if field in s['views'] for line in s['items'])
            data['columns']=e['guide']['columns']
            data['locations']=[location['value'] for location in e['locations']]
    else:
        item=entity['item']; card=item.get('card',{})
        data.update(type='File or folder',contents=item['description'],sources=[item['source']],columns=card.get('columns',[]) or
                    [c['Column'] for c in item.get('column_descriptions',[])])
        parent=catalog.records[item['parent']] if item['clinical'] else catalog.library.entries[item['parent']]
        if not item['clinical']: data['type']=parent['resource_type']
        data['storage']=', '.join(parent['storage_platform']) if item['clinical'] else parent['storage']
        data['locations']=[card.get('location') or item.get('location')]
        data['counts']='Not documented for this file.'
        data['dates']='Not documented for this file.'
        data['access']='See the original README for this file.'
        data['code']='See the original README for this file.'
        data['preview']='Prepared synthetic rows.' if card.get('file') else 'No prepared synthetic preview.'
        data['files']=item.get('card',{}).get('source_file') or item['name']
    return data


def comparison_answer(catalog,query,selection=None,previous=None):
    index=entities(catalog)
    active=selection if isinstance(selection,dict) and selection.get('kind')=='comparison' and 2<=len(selection.get('ids',[]))<=4 and all(k in index for k in selection['ids']) else None
    q=norm(query)
    follow=active and re.fullmatch(r'(?:tell me more|what about (?:the )?(?:columns|storage|access|dates|patient counts|code)|show (?:the )?columns|where are they|how are they different|can i (?:combine|merge) (?:them|these))',q)
    if not re.search(COMPARE,query,re.I) and not follow: return None
    # Study-aim comparisons have their own source-specific documentation view.
    if re.search(r'\baims?\s*[1-5]',query,re.I): return None
    if re.search(r'\b(?:subgroups?|patients? with|people with|diagnosed with)\b',query,re.I):
        keys=active['ids'] if active else parent_mentions(query,index)
        if len(keys)>=2:
            result=clarification(query,'This comparison has no documented subgroup counts for that request. You can compare the documented overall counts or file structures.',
                [{'label':'Compare overall counts','query':'What about patient counts?'},
                 {'label':'Compare columns','query':'What about the columns?'}])
            result['selection']={'kind':'comparison','ids':keys}
            return result
    if follow:
        chosen=[index[k] for k in active['ids']]; error=None
    else: chosen,error=resolve(query,index,catalog,selection,previous)
    if error: return error
    if re.search(r'\b(?:subgroups?|patients? with|people with|diagnosed with)\b',query,re.I):
        result=clarification(query,'This comparison has no documented subgroup counts for that request. You can compare the documented overall counts or file structures.',
            [{'label':'Compare overall counts','query':'What about patient counts?'},
             {'label':'Compare columns','query':'What about the columns?'}])
        result['selection']={'kind':'comparison','ids':[e['id'] for e in chosen]}
        return result
    criteria=' '+norm(query)+' '
    for e in chosen:
        for alias in sorted(e['aliases'],key=len,reverse=True):
            criteria=criteria.replace(' '+norm(alias)+' ',' ')
    requested=dimension(criteria)
    levels=[s for s in ['raw','daily','monthly'] if re.search(r'\b'+s+r'\b',query,re.I)]
    kinds=[s for s in ['codified','nlp'] if re.search(r'\b'+s+r'\b',query,re.I)]
    if follow:
        levels=active.get('levels',[]); kinds=active.get('data_kinds',[])
    scope_query=query+' '+' '.join(levels+kinds) if follow else query
    data=[data_for(e,catalog,scope_query) for e in chosen]
    fields=[('Resource type','type'),('Contents','contents'),('Storage','storage'),('Documented files','files')]
    two_ms_sites = len(chosen) == 2 and all(e['kind'] == 'dataset' and e['record'].get('documentation_only') for e in chosen)
    if two_ms_sites and requested == 'overview':
        fields = [('Storage', 'storage'), ('Primary disability label', 'disability'), ('NLP time resolution', 'nlp_time'),
                  ('Lab data', 'labs'), ('Cohort report counts', 'counts'), ('Documented files', 'files')]
    if requested=='location': fields=[('Storage','storage')]
    if requested == 'location' and two_ms_sites:
        for d in data:
            d['storage'] = d['locations'][0]
    if requested=='overview' and all(e['kind']=='file' for e in chosen) and any(d['columns'] for d in data):
        fields.append(('Column names','columns'))
    if requested=='columns': fields=[('Resource type','type'),('Storage','storage'),('Column names','columns')]
    if requested=='columns' and all(e['kind']=='dataset' for e in chosen) and all(
        d['schemas'] and all('monthly' in f['name'].lower() and {'month','year'}<=set(f['columns']) for f in d['schemas']) for d in data):
        fields=[('Resource type','type'),('Storage','storage')]
        for group in ['codified','nlp']:
            if not any(any(('nlp' in f['name'].lower())==(group=='nlp') for f in d['schemas']) for d in data): continue
            key='schema_'+group
            fields.append(('Monthly '+('NLP' if group=='nlp' else group)+' columns',key))
            for d in data:
                d[key]='\n'.join(short_columns(f['columns']) for f in d['schemas'] if ('nlp' in f['name'].lower())==(group=='nlp')) or 'Not documented.'
    if requested in {'counts','dates','access','code'}: fields=[('Resource type','type'),('Storage','storage'),
        ({'counts':'Documented patient / cohort count','dates':'Documented date coverage','access':'Access requirements','code':'Related code'}[requested],requested)]
    sections=[]; resources=[]
    for e,d in zip(chosen,data):
        if e['kind']=='dataset':
            sections.append({'dataset':catalog.summary(e['record']),'facts':[],'files':d['schemas'],'dictionaries':[],
                             'offer_preview':False,'additional_note':None,'date_summary':None})
        elif e['kind']=='file' and e['item']['clinical']:
            card={**e['item']['card'],'show_columns':requested=='columns','show_preview':False}
            sections.append({'dataset':catalog.summary(catalog.records[e['item']['parent']]),'facts':[],'files':[card],
                             'dictionaries':[],'offer_preview':False,'additional_note':None,'date_summary':None})
        else:
            entry=e.get('entry') or catalog.library.entries[e['item']['parent']]
            resources.append({**catalog.library.summary(entry),'blocks':[],'sources':d['sources'],'source':d['sources'][0],
                'locations':entry['locations'] if e['kind']=='resource' else [{'label':'Documented file location','value':p,'kind':'data'} for p in d['locations'] if p],
                **({'selected_file_name':e['item']['name'],'selected_file_id':e['id']} if e['kind']=='file' else {})})
    schema=comparison_summary('Compare '+scope_query,sections,catalog.records) if requested=='columns' else None
    intro=schema['summary'] if schema else 'Here is a comparison of the documented '+('column names and formats.' if requested=='columns' else
        {'counts':'counts.','dates':'date coverage.','access':'access requirements.','code':'code references.','location':'storage locations.'}.get(requested,'contents and storage.'))
    if two_ms_sites and requested == 'overview':
        intro = 'Both MS sites provide calendar-labeled EHR, NLP and registry outputs. Their primary disability measures and NLP time windows differ.'
    if (requested=='columns' or requested=='overview' and all(e['kind']=='file' for e in chosen)) and not schema:
        columns=[d['columns'] for d in data]
        if all(columns):
            shared=set(columns[0]).intersection(*[set(c) for c in columns[1:]])
            intro=f'These files share {len(shared)} exact column names. '+('Their column names match.' if all(c==columns[0] for c in columns) else 'Their column lists differ.')
        elif not any(columns) and not any(d['schemas'] for d in data) and requested=='columns': intro='Column descriptions are not documented for these resources; their documented contents and formats are shown below.'
    if re.search(r'best|better|interchange|merge|combin|performance|accuracy|effective|efficacy',query,re.I):
        intro+=' Documentation alone does not establish performance or that the data can be combined without further checks.'
    names=[e['name'] for e in chosen]
    rows=[]
    for title,key in fields:
        row={'Field':title}
        for name,d in zip(names,data):
            if key=='columns':
                value=short_columns(d['columns']) if not d['schemas'] else '\n'.join(f['name']+': '+short_columns(f['columns']) for f in d['schemas'])
            else: value=d.get(key,'Not documented.')
            row[name]=value
        rows.append(row)
    sources=list({s['url']:s for d in data for s in d['sources']}.values())
    if schema: sources.extend(schema['sources'])
    parents=list(dict.fromkeys(e['id'] if e['kind']!='file' else e['item']['parent'] for e in chosen))
    table={'columns':['Field',*names],'rows':rows}
    answer='\n\n'.join([intro,*(schema['details'] if schema else []),*[' | '.join(str(row.get(c,'')) for c in table['columns']) for row in rows],
        *[f['name']+': '+', '.join(f['columns']) for s in sections for f in s['files'] if requested=='columns']])
    return {'query':query,'engine':'catalog','model':None,'intent':'comparison','interpretation':'verified_comparison',
        'intro':intro,'answer':answer,'datasets':sections,'resources':resources,'sources':sources,
        'comparison':schema,'comparison_table':table,'context_dataset_ids':parents,'pending_topic':None,
        'selection':{'kind':'comparison','ids':[e['id'] for e in chosen],'view':requested,'levels':levels,'data_kinds':kinds},
        'warning':None,'compact':False,'elapsed_seconds':0,'actions':[
            {'label':'Compare columns','query':'What about the columns?'},
            {'label':'Compare storage','query':'What about storage?'}]}
