"""Brief, source-based notes; detailed generation instructions remain separate."""


def short_notes(record, requested=None):
    files = [f for f in record['files'] if not requested or f['file'] in requested]
    lines = [f"# {record['label']}", '',
             'A short guide to the file structure. The original README remains the source documentation.', '',
             '**Storage:** ' + ', '.join(record['storage_platform']) + ('. There is no O2 copy.' if record.get('has_o2_copy') is False else ''), '',
             '**Contact:** ' + record['contact'], '']
    for file in files:
        resource = next((r for r in record['resources'] if r.get('location') == file.get('source_path')), None)
        name = resource['name'] if resource else file['file'].replace('_fake_data.csv', '').replace('_', ' ')
        lines.extend(['## ' + name, '', file['row_meaning'], '',
                      '**Columns:** ' + ', '.join('`' + col + '`' for col in file['columns']), ''])
    lines.append('**Sample rows:** Generated fake data, showing structure only. They are not real patient records or measured patient statistics.')
    return '\n'.join(lines)


def fake_data_notes(record):
    """Short public generation notes; internal review notes stay on disk."""
    assumptions = record.get('assumptions', {})
    lines = [f"# {record['label']}: How the fake data were made", '',
             'These files were generated locally from the supplied column structure. No real patient rows were copied.', '',
             '## Files', '']
    lines.extend(f"- `{file['file']}`: {file['rows']:,} generated rows." for file in record['files'])
    patients = assumptions.get('synthetic_patients')
    lines.extend(['', '## Generation', ''])
    if patients:
        lines.append(f'- The files share {patients:,} generated patient IDs. These are not real patient identifiers.')
    lines.append('- Column names and order match the supplied structures. Dates and code-format examples are generated.')
    counts = assumptions.get('monthly_count_range', assumptions.get('count_range'))
    if counts:
        lines.append(f'- Monthly counts are generated integers from {counts[0]} to {counts[1]}.')
    lines.extend(['- Files were generated independently. Monthly counts are not calculated from the fake daily or raw files.',
                  '', '**Use:** File-format and software testing only. These examples do not represent real clinical distributions or validated code meanings.'])
    return '\n'.join(lines)
