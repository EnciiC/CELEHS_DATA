"""Read an allowlisted metadata subset of the tracker without changing it."""

from pathlib import Path, PurePosixPath
import json
import xml.etree.ElementTree as ET
import zipfile

TRACKER = 'outputs/resource_catalog_20261002/CELEHS_Resource_Catalog.xlsx'
MAPPING = {'DATA-001':('MGB_AD', "MGB Alzheimer's disease data"),
           'DATA-002':('UPMC_AD', "UPMC Alzheimer's disease data"),
           'DATA-004':('IBD', 'IBD Project Data')}
FIELDS = {'Dataset name','Dataset type','Disease / topic','Storage platform','Main folder','Contact',
          'Data type','Raw and processed files','Processing scripts','Patient count','Date range','Access level','Related paper'}


def load_tracker(project):
    path = Path(project) / TRACKER
    if not path.exists():
        snapshot = Path(project) / 'demo_input' / 'tracker_public.json'
        if not snapshot.exists(): return {}
        result = json.loads(snapshot.read_text(encoding='utf-8'))
        if set(result) - set(dataset_id for dataset_id, _ in MAPPING.values()):
            raise ValueError('Unexpected dataset in public tracker snapshot')
        if any(field['name'] not in FIELDS for item in result.values() for field in item['fields']):
            raise ValueError('Unapproved field in public tracker snapshot')
        return result
    ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(t.text or '' for t in si.findall('.//s:t', ns)) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)]
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        sheet = next(s for s in workbook.findall('s:sheets/s:sheet', ns) if s.get('name') == 'Datasets')
        rid = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next(r.get('Target') for r in rels if r.get('Id') == rid)
        member = target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl') / target)
        rows = ET.fromstring(z.read(member)).findall('s:sheetData/s:row', ns)
        headers, result = {}, {}
        for row in rows:
            cells = {}
            for c in row.findall('s:c', ns):
                address = c.get('r'); column = ''.join(x for x in address if x.isalpha())
                value = c.find('s:v', ns)
                text = ''.join(t.text or '' for t in c.findall('.//s:t', ns)) if c.get('t') == 'inlineStr' else strings[int(value.text)] if c.get('t') == 's' and value is not None else value.text if value is not None else ''
                cells[column] = (address, text)
            if cells.get('A', ('',''))[1] == 'Dataset ID':
                headers = {column:value[1] for column,value in cells.items()}; continue
            identity = cells.get('A', ('',''))[1]
            if identity not in MAPPING: continue
            dataset_id, expected_name = MAPPING[identity]
            if cells.get('B', ('',''))[1] != expected_name: raise ValueError('Tracker dataset ID/name mismatch')
            result[dataset_id] = {'workbook':path.name, 'sheet':'Datasets','row':int(row.get('r')), 'tracker_id':identity,
                'fields':[{'name':headers[col],'value':value,'cell':address} for col,(address,value) in cells.items()
                          if headers.get(col) in FIELDS and value]}
        return result


def tracker_notes(source):
    lines = ['# Spreadsheet entry', '', f"Source: {source['workbook']}, {source['sheet']} row {source['row']} ({source['tracker_id']}).",
             '', 'This is a tracker summary. Specific README and file-schema details remain separate.', '']
    for field in source['fields']:
        lines.extend(['## ' + field['name'], '', field['value'], ''])
    return '\n'.join(lines)
