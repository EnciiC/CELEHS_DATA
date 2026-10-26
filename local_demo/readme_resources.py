"""Source-backed views of additional original READMEs; never open patient data."""

import re
from pathlib import Path


def clean(text):
    return text.replace('`', '').replace('**', '').strip()


def tables(text):
    """Parse the simple pipe tables in the supplied Markdown documents."""
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines[:-1]):
        if not line.startswith('|') or not re.fullmatch(r'\s*\|[\s:|\-]+\|\s*', lines[i + 1]):
            continue
        headers = [clean(c) for c in line.strip().strip('|').split('|')]
        rows = []
        for row in lines[i + 2:]:
            if not row.startswith('|'):
                break
            cells = [c.strip() for c in row.strip().strip('|').split('|')]
            if len(cells) != len(headers):
                raise ValueError('Unexpected original README table shape')
            rows.append(dict(zip(headers, cells)))
        result.append((headers, rows))
    return result


def section(text, heading):
    match = re.search(r'^(' + r'#{1,6}' + r') ' + re.escape(heading) + r'\s*$', text, re.M)
    if not match:
        raise ValueError('Missing README section: ' + heading)
    end = re.search(r'^#{1,' + str(len(match[1])) + r'} ', text[match.end():], re.M)
    return text[match.end():match.end() + end.start() if end else len(text)].strip()


def source(record, kind, heading=None):
    doc = next(d for d in record['original_readmes'] if d['kind'] == kind)
    return {'kind': kind, 'label': doc['label'], 'file': doc['file'],
            'url': f"/api/datasets/{record['dataset_id']}/readme/{kind}", 'heading': heading}


def fact(record, key, category, text, kind, heading=None, markdown=False):
    return {'id': f"{record['dataset_id']}:{key}", 'dataset_id': record['dataset_id'],
            'category': category, 'text': text, 'source': source(record, kind, heading),
            'format': 'markdown' if markdown else 'text'}


def prepare_readmes(record, directory):
    docs = {}
    for doc in record.get('original_readmes', []):
        name, kind = doc['file'], doc['kind']
        if Path(name).name != name or not name.endswith('.md') or not re.fullmatch(r'[a-z][a-z0-9_]+', kind):
            raise ValueError('Unsafe original README registration')
        if kind in {'original', 'original_section', 'catalog', 'synthetic', 'notes', 'tracker'}:
            raise ValueError('Original README kind overlaps internal documents')
        docs[kind] = (directory / name).read_text(encoding='utf-8-sig')
    record['documented_files'] = []
    if 'ibd_lab' in docs:
        text = docs['ibd_lab']
        parsed = tables(text)
        columns = next(rows for headers, rows in parsed if headers == ['Column', 'Description'])
        coverage = next(rows for headers, rows in parsed if 'Source measurements' in headers)
        location = re.search(r'^- Folder: `([^`]+)`', text, re.M)[1]
        filenames = re.findall(r'^- Main (?:RDS|CSV): `([^`]+)`', text, re.M)
        script = re.search(r'^- Processing script: `([^`]+)`', text, re.M)[1]
        row_meaning = re.search(r'^Each row represents (.+)', text, re.M)[1]
        field_rows = [{'Column': col, 'Meaning': row['Description']} for row in columns
                      for col in re.findall(r'`([^`]+)`', row['Column'])]
        record['lab_summary'] = {'coverage': coverage, 'coverage_text': section(text, 'Dataset coverage and repeated measurements')}
        record['documented_files'].append({
            'id': 'ibd_lab_monthly', 'name': 'IBD monthly laboratory summary',
            'file': None, 'location': location, 'source_files': filenames,
            'columns': [r['Column'] for r in field_rows], 'column_descriptions': field_rows,
            'row_meaning': row_meaning[0].upper() + row_meaning[1:], 'owner': re.search(r'^\*\*Owner:\*\* (.+)', text, re.M)[1],
            'processing_script': location + script, 'readme_kind': 'ibd_lab',
            'synthetic': False, 'preview_available': False,
            'source': source(record, 'ibd_lab', 'Main output'),
            'description': section(text, 'Purpose'),
            'dictionaries': [], 'show_columns': False,
        })
        record['resources'].append({
            'name': 'IBD monthly laboratory summary', 'kind': 'Processed laboratory data',
            'location': location, 'description': section(text, 'Purpose'),
            'source_kind': 'ibd_lab', 'source': 'IBD_LAB_MONTHLY_README.md',
        })
    if 'ibd_project' in docs:
        text = docs['ibd_project']
        aims = next(rows for headers, rows in tables(text) if headers == ['Aim', 'Objective', 'Workstream'])
        derived = next(rows for headers, rows in tables(text) if headers == ['Aim', 'Features', 'Outcomes', 'Processing scripts folder'])
        headings = list(re.finditer(r'^# (Aim [1-5][^\n]*)', text, re.M))
        aim_sections = {}
        for i, match in enumerate(headings):
            end = headings[i + 1].start() if i + 1 < len(headings) else text.index('# End-to-End Execution Steps')
            aim_sections[match[1].split()[1]] = text[match.start():end].strip()
        if len(aims) != 5 or len(aim_sections) != 5:
            raise ValueError('Expected the five MAJOR project aims')
        record['ibd_project'] = {'aims': aims, 'derived': derived, 'sections': aim_sections}
    return docs


def is_lab_query(query):
    # "In our lab" describes the organization, not laboratory measurements.
    subject = re.sub(r'\bin (?:the |our )?lab\b(?!\s+(?:data|values|measurements|summary))|\b(?:our lab|lab inventory|lab resources|lab datasets|lab members)\b', '', query, flags=re.I)
    return bool(re.search(r'\blabs?\b|laborator|\b(?:albumin|crp|esr|fcp|hemoglobin|haemoglobin|calprotectin)\b', subject, re.I))


def is_project_query(query):
    return bool(re.search(
        r'\bmajor\b|\baims?\b|\bproject\b|workstreams?|what (?:have|has|did).*?(?:done|studied|analysed|analyzed)|'
        r'what (?:can|could).*?(?:do|study|use)|what.*?(?:analyses|analyses? have|prior work)|'
        r'previous(?:ly)? (?:work|stud|analys)|what.*?(?:done|accomplished).*?ibd', query, re.I))


def extra_facts(record, docs):
    result = []
    for item in record.get('documented_files', []):
        result.append(fact(record, 'lab_overview', 'lab', item['name'] + ': ' + item['description'], 'ibd_lab', 'Purpose'))
        result.append(fact(record, 'lab_columns', 'columns', item['name'] + ' columns: ' + ', '.join(item['columns']) + '. ' + item['row_meaning'], 'ibd_lab', 'Main output'))
        # Preserve the README's row/patient/measurement distinctions in retrieval.
        result.append(fact(record, 'lab_coverage', 'statistics', record['lab_summary']['coverage_text'], 'ibd_lab', 'Dataset coverage and repeated measurements'))
    project = record.get('ibd_project')
    if project:
        result.append(fact(record, 'project_overview', 'project', 'MAJOR IBD project: ' + section(docs['ibd_project'], 'Purpose'), 'ibd_project', 'Purpose'))
        for row in project['aims']:
            result.append(fact(record, 'project_' + row['Aim'].lower().replace(' ', '_'), 'project',
                               f"{row['Aim']}: {row['Objective']}. {row['Workstream']}.", 'ibd_project', row['Aim']))
    return result


def lab_answer_facts(record, query, purpose):
    text = record['lab_summary']['coverage_text']
    if purpose in {'statistics', 'dates'}:
        requested = [row for row in record['lab_summary']['coverage'] if re.search(r'\b' + clean(row['Laboratory']) + r'\b', query, re.I)]
        if re.search(r'calprotectin', query, re.I):
            requested = [row for row in record['lab_summary']['coverage'] if row['Laboratory'] == 'FCP']
        if requested:
            fields = ['First month', 'Last month'] if purpose == 'dates' else ['Patients'] if re.search(r'how many.*patient|patient count', query, re.I) else ['Monthly rows'] if re.search(r'how many.*rows?', query, re.I) else ['Source measurements'] if re.search(r'how many.*measurements?', query, re.I) else [k for k in requested[0] if k != 'Laboratory']
            text = '\n\n'.join(clean(row['Laboratory']) + ': ' + '; '.join(k + ': ' + row[k] for k in fields) for row in requested)
        elif purpose == 'dates':
            text = '| Laboratory | First month | Last month |\n| --- | --- | --- |\n' + '\n'.join(
                '| ' + ' | '.join(row[k] for k in ('Laboratory', 'First month', 'Last month')) + ' |' for row in record['lab_summary']['coverage'])
            text += '\n\nDate percentiles are not reported in this laboratory README.'
        elif re.search(r'how many.*(?:patient|rows?|measurements?)|patient count', query, re.I):
            marker = 'unique patients' if re.search(r'patient', query, re.I) else 'contributing source measurements' if re.search(r'measurement', query, re.I) else 'patient-lab-unit-month rows'
            text = 'The laboratory README reports ' + next(line.strip('- ;') for line in text.splitlines() if marker in line and line.startswith('- ')) + '.'
        return [fact(record, 'lab_answer_coverage', 'statistics', text, 'ibd_lab', 'Dataset coverage and repeated measurements', True)]
    if purpose in {'columns', 'preview', 'dictionary'}:
        return []
    item = record['documented_files'][0]
    labs = ', '.join(row['Laboratory'] for row in record['lab_summary']['coverage'])
    return [fact(record, 'lab_answer_overview', 'lab', item['description'] + '\nLabs: ' + labs + '. Owner: ' + item['owner'] + '.', 'ibd_lab', 'Purpose')]


def project_answer_facts(record, query):
    project = record['ibd_project']
    requested_aims = re.findall(r'\baim\s*([1-5])\b', query, re.I)
    pair = re.search(r'\baims?\s*([1-5])\s*(?:and|versus|vs\.?|&)\s*(?:aim\s*)?([1-5])\b', query, re.I)
    if pair:
        requested_aims += list(pair.groups())
    requested_aims = list(dict.fromkeys(requested_aims))
    if len(requested_aims) > 1:
        base = re.sub(r'\baims?\s*[1-5](?:\s*(?:and|versus|vs\.?|&)\s*(?:aim\s*)?[1-5])?', '', query, flags=re.I)
        return [f for number in requested_aims for f in project_answer_facts(record, base + ' Aim ' + number)]
    number = re.search(r'\baim\s*([1-5])\b', query, re.I)
    if number:
        aim = number[1]
        text = project['sections'][aim]
        requested = None
        for pattern, heading in [
            (r'\bresult|finding|auc|ppv|c.index|performance|effect estimate', 'Latest results' if aim == '5' else 'Main findings' if aim == '4' else 'Modeling and results'),
            (r'\boutcome|\brules?\b|response definition', 'Cohorts and outcomes' if aim == '5' else 'Treatment-response outcome' if aim == '4' else 'Composite outcome'),
            (r'\bwindow|baseline|\bt0\b|index date', 'Analysis' if aim == '5' else 'Predictors and analysis' if aim == '4' else 'Feature windows and construction'),
        ]:
            if re.search(pattern, query, re.I):
                try:
                    requested = section(text, heading)
                except ValueError:
                    pass
                break
        row = next(r for r in project['aims'] if r['Aim'] == 'Aim ' + aim)
        folder = next(r['Processing scripts folder'] for r in project['derived'] if r['Aim'] == row['Aim'])
        overview = f"## {row['Aim']}\n\n{row['Objective']}\n\n{row['Workstream']}\n\n**Processing scripts folder:** {folder}"
        if requested:
            overview += '\n\n' + requested
        elif not re.search(r'where|folder|path|location', query, re.I):
            # A bounded exact excerpt, rather than an invented project summary.
            overview += '\n\n' + text.split('\n', 1)[1].strip()[:3400]
        return [fact(record, 'project_answer_aim_' + aim, 'project', overview,
                     'ibd_project', 'Aim ' + aim, True)]
    rows = ['| Aim | Objective | Workstream |', '| --- | --- | --- |']
    rows += ['| ' + ' | '.join(row[k] for k in ('Aim', 'Objective', 'Workstream')) + ' |' for row in project['aims']]
    return [fact(record, 'project_answer_aims', 'project',
                 '## MAJOR IBD project\n\nThe project README documents these five aims:\n\n' + '\n'.join(rows),
                 'ibd_project', 'Study aims and implemented workstreams', True)]
