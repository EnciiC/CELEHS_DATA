"""Stateless conversational focus for the file/resource the user selected."""
import re

from .resource_guides import norm
from .single_files import file_inventory,match_files,single_file_answer
from .readme_topics import topic_answer


def valid_selection(catalog,selection):
    if not isinstance(selection,dict): return None
    kind=selection.get('kind'); key=selection.get('id')
    if kind=='file' and any(f['id']==key for f in file_inventory(catalog)):
        return {'kind':kind,'id':key,'view':selection.get('view','overview')}
    if kind=='dataset' and key in catalog.records: return {'kind':kind,'id':key}
    if kind=='resource' and key in catalog.library.entries: return {'kind':kind,'id':key}
    if kind=='topic' and any(key==parent+':'+t['id'] for parent,r in catalog.records.items() for t in r.get('readme_topics',[])):
        return {'kind':kind,'id':key}
    if kind=='choices':
        ids=selection.get('ids',[])
        if isinstance(ids,list) and 1<len(ids)<=19 and all(i in catalog.records or i in catalog.library.entries for i in ids):
            return {'kind':'choices','ids':list(dict.fromkeys(ids))}
    return None


def followup_view(query):
    q=norm(query)
    q=re.sub(r'^please | please$','',q)
    q=re.sub(r'^(?:can|could|would) you (?:please )?','',q)
    q=re.sub(r'^(?:provide|share) (?:some |a few )?(?:more )?(?:details|information)$','tell me more',q)
    q=re.sub(r'^(?:elaborate|expand)(?: (?:on|about) (?:it|this|that))?$','tell me more',q)
    q=re.sub(r'^more (?:on|about) (?:it|this|that)$','tell me more',q)
    q=re.sub(r' (?:for|from|in|of) (?:it|this|that|this file|this dataset)$','',q)
    if re.fullmatch(r'(?:what|which) (?:else|other data|other datasets|other files|other resources)(?: do (?:we|you) have)?(?: are available)?',q): return 'broader'
    patterns=[
        ('original',r'^(?:(?:can|could|may) i (?:see|read)|(?:please )?(?:show|open|read|view)(?: me)?) (?:the |its |their )?(?:original )?readme(?: file| documentation)?$'),
        ('location',r'^(?:where (?:is|are|can i find|can i get|do i find)(?: it| this| that| these| those| the file| this file| the data| the dataset)?|what(?: is| s) (?:its |the )?(?:file )?(?:path|location)|how (?:do|can) i find (?:it|this|that))(?: located| stored| saved)?$'),
        ('columns',r'^(?:(?:show|list|explain|describe)(?: me)? (?:its |the |these |those )?(?:columns|column names|fields|variables|schema)|what (?:are|s) (?:its |the )?(?:columns|column names|fields|variables|schema)|what (?:does|do) (?:it|this|that|these|those|the data|the dataset|the file) look like|how is (?:it|this|that) structured)$'),
        ('preview',r'^(?:(?:show|give)(?: me)? (?:some |a few |the |first )?(?:\d+ )?(?:fake |synthetic |sample |example )*(?:rows|data|examples|preview)|(?:can|could|may) i see (?:(?:some |a few |a |the )?(?:fake |synthetic |sample |example )*(?:rows|data|examples|preview))|(?:any|some) examples)$'),
        ('access',r'^(?:what about access|who can (?:use|access) (?:it|this)|how (?:do|can) i (?:get access|access) (?:it|this)|what (?:are|s) (?:the )?access (?:requirements|rules))$'),
        ('start',r'^(?:how (?:do|can|should) i (?:get started|start|begin|use (?:it|this|that))|how to (?:start|use (?:it|this|that))|what can i do with (?:it|this|that))$'),
        ('code',r'^(?:what (?:code|scripts) (?:is|are) available|show (?:me )?(?:the )?(?:code|scripts)|how was (?:it|this|that) processed)$'),
        ('linkage',r'^how (?:do|can|should) i (?:link|connect|join|merge) (?:it|this|that|these|those)(?: with| to)? (?:our |the |existing )*ehr$'),
        ('details',r'^(?:(?:please )?(?:tell|show|give) (?:me|us) (?:more|more details|more information|the details)(?: (?:about|on) (?:it|this|that|these|those|this file|this dataset|this resource|the file|the dataset))?|tell me about (?:it|this|that)|(?:more|more details|more information|details)(?: please)?|(?:can|could) i (?:get|have) (?:more )?(?:details|information)|(?:go on|continue|elaborate|explain(?: (?:it|this|that))?|what else should i know|what(?: does (?:it|this|that) contain| s in (?:it|this|that)| is (?:it|this|that))))$'),
    ]
    for view,pattern in patterns:
        if re.fullmatch(pattern,q): return view
    return None


def parent_selection(catalog,previous):
    ids=[i for i in previous or [] if i in catalog.records or i in catalog.library.entries]
    if len(ids)>1: return {'kind':'choices','ids':ids}
    if len(ids)==1: return {'kind':'dataset' if ids[0] in catalog.records else 'resource','id':ids[0]}
    return None


def infer_selection(catalog,result,query):
    if result.get('interpretation')=='ambiguous_file': return None
    if result.get('selected_file_id'):
        return valid_selection(catalog,{'kind':'file','id':result['selected_file_id'],'view':result.get('intent','overview')})
    parents=result.get('context_dataset_ids',[])
    files=[(s['dataset']['id'],f) for s in result.get('datasets',[]) for f in s.get('files',[])]
    inventory=file_inventory(catalog)
    named=match_files(catalog,query,parents)
    if len(named)==1:
        return {'kind':'file','id':named[0][0]['id'],'view':result.get('intent','overview')}
    if len(files)==1:
        parent,card=files[0]
        matching=[f for f in inventory if f['clinical'] and f['parent']==parent and
                  f['card'].get('location')==card.get('location') and
                  ((bool(card.get('file')) and f['card'].get('file')==card.get('file')) or f['name']==card['name'])]
        if len(matching)==1: return {'kind':'file','id':matching[0]['id'],'view':result.get('intent','overview')}
    if files and len(parents)==1:
        topics={f.get('topic_id') for _,f in files}
        if len(topics)==1 and None not in topics:
            return {'kind':'topic','id':parents[0]+':'+topics.pop()}
    return parent_selection(catalog,parents)


def clarification(catalog,query,focus,previous):
    actions=[]
    if focus and focus['kind']=='choices':
        for key in focus['ids']:
            label=catalog.records[key]['label'] if key in catalog.records else catalog.library.entries[key]['label']
            actions.append({'label':label,'query':'Tell me more about '+label})
        intro='Which dataset or resource would you like to explore?'
    else:
        intro='Which file or resource would you like to explore?'
        actions=[{'label':'Browse resources','view':'browse'}]
    return {'query':query,'engine':'guide','model':None,'intent':'exploration_choice','interpretation':'exploration_choice',
        'intro':intro,'answer':intro,'datasets':[],'resources':[],'sources':[],'warning':None,'compact':True,
        'actions':actions,'context_dataset_ids':previous or [],'pending_topic':None,'selection':focus,'elapsed_seconds':0}


def file_guidance(catalog,item,view,query):
    target=item['name'] if item.get('card',{}).get('worksheet') else item.get('card',{}).get('location') or item.get('location') or item['aliases'][0]
    explicit=target+' in '+item['label']
    if view=='linkage' and item['clinical']:
        result=topic_answer(catalog,f"How do I link {item['name']} with EHR?",[item['parent']])
        if result: return result
    if view in {'start','access','code'} and not item['clinical']:
        resource=catalog.library.view(catalog.library.entries[item['parent']],view,query)
        resource.update(selected_file_id=item['id'],selected_file_name=item['name'])
        resource['locations']=[{'label':'Documented file location','value':item['location'],'kind':'data'}] if item['location'] else []
        text='\n\n'.join(b.get('text') or '\n'.join(b.get('items',[])) for b in resource['blocks'])
        return {'engine':'catalog','model':None,'intent':'file_guidance','intro':item['name'],'answer':item['name']+'\n\n'+text,
            'datasets':[],'resources':[resource],'sources':resource['sources'],'context_dataset_ids':[item['parent']],
            'actions':[],'pending_topic':None,'warning':None,'compact':False,'elapsed_seconds':0}
    request={'columns':'Show columns for ','preview':'Show fake sample rows for ','location':'Where can I find '}.get(view,'Tell me more about ')+explicit
    result=single_file_answer(catalog,request,[item['parent']])
    if result is None: return None
    if view=='details' and item['clinical']:
        for section in result['datasets']:
            for card in section['files']:
                if card.get('columns') and len(card['columns'])<=12:
                    card['show_columns']=True
                    result['answer']+='\n\nColumns: '+', '.join(card['columns'])
    if view=='original':
        summary = item['clinical'] and catalog.records[item['parent']].get('public_summary')
        result['intro']=('Documentation for ' if summary else 'Original README for ')+item['name']
        label = 'Open documentation' if summary else 'Open original README'
        action={'label':label,'document':{'resource_id':item['parent']}} if not item['clinical'] else {
            'label':label,'document':{'dataset_id':item['parent'],'kind':item['source']['kind'] if item['source']['kind']!='notes' else 'original'}}
        result['actions'].insert(0,action)
    if view in {'access','start','code','linkage'} and item['clinical']:
        result['intro']={'access':'Access instructions','start':'Usage instructions','code':'Processing code','linkage':'Linkage instructions'}[view]+' for '+item['name']
        result['datasets'][0]['facts']=[]
        result['datasets'][0]['additional_note']='See the original README for these instructions.'
        result['answer']=result['intro']+'\n\nSee the original README for these instructions.'
    return result


def column_explanation(catalog,query,focus):
    if not focus or focus['kind']!='file': return None
    q = norm(query)
    context_suffix = r' (?:(?:right )?here|(?:in|for) (?:this|that|the current) (?:file|table|dataset))'
    match = re.fullmatch(
        r'(?:what (?:does|is|s) (?:the )?(?:column |field )?(.+?)(?: mean)?'
        r'|explain (?:the )?(?:column |field )?(.+?))'
        rf'(?:{context_suffix})?', q)
    if not match: return None
    requested=next(x for x in match.groups() if x)
    if requested in {'it','this','that','these','those','it mean','this mean'}: return None
    item=next(f for f in file_inventory(catalog) if f['id']==focus['id'])
    if item['clinical']:
        rows=item['card'].get('column_descriptions',[])
        if not rows:
            rows=[r for r in catalog.records[item['parent']]['column_descriptions']
                  if r['File']==item['card'].get('file')]
    else: rows=item['column_descriptions']
    rows=[r for r in rows if norm(r['Column'])==requested]
    if len(rows)!=1 or not rows[0].get('Meaning'): return None
    row=rows[0]
    result=file_guidance(catalog,item,'columns',query)
    if result is None:
        return None
    result['intro']=row['Column']+': '+row['Meaning']
    result['answer']=result['intro']
    if item['clinical']:
        for section in result['datasets']:
            section['facts']=[]
            for card in section['files']:
                card['columns']=[row['Column']]
                if card.get('column_descriptions'):
                    card['column_descriptions'] = [row]
    else:
        result['resources'][0]['blocks']=[{'title':row['Column'],'text':row['Meaning'],'items':[],'kind':'bullets'}]
    return result


def resolve_exploration(catalog,query,selection,previous):
    """Return a ready answer or a rewritten request; named new subjects bypass this."""
    view=followup_view(query)
    focus=valid_selection(catalog,selection) or parent_selection(catalog,previous)
    if not view:
        result=column_explanation(catalog,query,focus)
        if result:
            result['query']=query
            result['selection']={**focus,'view':'columns'}
            return result,None,focus
        return None,None,None
    if not focus or focus['kind']=='choices': return clarification(catalog,query,focus,previous),None,focus
    if view=='broader':
        parent=focus['id'].split(':',1)[0] if focus['kind'] in {'file','topic'} else focus['id']
        if parent in catalog.records: return None,'What data do we have in '+catalog.records[parent]['label']+'?',None
        return None,'What resources do we have?',None
    if focus['kind']=='file':
        item=next(f for f in file_inventory(catalog) if f['id']==focus['id'])
        result=file_guidance(catalog,item,view,query)
        if result is None: return clarification(catalog,query,focus,previous),None,focus
        if result:
            result['query']=query
            result['selection']={**focus,'view':view}
        return result,None,focus
    if focus['kind']=='topic':
        parent,key=focus['id'].split(':',1)
        label=next(t['name'] for t in catalog.records[parent]['readme_topics'] if t['id']==key)
    elif focus['kind']=='dataset': label=catalog.records[focus['id']]['label']
    else: label=catalog.library.entries[focus['id']]['label']
    if view == 'original' and focus['kind'] == 'dataset' and catalog.records[focus['id']].get('documentation_only'):
        return None, 'Show the original preprocessing README for ' + label, focus
    prefix={'columns':'Show columns for ','preview':'Show fake sample rows for ','location':'Where can I find ',
            'start':'How do I get started with ','access':'What access requirements apply to ',
            'code':'What code is documented for ','linkage':'How do I link '}.get(view,'Tell me more about ')
    return None,prefix+label+(' with EHR?' if view=='linkage' else ''),focus
