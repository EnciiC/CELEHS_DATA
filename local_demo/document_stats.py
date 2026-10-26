"""Read reported date tables from the original documentation, not patient files."""

import re
import xml.etree.ElementTree as ET
import zipfile

METRICS = ['Minimum', '25th percentile', 'Median', '75th percentile', 'Maximum']


def ibd_date_summaries(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    tables = []
    for table in root.findall('.//w:body/w:tbl', ns):
        rows = []
        for row in table.findall('w:tr', ns):
            cells = []
            for cell in row.findall('w:tc', ns):
                text = ''.join(t.text or '' for t in cell.findall('.//w:t', ns)).strip()
                span = cell.find('w:tcPr/w:gridSpan', ns)
                count = int(span.get('{'+ns['w']+'}val', '1')) if span is not None else 1
                cells.extend([text] * count)
            rows.append(cells)
        tables.append(rows)
    # These are the three tables in Sara's IBD document. Validate labels and
    # shapes instead of interpreting arbitrary tables as date distributions.
    definitions = [
        (0, 'Raw codified', ['RPDR diagnosis','RPDR medication','RPDR lab','RPDR procedure','IBD_2020 codified'], 1),
        (1, 'Processed codified (merged daily data)', ['Processed codified'], 0),
        (2, 'Processed NLP', ['IBD_2020 NLP','IBD_2019_MART NLP','IBD_2019_2025_MART NLP','Processed NLP (Total)'], 0),
    ]
    result = []
    for index, level, names, _ in definitions:
        if index >= len(tables): continue
        values = {}
        for row in tables[index]:
            label = row[0].lower() if row else ''
            key = 'Minimum' if label in {'min date','minimum date'} else 'Maximum' if label in {'max date','maximum date'} else '25th percentile' if label == '25% date' else '75th percentile' if label == '75% date' else 'Median' if label == 'median date' else None
            if key:
                if len(row) != len(names) + 1 or any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v) for v in row[1:]):
                    raise ValueError('Unexpected IBD date table layout')
                values[key] = row[1:]
        if set(values) != set(METRICS): raise ValueError('Incomplete IBD date summary')
        for col, name in enumerate(names):
            result.append({'name':name, 'level':level, 'table':index + 1,
                           'default':index == 1 or index == 2 and col == 3,
                           'dates':{metric:values[metric][col] for metric in METRICS}})
    return result


def date_view(record, query):
    summaries = record.get('date_summaries', [])
    q = query.lower()
    if 'raw' in q or 'rpdr' in q:
        selected = [s for s in summaries if s['level'] == 'Raw codified']
    elif 'by source' in q or 'breakdown' in q:
        selected = [s for s in summaries if s['level'] == 'Processed NLP' and not s['default']]
    else:
        selected = [s for s in summaries if s['default']]
    if 'nlp' in q and 'codified' not in q: selected = [s for s in selected if 'NLP' in s['name']]
    if 'codified' in q and 'nlp' not in q: selected = [s for s in selected if 'NLP' not in s['name']]
    if not selected: return None
    return {'columns':['Statistic', *(s['name'] for s in selected)],
            'rows':[{'Statistic':metric, **{s['name']:s['dates'][metric] for s in selected}} for metric in METRICS],
            'note':'Reported in the original README for processed codified (merged daily) and processed NLP data.' if all(s['default'] for s in selected) else 'Reported in the original README for the source groups shown.',
            'warning':'Reported minimum/maximum dates include implausible values. These are not a verified clean date range. The README does not separately establish monthly-file coverage or specify the unit used for the percentiles.'}
