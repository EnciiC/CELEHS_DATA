"""Direct storage answers derived from explicit metadata, not inferred absence."""

import re


def requested_platforms(query):
    q = query.lower()
    platforms = []
    if re.search(r'\bo2\b', q): platforms.append('O2')
    if re.search(r'\beris\b', q): platforms.append('Eris')
    if re.search(r'\bwindows\b|\bsfa\b|\bmgb\s+server', q): platforms.append('MGB Windows/SFA')
    if re.search(r'\baras\b', q): platforms.append('ARAS')
    return platforms


def is_storage_question(query):
    q = query.lower()
    if re.search(r'column|schema|dictionary|dictionaries|sample|preview|look like|count.*types|patient count|cohort size|where|\bpath\b|guide|access|permission|license|study|research', q): return False
    return bool(requested_platforms(query) and re.search(r'available|stored|copy|copies|located|hosted|\bon\b|\bin\b|find|access|where', q))


def names(records):
    labels = [r['label'] for r in records]
    return labels[0] if len(labels) == 1 else ' and '.join(labels) if len(labels) == 2 else ', '.join(labels[:-1]) + ' and ' + labels[-1]


def storage_list(record):
    return ' and '.join(record['storage_platform'])


def platform_status(record, platform):
    if platform == 'O2' and isinstance(record.get('has_o2_copy'), bool):
        return record['has_o2_copy']
    if platform in record['storage_platform']: return True
    # A different documented location does not prove no other copy exists.
    return None


def direct_storage_answer(records, query):
    platforms = requested_platforms(query)
    plural = len(records) > 1
    verb = 'are' if plural else 'is'
    if len(platforms) == 1:
        platform = platforms[0]
        status = [platform_status(r, platform) for r in records]
        if all(s is True for s in status):
            return f"Yes. {names(records)} {verb} stored on {platform}."
        if len(records) == 1 and status[0] is False:
            r = records[0]
            return f"No. {r['label']} is stored on {storage_list(r)}, not {platform}."
        sentences = []
        for r, exists in zip(records, status):
            if exists is True: sentences.append(f"{r['label']} is stored on {platform}.")
            elif exists is False: sentences.append(f"{r['label']} is stored on {storage_list(r)}, not {platform}.")
            else: sentences.append(f"The documentation lists {storage_list(r)} for {r['label']}. A copy on {platform} is not documented.")
        return ' '.join(sentences)
    sentences = []
    for r in records:
        sentence = f"{r['label']} is stored on {storage_list(r)}."
        if r.get('has_o2_copy') is False: sentence += ' There is no O2 copy.'
        sentences.append(sentence)
    return ' '.join(sentences)
