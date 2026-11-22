"""Answer named clinical README questions and their documented follow-ups."""
import re

from .resource_guides import norm, purpose


def clinical_guide_answer(catalog, query, previous, selection):
    library = catalog.library
    q = norm(query)
    if re.search(r'\b(compare|versus|vs|download real|real patient|uk biobank|prs|ibd|alzheimer|multiple sclerosis|ms|ad)\b', q):
        return None
    named = library.explicit(query)
    ids = named or ([selection['id']] if selection and selection.get('kind')=='resource' else previous or [])
    if not named and not re.search(r'\b(mgb|upmc|bch|vinci|va)\b', q) and re.search(r'\b(ra|rheumatoid arthritis)\b', q):
        ids = ['KDI_RA']
    if len(ids)!=1 or ids[0] not in library.entries or 'guide' not in library.entries[ids[0]]:
        return None
    entry = library.entries[ids[0]]
    requested = purpose(query)
    matched = any(re.search(s['match'],q) for s in entry['guide']['sections'])
    if requested=='compare' or (not named and not matched and requested=='overview' and 'tell me more' not in q):
        return None
    if matched and requested not in {'location','access'}:
        requested='topic'
    if requested=='samples':
        intro='The README describes the file structure. This entry has no synthetic sample rows.'
        requested='columns'
    else:
        intro=entry['label']
    view = library.view(entry,requested,query)
    if not view['blocks'] and not view['show_locations']:
        intro='The README does not document that detail.'
    lines=[intro,*[b['text'] or '\n'.join(b['items']) for b in view['blocks']]]
    return {'query':query,'engine':'catalog','model':None,'intent':'resource_'+requested,
            'intro':intro,'answer':'\n\n'.join(lines),'datasets':[],'resources':[view],
            'sources':view['sources'],'context_dataset_ids':ids,'selection':{'kind':'resource','id':ids[0]},
            'pending_topic':None,'warning':None,'compact':False,'actions':[],'elapsed_seconds':0}
