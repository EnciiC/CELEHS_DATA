"""Resolve individually documented files, retaining their source and parent resource."""
import hashlib
import re

from .presentation import file_views
from .readme_resources import tables, clean, source
from .resource_guides import norm
from .readme_topics import requested_view
from .ms import ms_ids


def basename(value):
    return value.replace('\\','/').rstrip('/').rsplit('/',1)[-1]


def file_inventory(catalog):
    result=[]
    for parent,record in catalog.records.items():
        cards=file_views(record,'','browse')
        cards += [f for f in record.get('documented_files',[]) if not any(
            (f.get('id') and f['id']==c.get('id')) or (f.get('file') and f['file']==c.get('file')) for c in cards)]
        for resource in record['resources']:
            if not resource.get('location') or any(c.get('location')==resource['location'] for c in cards): continue
            cards.append({'name':resource['name'],'location':resource['location'],
                          'description':resource.get('description',''),'file':None,'columns':[],
                          'dictionaries':[],'readme_kind':resource.get('source_kind')})
        for card in cards:
            resource=next((r for r in record['resources'] if r.get('location')==card.get('location')),{})
            kind=card.get('readme_kind') or 'notes'
            citation=card.get('source') or (source(record,kind) if kind!='notes' else {
                'kind':'notes','label':'Dataset notes','url':f'/api/datasets/{parent}/readme/notes'})
            description=card.get('description') or resource.get('description') or next((
                f['row_meaning'] for f in record['files'] if f['file']==card.get('file')),'')
            aliases=[card['name'],card.get('file',''),basename(card.get('location') or ''),card.get('location','')]
            for name in card.get('source_files',[]): aliases.append(name.split(' — ')[0])
            if re.search('monthly',card['name'],re.I):
                for kind_word in ['codified','NLP']:
                    if re.search(kind_word,card['name'],re.I):
                        aliases.extend(['monthly '+kind_word,kind_word+' monthly'])
            result.append({'parent':parent,'label':record['label'],'clinical':True,'card':card,
                           'name':card['name'],'description':description,'source':citation,'aliases':aliases})
        # Named, undocumented companion files must remain distinguishable from known schemas.
        for doc in record.get('original_readmes',[]):
            if doc['kind']!='ibd_scores': continue
            for headers,rows in tables(catalog.documents[parent][doc['kind']]):
                if headers!=['File','Contents']: continue
                for row in rows:
                    name=clean(row['File'])
                    if any(name in item['aliases'] for item in result if item['parent']==parent): continue
                    result.append({'parent':parent,'label':record['label'],'clinical':True,'name':name,
                        'aliases':[name],'description':row['Contents'] or 'The README lists this file without a contents description.',
                        'source':source(record,doc['kind'],'Files'),
                        'card':{'name':name,'file':None,'columns':[],'readme_kind':doc['kind'],
                                'dictionaries':[],'source_files':[name]}})
        # Include individually named source files that have no prepared fake example.
        if record.get('documentation_only'):
            continue
        documents=[('original',catalog.documents[parent]['original_section'])]+[
            (d['kind'],catalog.documents[parent][d['kind']]) for d in record.get('original_readmes',[])]
        for kind,document in documents:
            for i,line in enumerate(document.splitlines()):
                values=re.findall(r'`((?://|/n/)[^`\n]+)`',line)
                if not values:
                    match=re.search(r'((?://SMB|/n/)[^\n]+)',line,re.I)
                    values=[match[1].strip()] if match else []
                for path in values:
                    if path.endswith('`'): path=path[:-1]
                    def same_source(item):
                        card=item.get('card',{})
                        location=(card.get('location') or '').rstrip('/').lower()
                        candidates=[location]+[location+'/'+f.lower() for f in card.get('source_files',[])]
                        return item['parent']==parent and path.rstrip('/').lower() in candidates
                    lines=document.splitlines()
                    following=lines[i+1] if i+1<len(lines) else ''
                    columns=[]
                    column_match=re.match(r'Columns(?::| are )\s*(.+)',following)
                    if column_match and not column_match[1].startswith('unnamed'):
                        columns=[c.strip() for c in column_match[1].split(',')]
                    existing=next((item for item in result if same_source(item)),None)
                    if existing:
                        if columns and not existing['card'].get('columns'):
                            existing['card']['columns']=columns
                            existing['card']['readme_kind']=existing['card'].get('readme_kind') or kind
                        if following.startswith('Columns are unnamed'):
                            existing['card']['column_notes']=following
                            existing['source']={'kind':'original','label':"Sara's original documentation",
                                                'url':f'/api/datasets/{parent}/readme/original'}
                        continue
                    context=next((l.strip() for l in reversed(lines[:i]) if l.strip() and not
                                  re.search(r'/n/|//SMB|^Columns|^Data:?$|^Code:?$|```|^\|',l,re.I)), '')
                    citation=source(record,kind) if kind!='original' else {'kind':'original','label':"Sara's original documentation",
                                                                             'url':f'/api/datasets/{parent}/readme/original'}
                    name=basename(path)
                    result.append({'parent':parent,'label':record['label'],'clinical':True,'name':name,
                        'aliases':[name,path],'description':line.strip() if kind!='original' else context,
                        'source':citation,'card':{'name':name,'file':None,'columns':columns,'location':path,
                            'readme_kind':kind,'dictionaries':[],'source_files':[name]}})
    for parent,entry in catalog.library.entries.items():
        section=entry.get('sections',{}).get('Files and dataset identity','')
        paths=[] if 'west' in entry else [p.strip() for p in entry['canonical_location'].split('; ')
                                         if p.strip().startswith('/')]
        names={basename(p) for p in paths}
        names.update(re.findall(r'`([^`\n]+)`',section))
        if 'west' in entry:
            names={'patient_summary.csv','Individual patient files'}
        for name in sorted({basename(value) for value in names}):
            value=next((v for v in sorted(names) if basename(v)==name and '/' in v),name)
            # Exclude metadata values, checksums and authority/account identifiers.
            if not value or re.fullmatch(r'[0-9a-f]{12,}|\d+|[a-z0-9_]+:[a-z0-9_]+',value): continue
            relevant=[line.strip().removeprefix('- ') for line in section.splitlines() if '`'+value+'`' in line]
            location=next((p for p in paths if basename(p)==name),None)
            description='\n'.join(relevant) or entry['description']
            columns=[]
            if 'west' in entry:
                group='Patient summary file' if name=='patient_summary.csv' else name
                columns=[c for c in entry['west']['columns'] if c['File']==group]
                description=next((line.removeprefix('- ') for line in entry['west']['processed'].splitlines()
                                  if ('patient_summary.csv' in line if name=='patient_summary.csv' else 'Patient-level' in line)),name)
            result.append({'parent':parent,'label':entry['label'],'clinical':False,'name':name,
                           'description':description,'aliases':[value,name,location], 'location':location,
                           'column_descriptions':columns,'source':catalog.library.source(entry,'Metadata' if 'west' in entry else 'Files and dataset identity')})
    for item in result:
        item['id']=item['parent']+':'+hashlib.sha256((item['name']+'|'+str(item.get('card',{}).get('location',item.get('location')))).encode()).hexdigest()[:12]
        item['aliases']=[a for a in dict.fromkeys(item['aliases']) if a and (
            len(norm(a).split())>=2 or re.search(r'\.[A-Za-z0-9]{1,8}$',a) or re.search('[A-Z_0-9]',a))]
        if not item['clinical']:
            entry=catalog.library.entries[item['parent']]
            item['aliases']=[a for a in item['aliases'] if norm(a) not in {norm(x) for x in entry['aliases']}]
    return result


OPERATIONS=set('a an the i we you our this these those them their it its is are was were do does did have has '
    'what which where how can could would should want wanted please tell show see find get me about with to of '
    'for from in on at and or also available availability data dataset datasets resource resources records information '
    'details detail more further overview describe description help explain use using look looks like structure '
    'file files path paths location original readme documented columns column schema fields field preview sample '
    'samples fake synthetic rows row first five 5 10 monthly daily raw codified nlp type types dictionary contents '
    'o2 eris server storage stored notebook worksheet patient patients start started guide code script counts count '
    'ms multiple sclerosis mass general brigham pittsburgh'.split())


def match_files(catalog,query,previous=None):
    if re.search(r'\b(?:run|compute|calculate|fit|train|execute|perform|compare|versus|vs)\b',query,re.I): return []
    q=' '+norm(query)+' '
    explicit=[]
    if re.search(r'\bibd\b|inflammatory bowel',q): explicit.append('IBD')
    if re.search(r'\bmgb ad\b|\bmgb alzheimer',q): explicit.append('MGB_AD')
    if re.search(r'\bupmc ad\b|\bupmc alzheimer',q): explicit.append('UPMC_AD')
    explicit += ms_ids(query, catalog.records)
    explicit += [i for i,e in catalog.library.entries.items() if ' '+norm(e['label'])+' ' in q]
    if not explicit: explicit=catalog.library.explicit(query)
    matches=[]
    for item in file_inventory(catalog):
        aliases=[a for a in item['aliases'] if ' '+norm(a)+' ' in q]
        if not aliases or (explicit and item['parent'] not in explicit): continue
        remaining=q
        for alias in sorted([*aliases,item['label']],key=len,reverse=True):
            remaining=remaining.replace(' '+norm(alias)+' ',' ')
        if not item['clinical']:
            for alias in catalog.library.entries[item['parent']]['aliases']:
                remaining=remaining.replace(' '+norm(alias)+' ',' ')
        known=set(norm(item['description']+' '+item['label']).split())
        if set(remaining.split())-OPERATIONS-known: continue
        matches.append((max(len(norm(a)) for a in aliases),item,remaining))
    if not matches: return []
    best=max(score for score,_,_ in matches)
    matches=[(item,remaining) for score,item,remaining in matches if score==best]
    if len(matches)>1 and previous:
        focused=[m for m in matches if m[0]['parent'] in previous]
        if len(focused)==1: return focused
    return matches


def single_file_answer(catalog,query,previous=None):
    if re.search(r'\bdictionar(?:y|ies)\b',query,re.I) and re.search(r'monthly|raw|daily',query,re.I):
        # Existing dictionary views select the mapping for that file level.
        return None
    matches=match_files(catalog,query,previous)
    if not matches: return None
    if len(matches)>1:
        intro='Which dataset or site do you mean? This file name appears in more than one resource.'
        prefix={'columns':'Show columns for','preview':'Show fake sample rows for',
                'location':'Where can I find'}.get(requested_view(matches[0][1]),'Tell me more about')
        return {'query':query,'engine':'catalog','model':None,'intent':'file_clarification',
            'interpretation':'ambiguous_file','intro':intro,'answer':intro,'datasets':[],'resources':[],
            'sources':[],'context_dataset_ids':[],'pending_topic':None,'warning':None,'compact':True,
            'actions':[{'label':f"{item['label']} — {item['name']}"+(' — '+basename((item.get('card',{}).get('location') or item.get('location','')).rstrip('/').rsplit('/',1)[0])
                        if sum(other['parent']==item['parent'] for other,_ in matches)>1 else ''),
                        'query':f"{prefix} {item['name'] if item.get('card',{}).get('worksheet') else item.get('card',{}).get('location') or item.get('location') or item['aliases'][0]} in {item['label']}"} for item,_ in matches],
            'elapsed_seconds':0}
    item,remaining=matches[0]
    view=requested_view(remaining)
    if view in {'linkage','outcomes','statistics','versions'}: return None
    intro=item['name']
    citation=item['source']
    target=(item['name'] if item['name'] in item['aliases'] else item['aliases'][0])+' in '+item['label']
    actions=[{'label':'Show columns','query':'Show columns for '+target},
             {'label':'Show file location','query':'Where can I find '+target+'?'}]
    common={'query':query,'engine':'catalog','model':None,'intent':view if view in {'columns','preview','location'} else 'single_file',
            'interpretation':'verified_file_metadata' if item['clinical'] and view in {'columns','preview'} else 'verified_single_file','context_dataset_ids':[item['parent']],
            'selected_file_id':item['id'],'pending_topic':None,'warning':None,'compact':False,
            'actions':actions,'elapsed_seconds':0}
    if item['clinical']:
        card={**item['card'],'show_columns':view in {'columns','preview'},
              'show_preview':view=='preview' and bool(item['card'].get('file'))}
        text=item['description']
        if view=='preview' and not card.get('file'):
            intro='Fake sample rows have not been prepared for '+item['name']+'.'
        if view=='columns' and not card.get('columns'):
            intro=('The source columns are unnamed; the README lists their meanings in order.' if card.get('column_notes')
                   else 'Column descriptions have not been supplied for '+item['name']+'.')
        if card.get('file') and view!='preview':
            actions.insert(1,{'label':'Show 5 fake rows','query':'Show 5 fake rows for '+target})
        facts=[{'id':item['id'],'dataset_id':item['parent'],'category':'file','text':text,
                'format':'markdown','source':citation}] if view=='overview' and text else []
        if view=='columns' and card.get('column_notes'):
            facts=[{'id':item['id']+'_column_notes','dataset_id':item['parent'],'category':'columns',
                    'text':card['column_notes'],'format':'text','source':citation}]
        return {**common,'intro':intro,'answer':'\n\n'.join([intro,*[f['text'] for f in facts],
                    item['name']+(': '+', '.join(card['columns']) if card['show_columns'] else '')]),
                'datasets':[{'dataset':catalog.summary(catalog.records[item['parent']]),'facts':facts,
                             'files':[card],'dictionaries':[],'offer_preview':False,
                             'additional_note':None,'date_summary':None}], 'resources':[],'sources':[citation]}
    entry=catalog.library.entries[item['parent']]
    blocks=[{'title':item['name'],'text':item['description'],'items':[],'kind':'bullets'}]
    if view=='columns':
        if item['column_descriptions']:
            blocks=[{'title':item['name'],'items':[],'kind':'bullets',
                     'table':{'columns':['Column','Meaning'],'rows':item['column_descriptions']}}]
        else: intro='Column descriptions have not been supplied for '+item['name']+'.'
    if view=='preview': intro='Fake sample rows have not been prepared for '+item['name']+'.'
    resource={**catalog.library.summary(entry),'selected_file_id':item['id'],'selected_file_name':item['name'],
              'label':item['label'],'blocks':blocks,'source':citation,'sources':[citation],
              'locations':[{'label':'Documented file location','value':item['location'],'kind':'data'}] if item['location'] else [],
              'show_locations':view=='location'}
    return {**common,'intro':intro,'answer':intro+'\n\n'+item['description'],
            'datasets':[],'resources':[resource],'sources':[citation]}
