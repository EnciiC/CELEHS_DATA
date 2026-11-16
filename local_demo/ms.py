"""Dataset Finder entries for Benet's multiple sclerosis documentation."""

import json
import re

from lxml import html

from .readme_resources import clean, fact, is_lab_query, section, source


SITES = ('MGB', 'UPMC')
MS_QUERY = r'\b(?:multiple sclerosis|ms|promote(?: registry)?)\b'
SITE_QUERY = {'MGB': r'\b(?:mgb|mass general(?: brigham)?)\b',
              'UPMC': r'\b(?:upmc|pittsburgh|promote)\b'}
ROOT = '/n/data1/hsph/biostat/celehs/lab/bef299'
DOCUMENTS = (
    ('ms_preprocessing', 'Preprocessing README', 'preprocessing.md', 'Pipeline decisions and how to reproduce the outputs.'),
    ('ms_dictionary', 'Output data dictionary', 'output_data_dictionary.md', 'Columns, types, and row definitions for the preprocessed files.'),
    ('ms_raw', 'Raw source inventory', 'raw_sources.md', 'Input files and the provenance of their reported counts.'),
    ('ms_comparison', 'MGB and UPMC comparison', 'site_comparison.md', 'Differences in time, counts, code mappings, and registry labels.'),
    ('ms_mapping', 'Code-mapping README', 'code_mapping.md', 'Disease-modifying therapy (DMT) mapping, shared dictionary, and overrides.'),
    ('ms_report', 'Cohort report', 'cohort_report.html', 'Cohort selection, coverage, registry labels, and feature overlap.'),
)
REPO_PATHS = {
    'ms_preprocessing': 'preprocessing/{site}/README.md',
    'ms_dictionary': 'preprocessing/{site}/output_data_dictionary.md',
    'ms_raw': 'docs/data_summary_{site}.md',
    'ms_comparison': 'docs/UPMC_vs_MGB.md',
    'ms_mapping': 'data/README.md',
}
CORE_FILES = (
    ('all_ehr_absolute_date.parquet', 'Daily codified EHR', 'daily', 'codified', 'EHR features by patient, date, source code and mapped feature.'),
    ('all_ehr_calendar_month_aggregation.parquet', 'Monthly codified EHR', 'monthly', 'codified', 'One row per patient, calendar month and rolled-up feature.'),
    ('all_nlp_calendar_month_aggregation.parquet', 'Monthly NLP concepts', 'monthly', 'nlp', 'One row per patient, month label and NLP concept.'),
    ('df_registry_monthly_labels.parquet', 'Monthly registry labels', 'monthly', 'registry', 'One row for each patient and month with a registry observation.'),
    ('df_patient_demographics.parquet', 'Patient demographics', None, 'demographics', 'One row per patient in the documented demographics output.'),
    ('list_all_patients.csv', 'Patient inventory and cohort flags', None, 'cohort', 'One row per patient in the site inventory, with availability and cohort flags.'),
    ('ehr_code_dictionary.csv', 'Codified EHR code dictionary', None, 'mapping', 'Local codes, mapped features, descriptions, and usage counts.'),
    ('source_files.tsv', 'Pipeline input manifest', None, 'provenance', 'Input paths, file counts, sizes, and modification times by pipeline step.'),
)
UPMC_LAB_SECTION = '13.1 Lab values, units and reference ranges'
UPMC_LAB_FOLDER = '/n/data1/hsph/biostat/celehs/lab/SHARE/UPMC/MS/data_raw/data_codified'
UPMC_LAB_SHARDS = [f'ms_obs_fact_{end}_012023.csv' for end in (5000, 10000, 15000, 20000)]
UPMC_LAB_FIELDS = (
    ('patient_num', 'Patient identifier', 'Identifier'),
    ('concept_cd', 'Lab concept code, including LOINC and local codes', 'Text'),
    ('start_date', 'Test date in YYYY-MM-DD format', 'Date'),
    ('Field 4', 'Empty in the rows described in the source inventory', 'Empty in inspected rows'),
    ('Test name', 'Name of the laboratory test', 'Text'),
    ('Result value', 'Reported result, which can be numeric, bounded, or qualitative', 'Text'),
    ('Unit', 'Reported measurement unit, when present', 'Text'),
    ('Reference low', 'Lower reference value, when present', 'Text'),
    ('Reference high', 'Upper reference value, when present', 'Text'),
)


def ms_ids(query, records):
    if not re.search(MS_QUERY, query, re.I):
        return []
    named = [site for site in SITES if re.search(SITE_QUERY[site], query, re.I)]
    return [site + '_MS' for site in (named or SITES) if site + '_MS' in records]


def _text(node):
    return ' '.join(node.text_content().split())


def _report_metrics(section):
    return {_text(box.find("div[@class='stat-l']")): _text(box.find("div[@class='stat-v']"))
            for box in section.xpath('./div[@class="stats"]/*')}


def _report(path, site):
    tree = html.fromstring(path.read_text(encoding='utf-8-sig'))
    title = tree.xpath('//h1')[0]
    if site + ' MS cohort' not in _text(title):
        raise ValueError(f'Unexpected cohort report for {site}')
    generated = re.search(r'generated (\d{4}-\d{2}-\d{2} \d{2}:\d{2})', _text(title.getparent()))[1]
    sections = {_text(h): h.getparent() for h in tree.xpath('//section/h2')}
    cohort = sections['Cohort']
    rows = cohort.xpath('.//table')[0].xpath('.//tr[td]')
    pairs = [[_text(cell) for cell in row.xpath('./td')] for row in rows]
    stages = {label: int(value) for label, value in pairs if label and value.isdigit()}
    first_stage = next(iter(stages))
    filtered_stage = next(label for label in stages if label.startswith('REPORT COHORT'))
    registry_stage = "is_registry == 1 and registry_dx_group in ['ms']"
    stats = {'generated': generated, 'inventory': stages[first_stage], 'cohort': stages[filtered_stage],
             'registry_ms': stages[registry_stage], 'inventory_label': first_stage,
             'labels': _report_metrics(sections['Registry labels'])}
    modality = _report_metrics(cohort)
    ehr = _report_metrics(sections['Codified EHR feature space'])
    nlp = _report_metrics(sections['NLP feature space (CUIs)'])
    history = _report_metrics(sections['History length, density and follow-up'])
    demographics = _report_metrics(sections['Demographics'])
    age_label = 'median age at diagnosis' if site == 'MGB' else 'median age at first codified record'
    scale = 'EDSS' if site == 'MGB' else 'PDDS'
    stats['profile'] = {
        'Patients with codified EHR': modality['with codified EHR'],
        'Patients with NLP': modality['with NLP'],
        'Distinct codified feature codes': ehr['distinct codes'],
        'Distinct NLP concepts': nlp['distinct CUIs'],
        'Median EHR history span': history['EHR: median span'],
        'Median active EHR months': history['EHR: median active months'],
        'Median NLP history span': history['NLP: median span'],
        'Median active NLP months': history['NLP: median active months'],
        age_label.capitalize(): demographics[age_label],
        f'Patients with {scale}': stats['labels'][f'patients with {scale}'],
        f'Months with {scale}': stats['labels'][f'months with {scale}'],
    }
    overlap = sections['Do labels and features overlap in time?']
    if site == 'UPMC':
        grid = [[_text(cell) for cell in row.xpath('./td')] for row in overlap.xpath('.//tr')]
        stats['progression'] = {f'{row[0]}:{row[1]}': [int(row[2]), int(row[3])] for row in grid if len(row) == 4}
        patients, changed = stats['progression']['2:0']
        year_patients, year_changed = stats['progression']['2:12']
        nlp_window = next((_text(p) for p in overlap.xpath('./p') if 'NLP window instead' in _text(p)), '')
        stats['overlap'] = (f'{patients:,} patients had at least two PDDS months within their codified EHR window, '
                            f'and {changed:,} of those had a score change. Requiring those months to be at least '
                            f'12 months apart gives {year_patients:,} patients, including {year_changed:,} with a score change. '
                            + nlp_window).strip()
    else:
        metrics = _report_metrics(overlap)
        stats['overlap'] = (f"Of {metrics['patients with EDSS + EHR']} patients with EDSS and EHR, "
                            f"{metrics['with overlapping windows']} had overlapping windows. "
                            f"Median overlap was {metrics['median overlap'].removesuffix(' y')} years, with "
                            f"a median of {metrics['median EHR lead-in before first EDSS'].removesuffix(' y')} years of EHR before the first EDSS.")
    inventory_scope = ' with EHR or NLP data' if site == 'MGB' else ''
    counts = (f"{stats['inventory']:,} patients{inventory_scope} in the source inventory and "
              f"{stats['cohort']:,} patients in the filtered cohort report. "
              f"{stats['registry_ms']:,} are registry patients in the MS diagnosis group.")
    stats['counts'] = counts
    summary = (f'# {site} MS cohort report\n\nReport generated {generated}.\n\n{counts}\n\n'
               'The report selects `ms_spec_90 == 1` or registry enrollment, then restricts registry patients to '
               'the MS diagnosis group. The preprocessing outputs retain the broader inventory.\n\n'
               f'## Label and feature overlap\n\n{stats["overlap"]}\n\n'
               '## Report sections\n\n' + '\n'.join('- ' + heading for heading in sections))
    return stats, summary


def report_profile(stats):
    return ('These figures describe the filtered report cohort.\n\n| Measure | Value |\n| --- | --- |\n' +
            '\n'.join(f'| {label} | {value} |' for label, value in stats['profile'].items()))


def _columns(dictionary, filename):
    block = section(dictionary, f'`{filename}`')
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if not re.match(r'^\|\s*Column\s*\|', line, re.I):
            continue
        rows = []
        for row in lines[i + 2:]:
            if not row.startswith('|'):
                break
            raw_cells = re.split(r'(?<!\\)\|', row.strip()[1:-1])
            cells = [clean(re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', c)).replace(r'\|', '|') for c in raw_cells]
            names = re.findall(r'`([^`]+)`', raw_cells[0])
            rows.extend({'Column': name, 'Type': cells[1], 'Meaning': cells[-1]} for name in names)
        if rows:
            return rows
    raise ValueError(f'Missing column definitions for {filename}')


def load_ms(directory, site, public=False):
    """Read only the staged documentation. Data paths are stored as text."""
    identifier = site + '_MS'
    label = site + ' MS'
    location = f'{ROOT}/preprocessed_{site}'
    record = {'dataset_id': identifier, 'dataset_name': site + ' multiple sclerosis', 'label': label, 'site': site,
              'description': f'Multiple sclerosis at {site}: daily and monthly coded EHR, monthly concepts from notes, demographics, registry outcomes and cohort flags.',
              'storage_platform': ['O2'], 'storage_location': location, 'has_o2_copy': True,
              'contact': '', 'readme_curator': 'Benet', 'documentation_only': True,
              'files': [], 'resources': [], 'documented_files': [], 'dictionaries': [], 'column_descriptions': []}
    record['original_readmes'] = [dict(kind=kind, label=title, file=name, description=description)
                                  for kind, title, name, description in DOCUMENTS]
    snapshot = json.loads((directory / f'{site}.json').read_text(encoding='utf-8')) if public else None
    if public:
        if snapshot['site'] != site:
            raise ValueError(f'Mismatched public MS documentation for {site}')
        record['public_summary'] = True
        for doc in record['original_readmes']:
            doc['file'] = None
            if doc['kind'] != 'ms_dictionary':
                doc['label'] += ' summary'
    record['original_documents'] = [{**doc, 'url': f'/api/datasets/{identifier}/readme/{doc["kind"]}'}
                                    for doc in record['original_readmes']]
    if public:
        docs, stats = snapshot['docs'], snapshot['report_stats']
    else:
        for doc in record['original_documents']:
            if doc['kind'] in REPO_PATHS:
                doc['repository_path'] = REPO_PATHS[doc['kind']].format(site=site)
        docs = {kind: (directory / name).read_text(encoding='utf-8-sig') for kind, _, name, _ in DOCUMENTS if kind != 'ms_report'}
        stats, docs['ms_report'] = _report(directory / 'cohort_report.html', site)
        record['cohort_report_url'] = f'/api/datasets/{identifier}/cohort-report'
    record['report_stats'] = stats
    dictionary = docs['ms_dictionary']
    files = list(CORE_FILES)
    if site == 'UPMC':
        files.append(('nlp_code_dictionary.csv', 'NLP concept dictionary', None, 'mapping', 'Concept IDs, labels, and usage counts.'))
    for filename, name, level, kind, description in files:
        if public:
            columns = snapshot['columns'][filename]
        elif filename == 'source_files.tsv':
            columns = [{'Column': key, 'Meaning': value, 'Type': typ} for key, typ, value in (
                ('step', 'str', 'Pipeline step'), ('input', 'str', 'Input label'), ('path', 'str', 'Source path or pattern'),
                ('n_files', 'int', 'Number of matching files'), ('size_bytes', 'int', 'Total file size'),
                ('mtime', 'str', 'Latest input modification time'))]
        else:
            columns = _columns(dictionary, filename)
        if not public and site == 'UPMC' and kind == 'nlp':
            for col in columns:
                if col['Column'] == 'count':
                    col['Meaning'] = ('Number of days in the calendar month with an asserted mention of this concept for the patient. '
                                      'The extract has one source row per patient, day and concept, so count equals n_days.')
        if not public and site == 'UPMC' and kind == 'registry':
            for col in columns:
                if col['Column'] == 'pdds':
                    col['Meaning'] = 'Patient-Determined Disease Steps (0–8), summarized by the median within the month.'
                elif col['Column'] == 'pdds_max':
                    col['Meaning'] = 'Patient-Determined Disease Steps (0–8), summarized by the maximum within the month.'
        if kind == 'nlp':
            description += (' The count measures days with a mention in a 30.4375-day source window labeled with a calendar month.'
                            if site == 'MGB' else ' The count measures distinct days with an asserted mention in the calendar month.')
        elif kind == 'registry':
            description += (' The main disability outcome is EDSS (Expanded Disability Status Scale).'
                            if site == 'MGB' else ' The main disability outcome is PDDS (Patient-Determined Disease Steps) from PROMOTE.')
        path = location + '/' + filename
        card = {'id': filename, 'name': name, 'file': None, 'source_files': [filename], 'location': path,
                'description': description, 'columns': [c['Column'] for c in columns], 'column_descriptions': columns,
                'dictionaries': [], 'readme_kind': 'ms_dictionary', 'preview_available': False, 'level': level, 'data_kind': kind}
        record['documented_files'].append(card)
        record['resources'].append(dict(name=name, kind=kind, location=path, description=description, source_kind='ms_dictionary'))
        record['column_descriptions'].extend({**col, 'File': filename} for col in columns)
    if site == 'UPMC':
        lab_columns = [{'Column': name, 'Meaning': meaning, 'Type': data_type}
                       for name, meaning, data_type in UPMC_LAB_FIELDS]
        lab_file = {
            'id': 'upmc_ms_raw_labs', 'name': 'Raw lab results', 'file': None,
            'source_files': UPMC_LAB_SHARDS, 'location': UPMC_LAB_FOLDER,
            'description': 'Four headerless raw codified CSVs contain lab results, units and lower and upper reference values.',
            'columns': [column['Column'] for column in lab_columns], 'column_descriptions': lab_columns,
            'dictionaries': [], 'readme_kind': 'ms_raw', 'preview_available': False, 'level': 'raw', 'data_kind': 'lab',
            'source': source(record, 'ms_raw', UPMC_LAB_SECTION),
        }
        record['documented_files'].append(lab_file)
        record['resources'].append(dict(name=lab_file['name'], kind='lab', location=UPMC_LAB_FOLDER,
                                        description=lab_file['description'], source_kind='ms_raw'))
        record['column_descriptions'].extend({**column, 'File': 'ms_obs_fact_*_012023.csv'} for column in lab_columns)
        if public:
            schema_rows = '\n'.join(f'| {i} | {name} | {meaning} |'
                                    for i, (name, meaning, _) in enumerate(UPMC_LAB_FIELDS, start=1))
            docs['ms_raw'] += (f'\n\n## {UPMC_LAB_SECTION}\n\nThe four headerless CSVs are on O2 in '
                               f'`{UPMC_LAB_FOLDER}`.\n\n' + '\n'.join(f'- `{filename}`' for filename in UPMC_LAB_SHARDS) +
                               '\n\n| Position | Field | Meaning |\n| --- | --- | --- |\n' + schema_rows +
                               '\n\nThe raw result field can contain numeric, bounded or qualitative text. '
                               'Units and reference limits may be blank. The source inventory did not measure how many rows carry a result. '
                               'Processed codified tables carry test occurrences.')
    for filename, description in (
        ('dmt_mapping.csv', 'Disease-modifying therapy vocabulary and mapped feature IDs for both sites.'),
        ('code_mapping_overrides.csv', 'Shared corrections applied to the rollup dictionary before resolving codes.'),
        ('dictionary_mapping_v3.4.tsv', 'Shared rollup dictionary for mapping source codes to feature IDs.'),
        *((('registry_treatment_map_MGB.csv', 'MGB registry treatment names mapped to RxNorm and the therapy sheet.'),) if site == 'MGB' else ()),
    ):
        record['dictionaries'].append(dict(name=filename, description=description, location=f'{ROOT}/ms-thesis/data/{filename}'))
    record['schema'] = {card['id']: card['column_descriptions'] for card in record['documented_files']}
    facts = [fact(record, 'overview', 'overview', record['description'], 'ms_preprocessing'),
             fact(record, 'location', 'location', f'O2 output folder: {location}', 'ms_preprocessing'),
             fact(record, 'report_counts', 'statistics', f'Report generated {stats["generated"].split()[0]}. {stats["counts"]}', 'ms_report', 'Cohort'),
             fact(record, 'overlap', 'statistics', stats['overlap'], 'ms_report', 'Do labels and features overlap in time?')]
    return record, docs, facts


def ms_answer(catalog, query, previous=None):
    """Answer common MS discovery questions from the named site documentation."""
    from .presentation import file_views

    if not any(key.endswith('_MS') for key in catalog.records):
        return None
    q = query.lower()
    if re.search(r'\b(?:ibd|alzheimer|dementia|rheumatoid|ad)\b', q):
        return None
    explicit = re.search(MS_QUERY, q)
    lab_question = is_lab_query(query)
    processed_labs = lab_question and re.search(r'\b(?:monthly|daily|processed)\b', q) and not re.search(r'\braw\b', q)
    ids = ms_ids(q, catalog.records)
    named_sites = [site for site in SITES if re.search(SITE_QUERY[site], q)]
    if not ids and named_sites == ['UPMC'] and 'UPMC_MS' in catalog.records and re.search(r'\bregistry\b', q):
        ids = ['UPMC_MS']
    active = [key for key in previous or [] if key.endswith('_MS') and key in catalog.records]
    if len(active) != len(previous or []):
        active = []
    if not ids and not active and not re.search(r'\b(?:edss|pdds)\b', q):
        return None
    if not ids:
        if not explicit and not lab_question and not re.search(r'cohort|registry|edss|pdds|calendar|\bt0\b|overlap|\bdmt\b|'
                                           r'patient counts?|how many patients|what about|mapping|readme|reports?|statistics|'
                                           r'\bwhere\b|\bcolumns\b|\bmonths?\b|\baccess\b', q):
            return None
        ids = [site + '_MS' for site in named_sites if site + '_MS' in catalog.records] or active
        if not ids and re.search(r'\b(?:edss|pdds)\b', q):
            ids = [site + '_MS' for site in SITES if site + '_MS' in catalog.records]
    if not ids:
        return None
    sections, sources, actions = [], [], []
    intent = 'overview'
    if re.search(r'\b(?:va|kdi|vinci|bch|mimic)\b', q):
        intro = 'The documented MS sites here are MGB and UPMC.'
        return {'query': query, 'engine': 'catalog', 'model': None, 'intent': 'ms_scope',
                'interpretation': 'verified_ms_documentation', 'intro': intro, 'answer': intro, 'datasets': [],
                'sources': [], 'context_dataset_ids': [], 'pending_topic': None, 'warning': None,
                'compact': True, 'elapsed_seconds': 0, 'actions': [{'label': 'Browse MS datasets', 'query': 'What MS data do we have?'}]}
    overlap = re.search(r'overlap|progression|feature window|score chang|(?:two|2|three|3|five|5) (?:pdds|edss)|longitudinal.*label', q)
    count = re.search(r'how many|patient counts?|cohort size|number of patients', q)
    cohort = re.search(r'cohort filter|cohort flags|cohort selection|cohort (?:was )?selected|how.*select.*cohort|report cohort|ms_spec_9[05]', q)
    named_mappings = {d['name'] for key in ids for d in catalog.records[key]['dictionaries'] if d['name'].lower() in q}
    if lab_question:
        view, intent = 'labs', 'ms_labs'
        if processed_labs:
            intro = 'The requested processed MS files record lab test occurrences.'
        elif ids == ['UPMC_MS']:
            intro = 'Yes. UPMC MS has lab results in the raw codified files on O2.'
        elif ids == ['MGB_MS']:
            intro = 'The documented MGB MS extract has lab test codes and counts. Result values are absent.'
        else:
            intro = 'UPMC MS has raw lab results on O2. MGB MS provides lab test codes and counts.'
    elif overlap:
        view, intro = 'overlap', 'The cohort reports describe where registry labels and EHR or NLP feature windows overlap.'
    elif re.search(r'summary stat|cohort stat|report stat|cohort profile|cohort characteristics', q):
        view, intro = 'report', 'Here are the inventory counts and summary statistics for the filtered report cohorts.'
    elif count:
        view, intro = 'count', 'Here are the counts and their denominators in the supplied documentation.'
    elif cohort:
        view, intro = 'cohort', 'The reports apply a cohort filter to the broader preprocessing outputs.'
    elif named_mappings or re.search(r'code.mapping|code map|rollup|roll up|crosswalk|override|\bdmt\b|disease.modifying|rxnorm|loinc', q):
        view, intro = 'mapping', 'Here is how Benet documents the mappings used by the preprocessing pipelines.'
    elif re.search(r'raw|source inventory|input files?', q):
        view, intro = 'raw', 'The raw-source inventory for each site identifies which inputs the preprocessing reads.'
    elif re.search(r'report|characterization|coverage|date range', q):
        view, intro = 'report', 'The cohort documentation describes counts, coverage and registry labels.'
    elif re.search(r'\b(?:scripts?|pipeline|preprocessing code)\b', q):
        view, intro = 'preprocessing', 'Benet documents each preprocessing step and its inputs and outputs.'
    elif re.search(r'\bwhere\b|\bo2\b|storage|\bpaths?\b|\baccess\b|download', q):
        view, intro, intent = 'location', 'The documented MS outputs are on O2.', 'location'
    elif re.search(r'calendar|\bt0\b|negat|assertion|\btime\b.*nlp|dates?|\bcount_events\b', q) and not re.search(r'\bcolumns?\b|schema', q):
        view, intro = 'time', 'Check the source resolution and feature definitions before comparing the sites.'
    elif re.search(r'\b(?:join|link|linkage|connect|merge)\b', q):
        view, intro = 'linkage', 'Use the site-specific EHR identifier and calendar month to align the documented outputs.'
    elif re.search(r'\b(?:registry|edss|pdds|outcomes?|labels?|disability)\b', q) and not re.search(r'\bcolumns?\b|schema', q):
        view, intro = 'labels', 'Monthly registry labels are available for ' + ' and '.join(
            catalog.records[key]['label'] for key in ids) + '.'
    elif re.search(r'columns?|schema|fields|look like', q):
        view, intro, intent = 'files', 'Here are the documented files and their columns.', 'columns'
    elif re.search(r'sample|preview|fake rows', q):
        view, intro, intent = 'files', 'Use the column definitions and cohort reports to inspect the MS outputs.', 'columns'
    elif re.search(r'\b(?:monthly|daily|nlp|codified|registry|demographics)\b', q):
        view, intro = 'files', 'These are the relevant preprocessed MS files.'
    elif re.search(r'preprocess|pipeline|\bcode\b|scripts?', q):
        view, intro = 'preprocessing', 'Benet documents each preprocessing step and its inputs and outputs.'
    elif re.search(r'\b(?:readme|documentation)\b', q):
        view, intro = 'preprocessing', 'Open the preprocessing README and related documentation for each site.'
    else:
        view = 'overview'
        intro = ('Dataset Finder covers multiple sclerosis at MGB and UPMC.' if len(ids) == 2
                 else f'{catalog.records[ids[0]]["label"]} is documented in Dataset Finder.')

    for key in ids:
        record = catalog.records[key]
        site = record['site']
        docs = catalog.documents[key]
        stats = record['report_stats']
        facts, cards = [], []
        def add(text, kind, heading=None, markdown=False):
            facts.append(fact(record, 'ms_answer_' + str(len(facts)), view, text, kind, heading, markdown))

        def open_doc(kind):
            citation = source(record, kind)
            actions.append({'label': f'{site} {citation["label"].lower()}', 'document': {'dataset_id': key, 'kind': kind}})

        if view in {'overview', 'files', 'location', 'labels', 'cohort', 'linkage'}:
            scope = 'monthly registry' if view in {'labels', 'linkage'} else 'cohort flags' if view == 'cohort' else query
            cards = file_views(record, scope, intent)
            sources.extend(source(record, 'ms_dictionary', f'`{card["id"]}`') for card in cards)
        if view in {'overview', 'location'}:
            add(f'O2 output folder:\n{record["storage_location"]}', 'ms_preprocessing', 'Outputs' if site == 'MGB' else 'The pipeline')
        if view in {'overview', 'count', 'cohort', 'report', 'overlap'}:
            if view == 'count' and re.search(r'\b(?:rows?|events?|(?:patients? (?:with|have|who))|edss|pdds|nlp|codified)\b', q):
                outcome = next((name for name in ('EDSS', 'PDDS') if re.search(r'\b'+name.lower()+r'\b', q)), None)
                metric = f'patients with {outcome}'
                if outcome and metric in stats['labels'] and not re.search(r'\b(?:rows?|events?|months?|and|also|who|with both)\b', q):
                    add(f"{stats['labels'][metric]} {metric} in the filtered cohort report.", 'ms_report', 'Registry labels')
                else:
                    add('Use the relevant cohort report table for modality or outcome counts. The pipeline step reports describe exact output-file row counts.', 'ms_report')
            else:
                add(f'Report generated {stats["generated"].split()[0]}. {stats["counts"]}', 'ms_report', 'Cohort')
            if view in {'overview', 'cohort', 'report'}:
                add('Preprocessing retains the broader inventory. The report selects `ms_spec_90 == 1` or registry enrollment, '
                    'then restricts registry patients to the MS diagnosis group.', 'ms_report', 'Cohort')
            if view in {'overlap', 'report'}:
                if view == 'report':
                    add(report_profile(stats), 'ms_report', 'Filtered cohort summary statistics', markdown=True)
                span = re.search(r'\b(\d+) months? apart\b', q)
                minimum = re.search(r'\b(two|2|three|3|five|5) pdds months\b', q)
                if site == 'UPMC' and view == 'overlap' and (span or minimum) and not re.search(r'\bnlp\b', q):
                    n = {'two': '2', 'three': '3', 'five': '5'}.get(minimum[1], minimum[1]) if minimum else '2'
                    duration = span[1] if span else '0'
                    threshold = stats['progression'].get(f'{n}:{duration}')
                    text = (f'{threshold[0]:,} patients had at least {n} PDDS months within the codified EHR window' +
                            (f' at least {duration} months apart' if span else '') +
                            f'. Of those, {threshold[1]:,} had a score change.' if threshold else
                            'The report gives the progression grid for its listed PDDS-month and span thresholds.')
                    add(text, 'ms_report', 'Do labels and features overlap in time?')
                else:
                    add(stats['overlap'], 'ms_report', 'Do labels and features overlap in time?')
            if view == 'report' and re.search(r'coverage|date range', q):
                add(('The UPMC raw-source summary reports codified EHR from January 2004 to December 2022 and NLP from 2011 to 2021.'
                     if site == 'UPMC' else 'The MGB cohort report summarizes coverage over calendar time.'),
                    'ms_raw' if site == 'UPMC' else 'ms_report')
            open_doc('ms_report')
        if view == 'labels':
            add(('EDSS is the Expanded Disability Status Scale. MGB uses it as the primary disability measure and also documents PDDS.'
                 if site == 'MGB' else 'PDDS is Patient-Determined Disease Steps, the primary disability measure from the UPMC PROMOTE registry. EDSS has limited coverage there.'),
                'ms_comparison', 'The differences')
            open_doc('ms_report')
        if view == 'time':
            add(('MGB labels a 30.4375-day NLP source window with a reconstructed calendar month using corrected `t0`. '
                 'Mention days can fall in a neighboring calendar month. Its daily codified table carries actual calendar dates.'
                 if site == 'MGB' else 'UPMC NLP counts distinct days with an asserted concept in the actual calendar month. '
                 'Both feature sources have absolute dates, so no `t0` reconstruction is required.'), 'ms_comparison', 'Three traps in a two-site model')
            if re.search(r'count_events', q):
                add('In the daily codified table, `count` credits an event to each mapped concept. '
                    '`count_events` apportions the event across those concepts so the values can be summed for source-event totals.',
                    'ms_dictionary', '`all_ehr_absolute_date.parquet`')
            open_doc('ms_comparison')
        if view == 'labs':
            show_columns = bool(re.search(r'\b(?:columns?|fields?|schema|structure)\b', q))
            if site == 'UPMC' and not processed_labs:
                add('The four headerless CSVs include the test date and name, result, unit, and reference ranges. '
                    'The result field can contain numbers, bounded results such as `<20`, or text such as `Neg`. '
                    'Processed codified tables record test occurrences.', 'ms_raw', UPMC_LAB_SECTION, markdown=True)
                if re.search(r'how many|coverage|patient count|row count', q):
                    add('The source inventory lists four files totaling 2.73 GB. The number of rows with a result is unmeasured.',
                        'ms_raw', UPMC_LAB_SECTION)
                raw_lab = next(file for file in record['documented_files'] if file['data_kind'] == 'lab')
                cards = [{**raw_lab, 'show_columns': show_columns}]
                if not show_columns:
                    actions.append({'label': 'Show UPMC raw lab columns', 'query': 'Show the raw lab columns for UPMC MS'})
            else:
                description = ('MGB includes `LabTest` events in its coded EHR files. The documented extract contains codes and dates. '
                               'Numeric results, units and reference ranges are absent.' if site == 'MGB' else
                               'The daily and monthly codified EHR tables contain lab test codes and occurrence counts. '
                               'The raw codified files hold the result values, units and reference ranges.')
                add(description, 'ms_comparison', 'The differences', markdown=True)
                cadence = 'daily' if 'daily' in q and 'monthly' not in q else 'monthly' if 'monthly' in q and 'daily' not in q else ''
                cards = file_views(record, cadence + ' codified', 'columns' if show_columns else 'location')
                if site == 'UPMC':
                    actions.append({'label': 'Find UPMC raw results', 'query': 'Where are the raw lab results for UPMC MS?'})
            sources.extend(card.get('source') or source(record, 'ms_dictionary', f'`{card["id"]}`') for card in cards)
        if view == 'linkage':
            add(('At MGB, `EHR_mapping.csv` connects registry `mapping_index` to EHR `patient_num`.' if site == 'MGB' else
                 'At UPMC, the PROMOTE bridge connects `id_participant` to EHR `patient_num`. '
                 '`has_ehr_link` indicates a mapped identifier. Check `has_ehr` and `has_nlp` for feature availability.') +
                ' Use `patient_num` and `calendar_month` to align site-specific monthly features and labels. Check the overlap before choosing a study cohort.',
                'ms_dictionary', '`df_registry_monthly_labels.parquet`')
            open_doc('ms_report')
        if view == 'mapping':
            add('`dmt_mapping.csv` documents the disease-modifying therapy vocabulary and feature IDs. '
                '`code_mapping_overrides.csv` applies shared corrections to `dictionary_mapping_v3.4.tsv` before the site rollup.' +
                (' `registry_treatment_map_MGB.csv` maps MGB registry drug names to RxNorm and the therapy sheet.' if site == 'MGB' else ''),
                'ms_mapping')
            for mapping in record['dictionaries']:
                if not named_mappings or mapping['name'] in named_mappings:
                    add(f'{mapping["name"]}\nSource location: {mapping["location"]}', 'ms_mapping')
            if re.search(r'plegridy', q):
                add(section(docs['ms_mapping'], 'Known gap: Plegridy at MGB'), 'ms_mapping', 'Known gap: Plegridy at MGB')
            open_doc('ms_mapping')
        if view == 'raw':
            add(('MGB uses unrolled codified RData, monthly NLP RData, and registry and demographics CSVs.' if site == 'MGB' else
                 'UPMC uses codified event, raw ICD and procedure extracts, daily NLP, demographics and PROMOTE registry tables.'), 'ms_raw')
            open_doc('ms_raw')
        if view == 'preprocessing':
            add('The README identifies pipeline entry points, configuration, and the steps that create the EHR, NLP and registry outputs. '
                f'The O2 project module is at `{ROOT}/ms-thesis/preprocessing/{site}/`.', 'ms_preprocessing')
            open_doc('ms_preprocessing')
        sources.extend(item['source'] for item in facts)
        sections.append({'dataset': catalog.summary(record), 'facts': facts, 'files': cards, 'dictionaries': [],
                         'offer_preview': False, 'additional_note': None, 'date_summary': None})
    if view == 'overview' and len(ids) == 2:
        actions.insert(0, {'label': 'Compare MGB and UPMC', 'query': 'Compare MGB MS and UPMC MS'})
    if view == 'labels':
        actions.insert(0, {'label': 'Link registry labels to EHR',
                           'query': 'How do I link registry labels to EHR for ' +
                                    ' and '.join(catalog.records[key]['label'] for key in ids) + '?'})
    answer = [intro, *(f['text'] for s in sections for f in s['facts'])]
    if intent in {'columns', 'ms_labs'}:
        for dataset_section in sections:
            for card in dataset_section['files']:
                if card.get('show_columns'):
                    answer.append(card['name'] + ': ' + ', '.join(card['columns']))
                if intent == 'ms_labs':
                    answer.append(card['name'] + ' on O2: ' + card['location'])
                    if card['data_kind'] == 'lab':
                        answer.append(', '.join(card['source_files']))
    return {'query': query, 'engine': 'catalog', 'model': None, 'intent': intent,
            'interpretation': 'verified_ms_documentation', 'intro': intro,
            'answer': '\n\n'.join(answer),
            'datasets': sections, 'sources': list({(s['url'], s.get('heading')): s for s in sources}.values()),
            'context_dataset_ids': ids, 'pending_topic': None, 'warning': None,
            'compact': False, 'elapsed_seconds': 0, 'actions': actions}
