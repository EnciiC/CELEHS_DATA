"""Short schema comparisons derived from documented column meanings."""

import re


def column_roles(record, file):
    fields = [f for f in record['column_descriptions'] if f['File'] == file['file']]
    roles = {}
    for field in fields:
        meaning = field['Meaning'].lower()
        if re.search(r'number of occurrences', meaning): roles['count'] = field['Column']
        elif re.search(r'patient identifier', meaning): roles['patient'] = field['Column']
        elif re.search(r'(?:code after|grouped codified feature|(?:nlp )?concept identifier)', meaning):
            roles['code'] = field['Column']
    return roles


def comparison_summary(query, sections, records):
    if not re.search(r'compar|difference|differ|similar|versus|\bvs\b|same columns', query, re.I): return None
    if len(sections) < 2 or re.search(r'\bdaily\b|\braw\b', query, re.I): return None
    groups = {}
    evidence = []
    for section in sections:
        record = records[section['dataset']['id']]
        for file in section.get('files', []):
            if not file.get('file') or 'monthly' not in file['file'].lower(): continue
            if not {'month','year'}.issubset(file['columns']): continue
            roles = column_roles(record, file)
            if not {'count','code','patient'}.issubset(roles): continue
            kind = 'NLP' if 'nlp' in file['file'].lower() else 'Codified'
            groups.setdefault(kind, []).append((record['label'], roles))
            evidence.append({'kind':'schema','label':'Documented column meanings','dataset_id':record['dataset_id'],
                             'url':f"/api/datasets/{record['dataset_id']}/schema"})
    lines, different = [], False
    for kind in ['Codified','NLP']:
        items = groups.get(kind, [])
        if len({label for label,_ in items}) < 2: continue
        different |= len({(roles['patient'],roles['code'],roles['count']) for _,roles in items}) > 1
        details = '; '.join(f"{label} uses `{roles['code']}` and `{roles['count']}`" for label,roles in items)
        lines.append(kind + ': ' + details + '.')
    if not lines: return None
    summary = 'The monthly files use a similar structure: a patient, calendar month/year, code or concept, and occurrence count. '
    summary += 'Some column names differ.' if different else 'The documented patient, code/concept and count column names match.'
    return {'summary':summary, 'details':lines,
            'caution':'Similar structure does not establish that code mappings or cohorts are interchangeable.',
            'sources':list({e['dataset_id']:e for e in evidence}.values())}
