import asyncio
import csv
import io
import json
import re

import pytest
from fastapi.testclient import TestClient

from local_demo.app import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def ask(client, question):
    response = client.post('/api/chat', json={'query': question, 'use_llm': False})
    assert response.status_code == 200
    return response.json()


def test_ibd_location_and_dictionaries(client):
    result = ask(client, 'I wanted to see IBD data, guide me and let me know where I can find it')
    assert [s['dataset']['id'] for s in result['datasets']] == ['IBD']
    assert 'no O2 copy' in result['answer']
    files = result['datasets'][0]['files']
    assert any('codified_data_monthly.Rdata' in f['location'] for f in files)
    assert any('NLP_data_monthly.RData' in f['location'] for f in files)
    assert 'dictionary_mapping_v3.4.tsv' not in result['answer']
    monthly = [f for f in files if 'monthly' in f['name']]
    assert all('CONCEPT_CD' not in json.dumps(f['dictionaries']) for f in monthly)
    assert 'as confirmed by Enci' not in result['answer']


def test_ad_inventory_and_site_filter(client):
    result = ask(client, 'I wanted to see AD, what we have now')
    assert {s['dataset']['id'] for s in result['datasets']} == {'MGB_AD', 'UPMC_AD'}
    assert 'Raw and daily-level UPMC AD data are also available' in result['answer']
    mgb = next(s for s in result['datasets'] if s['dataset']['id'] == 'MGB_AD')
    assert any('/Monthly_Counts/MGB/Monthly_codified.RData' in f['location'] for f in mgb['files'])
    assert len(mgb['files']) == 2
    assert all(any(f['category'] == 'location' and f['text'] == 'Storage: O2' for f in s['facts']) for s in result['datasets'])
    nlp = next(f for f in mgb['files'] if 'NLP' in f['file'])
    assert nlp['location'] == '/n/data1/hsph/biostat/celehs/lab/SHARE/MGB/MS-AD/Sara/Monthly_Counts/MGB/NLP/'
    assert '1_1501' not in json.dumps(result['datasets'])
    assert not any('/MGB/Daily_codified.RData' in f['text'] for f in mgb['facts'])
    assert [s['dataset']['id'] for s in ask(client, 'UPMC AD columns')['datasets']] == ['UPMC_AD']


def test_microbiome_gap_and_unknown_dataset(client):
    result = ask(client, 'I want EHR data and gut microbiome measurements')
    assert 'Microbiome availability is not documented' in result['answer']
    assert 'does not contain microbiome' not in result['answer']
    assert not ask(client, 'Where is VINCI heart failure data?')['datasets']
    assert not ask(client, 'Where is UPMC IBD?')['datasets']


def test_scope_does_not_index_va_section(client):
    catalog = client.app.state.catalog
    for dataset_id in ['MGB_AD', 'UPMC_AD']:
        section = catalog.documents[dataset_id]['original_section']
        assert '/mnt/mvpfs/' not in section
        assert 'VA (KDI)' not in section


def test_schema_and_synthetic_preview_download(client):
    response = client.get('/api/datasets/UPMC_AD/files/Monthly_codified_fake_data.csv/preview?limit=50')
    assert response.status_code == 200
    data = response.json()
    assert data['synthetic'] is True and len(data['rows']) == 50
    assert data['columns'] == ['patient_num', 'month', 'year', 'feature_id', 'Group_Code_Count']
    assert all(len(r['month']) == 2 for r in data['rows'])
    download = client.get('/api/datasets/UPMC_AD/download/Monthly_codified_fake_data.csv')
    assert download.status_code == 200
    assert 'fake_data.csv' in download.headers['content-disposition']
    assert client.get('/api/datasets/UPMC_AD/download/Monthly_codified.RData').status_code == 404
    assert client.get('/api/datasets/UPMC_AD/files/column_dictionary.csv/preview').status_code == 404
    assert client.get('/api/datasets/UPMC_AD/files/Monthly_codified_fake_data.csv/preview?limit=1000').status_code == 422
    with pytest.raises(ValueError):
        client.app.state.catalog.downloadable('UPMC_AD', '../README.md')


def test_readmes_and_empty_question(client):
    original = client.get('/api/datasets/UPMC_AD/readme/original').json()
    assert 'UPMC' in original['text'] and 'scope_note' in original
    assert '<table' in original['html'] and '<p' in original['html']
    assert '<script' not in original['html']
    assert client.post('/api/chat', json={'query': '   '}).status_code == 422
    assert client.post('/api/catalog/reload', headers={'Origin': 'https://example.org'}).status_code == 403


def test_original_retrieval_and_fake_patient_counts(client):
    result = ask(client, 'Where can I find MGB AD APOE genetic data?')
    assert 'APOE_SNPs.csv' in result['answer']
    assert any(f['source']['kind'] == 'original' for s in result['datasets'] for f in s['facts'])
    result = ask(client, 'How many patients are in the UPMC AD fake data?')
    assert '200 generated patients' in result['answer']
    assert '1,000 generated rows' in result['answer']
    assert 'Patient count for these source files: Not documented' not in result['answer']


def test_model_failure_is_honest_and_source_based(client, monkeypatch):
    async def broken(*args, **kwargs):
        raise ValueError('invalid evidence')
    agent = client.app.state.agent
    monkeypatch.setattr(agent, 'select', broken)
    monkeypatch.setattr(agent, 'interpret', broken)
    result = asyncio.run(agent.answer('Show IBD'))
    assert result['engine'] == 'catalog'
    assert result['warning']
    assert result['datasets'][0]['files'][0]['dictionaries']
    assert 'dictionary_mapping_v3.4.tsv' not in result['answer']


def test_monthly_structure_is_short_and_optional_details_are_scoped(client):
    result = ask(client, 'Can you show me what a IBD monthly count data look like')
    assert result['intent'] == 'columns'
    section = result['datasets'][0]
    assert section['facts'] == []
    assert [f['name'] for f in section['files']] == ['IBD monthly codified counts', 'IBD monthly NLP counts']
    assert section['files'][0]['columns'] == ['EMPI','Patient_num','month','year','Rollup_Code','N']
    assert section['files'][1]['columns'] == ['EMPI','month','year','CUI','N','Patient_num']
    assert len(result['answer']) < 400
    assert 'Storage:' not in result['answer'] and 'Raw codified' not in result['answer']
    assert 'CONCEPT_CD' not in json.dumps(section)
    assert '/data/' not in result['answer'] and 'Source location' not in result['answer']
    assert section['offer_preview']


@pytest.mark.parametrize('question,expected', [
    ('IBD monthly NLP columns', ['NLP_data_monthly_fake_data.csv']),
    ('IBD raw columns', ['IBD_2020_codified_raw_fake_data.csv']),
    ('MGB AD daily columns', ['combined_daily_fake_data.csv','Daily_codified_fake_data.csv']),
    ('UPMC AD monthly codified columns', ['Monthly_codified_fake_data.csv']),
])
def test_file_scope(client, question, expected):
    result = ask(client, question)
    assert [f['file'] for s in result['datasets'] for f in s['files']] == expected


def test_dictionary_is_specific_and_followups_use_previous_dataset(client):
    result = ask(client, 'IBD monthly NLP dictionary')
    dictionaries = result['datasets'][0]['dictionaries']
    assert [d['name'] for d in dictionaries] == ['NLP dictionary']
    assert 'CONCEPT_CD' not in result['answer']
    result = client.post('/api/chat', json={'query':'Show sample rows for monthly NLP', 'previous_dataset_ids':['IBD'], 'use_llm':False}).json()
    assert result['intent'] == 'preview'
    assert len(result['datasets']) == 1
    assert result['datasets'][0]['files'][0]['show_preview']


def test_display_and_model_evidence_are_english(client):
    for dataset_id in ['IBD','MGB_AD','UPMC_AD']:
        for endpoint in ['', '/schema', '/readme/catalog', '/readme/original']:
            data = client.get('/api/datasets/' + dataset_id + endpoint).json()
            assert not re.search(r'[\u3400-\u9fff]', json.dumps(data, ensure_ascii=False))
        assert not re.search(r'[\u3400-\u9fff]', json.dumps(client.app.state.catalog.facts[dataset_id], ensure_ascii=False))


def test_original_readme_preserves_merged_table_headers(client):
    original = client.get('/api/datasets/IBD/readme/original').json()
    assert 'colspan="4" rowspan="1"><p>Merged RPDR files</p>' in original['html']
    assert 'colspan="1" rowspan="2"><p>IBD_2020</p>' in original['html']
    schema = client.get('/api/datasets/IBD/schema').json()
    meanings = [c['meaning'] for f in schema['files'] for c in f['columns'] if c['name'] == 'CUI']
    assert meanings == ['Concept identifier in NLP results.']


def test_short_notes_are_scoped_and_technical_details_are_separate(client):
    response = client.get('/api/datasets/MGB_AD/readme/notes?files=NLP_monthly_fake_data.csv,Monthly_codified_fake_data.csv')
    assert response.status_code == 200
    notes = response.json()['text']
    assert len(notes.split()) < 160
    assert '**Storage:** O2' in notes
    assert '`patientnum`' in notes and '`Group_Code`' in notes
    assert 'daily' not in notes.lower()
    assert 'seed' not in notes.lower() and 'probability' not in notes.lower()
    assert 'fake data' in notes and 'original README' in notes
    assert 'How the fake data were made' in client.get('/api/datasets/MGB_AD/readme/synthetic').json()['text']
    assert client.get('/api/datasets/MGB_AD/readme/notes?files=wrong.csv').status_code == 422


def test_mgb_nlp_location_is_folder_not_sample_file(client):
    result = ask(client, 'Where can I find MGB AD monthly NLP?')
    assert len(result['datasets'][0]['files']) == 1
    assert result['datasets'][0]['files'][0]['location'].endswith('/Monthly_Counts/MGB/NLP/')
    assert '1_1501.RData' not in json.dumps(result['datasets'])
    data = client.get('/api/datasets/MGB_AD').json()
    assert next(f for f in data['files'] if 'NLP' in f['file'])['source_path'].endswith('/NLP/')
    # Keep observed row-count provenance; never present one batch as the whole folder.
    assert data['source_file_dimensions'][0]['source_path'].endswith('/NLP/1_1501.RData')


@pytest.mark.parametrize('question', ['hi', 'Hello!', 'hey there', 'Good morning', 'How are you?'])
def test_greetings_are_friendly_and_do_not_call_the_model(client, monkeypatch, question):
    async def should_not_run(*args):
        raise AssertionError('A greeting does not need dataset evidence selection')
    monkeypatch.setattr(client.app.state.agent, 'select', should_not_run)
    result = client.post('/api/chat', json={'query':question}).json()
    assert result['engine'] == 'guide'
    assert result['intent'] == 'greeting'
    assert result['answer'].startswith('Hi!')
    assert 'could not find' not in result['answer']
    assert result['datasets'] == [] and len(result['actions']) == 3


def test_ra_response_offers_next_steps_without_substituting_other_cohorts(client):
    result = ask(client, 'I want to study rheumatoid arthritis using MGB data. What is available?')
    assert result['intent'] == 'unavailable'
    assert result['pending_topic'] == 'RA:MGB'
    assert 'rheumatoid arthritis (RA) from MGB' in result['answer']
    assert "can't verify" in result['answer'] and 'may exist elsewhere in the lab' in result['answer']
    assert not result['datasets'] and not result['context_dataset_ids']
    assert all('location' not in action for action in result['actions'])
    assert result['actions'][0]['label'] == 'What information should I collect?'
    assert 'instead' in result['actions'][1]['label']
    assert 'O2' not in result['answer'] and '/n/' not in result['answer']


def test_missing_topic_followup_does_not_silently_switch_to_available_data(client):
    result = client.post('/api/chat', json={'query':'What about monthly counts?', 'pending_topic':'RA:MGB', 'previous_dataset_ids':['MGB_AD'], 'use_llm':False}).json()
    assert result['pending_topic'] == 'RA:MGB' and not result['datasets']
    follow = client.post('/api/chat', json={'query':result['actions'][0]['query'], 'pending_topic':result['pending_topic'], 'use_llm':False}).json()
    assert follow['intent'] == 'documentation_help'
    assert 'README' in follow['answer'] and 'column names' in follow['answer']
    assert 'does not upload or add them automatically' in follow['answer']
    switch = client.post('/api/chat', json={'query':'Show MGB AD monthly columns', 'pending_topic':'RA:MGB', 'use_llm':False}).json()
    assert [s['dataset']['id'] for s in switch['datasets']] == ['MGB_AD']
    assert switch['pending_topic'] is None


def test_small_talk_preserves_existing_dataset_context(client):
    for message in ['hi', 'thanks', 'okay']:
        result = client.post('/api/chat', json={'query':message,'previous_dataset_ids':['IBD'],'use_llm':False}).json()
        assert result['context_dataset_ids'] == ['IBD']
        assert 'MGB IBD' in result['actions'][0]['query']
    result = client.post('/api/chat', json={'query':'hi','pending_topic':'RA:MGB','use_llm':False}).json()
    assert result['pending_topic'] == 'RA:MGB'
    result = client.post('/api/chat', json={'query':'hi','pending_topic':'invented:path','use_llm':False}).json()
    assert result['pending_topic'] is None


def test_help_clarification_and_greeting_with_real_question(client):
    result = ask(client, 'What can you do?')
    assert result['intent'] == 'help' and 'fake sample rows' in result['answer']
    result = ask(client, 'xyzzy')
    assert result['intent'] == 'clarification' and 'disease, site' in result['answer']
    assert not result['datasets']
    result = ask(client, 'Hi, where can I find IBD data?')
    assert [s['dataset']['id'] for s in result['datasets']] == ['IBD']
    assert len(ask(client, 'What do we have?')['datasets']) == 3


@pytest.mark.parametrize('question', [
    'Is IBD data available on O2?', 'Do we have IBD on O2?',
    'Does IBD have an O2 copy?', 'Is MGB IBD stored on O2?',
    'Can we find IBD data on O2', 'Can we find IBD data on O2? \\\n ',
    'Can I locate IBD data on O2?', 'Is there a copy of IBD data on O2?',
])
def test_ibd_o2_question_is_answered_directly(client, question):
    result = ask(client, question)
    assert result['intent'] == 'storage' and result['compact'] is True
    assert result['answer'] == 'No. MGB IBD is stored on MGB Windows/SFA and Eris, not O2.'
    assert len(result['answer'].split()) < 25
    assert len(result['datasets']) == 1 and result['datasets'][0]['files'] == []
    assert [f['category'] for f in result['datasets'][0]['facts']] == ['location']
    assert 'CONCEPT_CD' not in result['answer'] and 'Sara' not in result['answer']
    assert result['actions'][0]['label'] == 'Show file locations'
    assert result['sources']


def test_ad_o2_and_unknown_copy_are_not_confused(client):
    result = ask(client, 'Is AD data available on O2?')
    assert result['answer'] == 'Yes. MGB AD and UPMC AD are stored on O2.'
    result = ask(client, 'Is UPMC AD stored on Eris?')
    assert result['compact'] is True
    assert 'O2' in result['answer'] and 'A copy on Eris is not documented.' in result['answer']
    assert not result['answer'].startswith('No.')
    result = ask(client, 'Is IBD stored on Eris?')
    assert result['answer'] == 'Yes. MGB IBD is stored on Eris.'


@pytest.mark.parametrize('question, expected', [
    ('Can we find IBD data on O2', 'No. MGB IBD is stored on MGB Windows/SFA and Eris, not O2.'),
    ('Can we find AD data on O2?', 'Yes. MGB AD and UPMC AD are stored on O2.'),
    ('Can we find UPMC AD data on Eris?', 'The documentation lists O2 for UPMC AD. A copy on Eris is not documented.'),
])
def test_verified_storage_does_not_depend_on_model_interpretation(client, monkeypatch, question, expected):
    async def should_not_run(*args):
        raise AssertionError('Verified storage lookups do not need model inference')
    agent = client.app.state.agent
    monkeypatch.setattr(agent, 'interpret', should_not_run)
    monkeypatch.setattr(agent, 'select', should_not_run)
    result = client.post('/api/chat', json={'query':question}).json()
    assert result['answer'] == expected
    assert result['interpretation'] == 'verified_storage' and result['compact']
    assert result['engine'] == 'catalog' and result['model'] is None
    assert result['warning'] is None and result['sources']


@pytest.mark.parametrize('question', [
    'Can we find cardiovascular data on O2?',
    'Can we find IBD cardiovascular subgroup data on O2?',
    'Can we find UPMC IBD data on O2?',
])
def test_storage_lookup_cannot_assert_unknown_cohort_or_subgroup(client, monkeypatch, question):
    async def unknown(*args):
        return {'mode':'not_documented','dataset_ids':[],'intent':'storage','subject':'the requested cohort',
                'clarification':'Which cohort documentation would you like to add?',
                'short_answer':'','evidence_ids':[]}, {}
    monkeypatch.setattr(client.app.state.agent, 'interpret', unknown)
    result = client.post('/api/chat', json={'query':question}).json()
    assert result['datasets'] == [] and result['sources'] == []
    assert result['interpretation'] == 'not_documented'
    assert not result['answer'].startswith(('Yes.', 'No.'))


def test_storage_followup_uses_dataset_context_and_missing_topic(client):
    result = client.post('/api/chat', json={'query':'Is it on O2?', 'previous_dataset_ids':['IBD'], 'use_llm':False}).json()
    assert result['answer'].startswith('No. MGB IBD')
    result = client.post('/api/chat', json={'query':'On O2?', 'pending_topic':'RA:MGB', 'use_llm':False}).json()
    assert result['intent'] == 'unavailable' and not result['datasets']
    result = ask(client, 'Show MGB AD monthly columns on O2')
    assert result['intent'] == 'columns' and not result['compact']
    result = ask(client, 'Where can I find MGB AD daily data on O2?')
    assert result['intent'] == 'location' and not result['compact']
    assert result['datasets'][0]['files']


@pytest.mark.parametrize('question', [
    'do we have cardiovascular data?', 'Do we have oncology data?',
    'Do we have kidney disease data from MGB?', 'Do we have respiratory data from UPMC?',
])
def test_generic_data_word_does_not_mean_return_every_dataset(client, question):
    assert client.app.state.catalog.find(question) == []
    result = ask(client, question)
    assert result['datasets'] == []


def test_model_interprets_any_undocumented_subject_before_retrieval(client, monkeypatch):
    async def route(query, previous, pending):
        return {'mode':'not_documented','dataset_ids':[],'intent':'overview','subject':'cardiovascular data',
                'clarification':'Do you mean a dedicated cohort, or cardiovascular features in EHR data?',
                'short_answer':'','evidence_ids':[]}, {}
    async def no_selection(*args):
        raise AssertionError('Do not select evidence for a nonexistent match')
    monkeypatch.setattr(client.app.state.agent, 'interpret', route)
    monkeypatch.setattr(client.app.state.agent, 'select', no_selection)
    result = client.post('/api/chat', json={'query':'do we have cardiovascular data?'}).json()
    assert result['engine'] == 'local_llm' and result['interpretation'] == 'not_documented'
    assert result['pending_topic'] == 'query:cardiovascular data'
    assert not result['datasets'] and not result['sources']
    assert 'cardiovascular features' in result['answer'] and "can't confirm" in result['answer']
    thanks = client.post('/api/chat', json={'query':'thanks','pending_topic':result['pending_topic']}).json()
    assert thanks['pending_topic'] == 'query:cardiovascular data'


def test_semantic_schema_rejects_invented_evidence_and_numbers(client):
    from local_demo.semantic import routing_context, validate_route
    catalog = client.app.state.catalog
    context, evidence = routing_context(catalog, 'What is a monthly count?', [], None)
    route = {'mode':'explain','dataset_ids':[],'intent':'columns','subject':'monthly count',
             'clarification':'','short_answer':'N counts occurrences for a patient in a calendar month.',
             'evidence_ids':['IBD:resource_4']}
    assert validate_route(route, catalog.records, evidence)['dataset_ids'] == ['IBD']
    bad = {**route, 'short_answer':'There are 987654321 patients.'}
    with pytest.raises(ValueError): validate_route(bad, catalog.records, evidence)
    with pytest.raises(ValueError): validate_route({**route,'evidence_ids':['imaginary:fact']}, catalog.records, evidence)
    with pytest.raises(ValueError): validate_route({**route,'mode':'not_documented'}, catalog.records, evidence)
    assert any(f['category'] == 'columns' for f in context['evidence'])
    assert any(f['category'] == 'fake' and 'Synthetic example' in f['text'] for f in context['evidence'])


def test_general_pending_subject_is_not_lost_in_fallback(client):
    result = client.post('/api/chat', json={'query':'What about monthly counts?', 'pending_topic':'query:cardiovascular data','use_llm':False}).json()
    assert not result['datasets'] and result['pending_topic'] == 'query:cardiovascular data'
    follow = client.post('/api/chat', json={'query':'What information do you need to add cardiovascular data as a dataset?',
                                        'pending_topic':'query:cardiovascular data','use_llm':False}).json()
    assert follow['intent'] == 'documentation_help' and 'cardiovascular' in follow['answer']


def test_direct_source_fields_do_not_override_undocumented_subgroups(client):
    from local_demo.semantic import direct_document_request
    records = client.app.state.catalog.records
    assert direct_document_request('What is the patient count for AD?', records)
    assert direct_document_request('Can you show me what IBD monthly count data look like?', records)
    assert not direct_document_request('What is the cardiovascular subgroup patient count for IBD?', records)
    assert not direct_document_request('Do MGB AD patients have kidney function measurements?', records)


def test_wrong_monthly_row_grain_is_rejected(client):
    from local_demo.semantic import routing_context, validate_route
    catalog = client.app.state.catalog
    _, evidence = routing_context(catalog, 'What is a monthly count row?', [], None)
    route = {'mode':'explain','dataset_ids':['IBD'],'intent':'columns','subject':'monthly count row',
             'clarification':'','short_answer':'There is one row per patient per month.',
             'evidence_ids':['IBD:resource_4']}
    with pytest.raises(ValueError): validate_route(route, catalog.records, evidence)


def test_clarification_can_ask_about_o2_but_cannot_invent_a_patient_count(client):
    from local_demo.semantic import routing_context, validate_route
    catalog = client.app.state.catalog
    _, evidence = routing_context(catalog, 'Is diabetes data on O2?', [], None)
    route = {'mode':'not_documented','dataset_ids':[],'intent':'storage','subject':'diabetes data',
             'clarification':'Which diabetes cohort or data type do you mean on O2?',
             'short_answer':'','evidence_ids':[]}
    assert validate_route(route, catalog.records, evidence)['mode'] == 'not_documented'
    with pytest.raises(ValueError):
        validate_route({**route,'clarification':'Would you like our 500 patient cohort?'}, catalog.records, evidence)


def test_failed_interpretation_does_not_fall_back_to_unrelated_inventory(client, monkeypatch):
    async def broken(*args): raise ValueError('Invalid interpretation')
    monkeypatch.setattr(client.app.state.agent, 'interpret', broken)
    monkeypatch.setattr(client.app.state.catalog, 'find', lambda *args: ['IBD','MGB_AD','UPMC_AD'])
    result = client.post('/api/chat', json={'query':'Do we have cardiovascular data?'}).json()
    assert result['datasets'] == [] and result['warning']


@pytest.mark.parametrize('dataset_id', ['IBD', 'MGB_AD', 'UPMC_AD'])
def test_public_generation_notes_are_short_and_do_not_expose_internal_review(client, dataset_id):
    catalog = client.app.state.catalog
    private_notes = catalog.root / dataset_id / 'README.md'
    source = private_notes.read_text(encoding='utf-8') if private_notes.exists() else ''
    public = client.get(f'/api/datasets/{dataset_id}/readme/synthetic').json()['text']
    assert len(public.split()) < 220
    assert 'How the fake data were made' in public
    assert 'No real patient rows were copied' in public
    assert '200' in public and '1,000' in public
    assert 'Points to confirm' not in public
    assert '/data/' not in public and '/n/' not in public
    # Old URLs must not provide a back door to the internal review checklist.
    assert client.get(f'/api/datasets/{dataset_id}/readme/catalog').json()['text'] == public
    assert all('Detailed demo notes' not in d['label'] for d in client.get(f'/api/datasets/{dataset_id}').json()['documents'])
    assert client.get(f'/api/datasets/{dataset_id}/download/README.md').status_code == 404
    if dataset_id == 'IBD' and source: assert '## Points to confirm' in source


@pytest.mark.parametrize('dataset_id, expected_rows', [('IBD',17), ('MGB_AD',18), ('UPMC_AD',10)])
def test_dictionary_download_is_english_and_excel_readable(client, dataset_id, expected_rows):
    response = client.get(f'/api/datasets/{dataset_id}/download/column_dictionary.csv')
    assert response.status_code == 200
    assert response.content.startswith(b'\xef\xbb\xbf')
    text = response.content.decode('utf-8-sig')
    assert not re.search(r'[\u3400-\u9fff]', text)
    assert '\ufffd' not in text and 'æ' not in text
    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == expected_rows
    record = client.app.state.catalog.records[dataset_id]
    assert rows == record['column_descriptions']
    if dataset_id == 'IBD':
        assert next(r for r in rows if r['Column'] == 'Rollup_Code')['Meaning'] == 'Code after rollup for codified data.'
        source = (client.app.state.catalog.root / dataset_id / 'column_dictionary.csv').read_text(encoding='utf-8')
        assert '汇总' in source  # Source CSV stays intact; download uses its English copy.


@pytest.mark.parametrize('dataset_id', ['IBD', 'MGB_AD', 'UPMC_AD'])
def test_combined_file_details_cover_every_synthetic_file(client, dataset_id):
    record = client.get(f'/api/datasets/{dataset_id}').json()
    assert [f['file'] for f in record['file_details']] == [f['file'] for f in record['files']]
    assert all(f['location'] and f['name'] for f in record['file_details'])
    assert all(f['columns'] for f in record['file_details'])


def test_ibd_reported_date_distribution_is_not_replaced_by_fake_period(client):
    result = ask(client, 'Do we know a time distribution for IBD data')
    assert result['intent'] == 'dates'
    view = result['datasets'][0]['date_summary']
    assert view['columns'] == ['Statistic','Processed codified','Processed NLP (Total)']
    by_metric = {row['Statistic']:row for row in view['rows']}
    assert by_metric['Minimum']['Processed codified'] == '1840-12-31'
    assert by_metric['25th percentile']['Processed codified'] == '2009-09-18'
    assert by_metric['Median']['Processed codified'] == '2015-07-25'
    assert by_metric['75th percentile']['Processed codified'] == '2019-06-14'
    assert by_metric['Maximum']['Processed codified'] == '2101-08-27'
    assert by_metric['25th percentile']['Processed NLP (Total)'] == '2015-07-06'
    assert by_metric['Median']['Processed NLP (Total)'] == '2019-07-23'
    assert by_metric['75th percentile']['Processed NLP (Total)'] == '2022-08-27'
    assert by_metric['Maximum']['Processed NLP (Total)'] == '6466-05-01'
    assert 'implausible' in view['warning'] and 'unit' in view['warning']
    assert result['datasets'][0]['files'] == []
    assert all(f['source']['kind'] == 'original' for f in result['datasets'][0]['facts'])
    assert 'SYN_' not in result['answer']


@pytest.mark.parametrize('question, expected', [
    ('Show the IBD raw codified date distribution', ['RPDR diagnosis','RPDR medication','RPDR lab','RPDR procedure','IBD_2020 codified']),
    ('What is the IBD NLP time distribution?', ['Processed NLP (Total)']),
    ('Show IBD NLP date distribution by source', ['IBD_2020 NLP','IBD_2019_MART NLP','IBD_2019_2025_MART NLP']),
])
def test_date_tables_preserve_source_groups(client, question, expected):
    result = ask(client, question)
    assert result['datasets'][0]['date_summary']['columns'][1:] == expected


def test_tracker_metadata_is_allowlisted_and_original_workbook_not_exposed(client):
    catalog = client.app.state.catalog
    assert catalog.records['IBD']['tracker_source']['row'] == 9
    assert catalog.records['IBD']['tracker_source']['tracker_id'] == 'DATA-004'
    assert set(catalog.records) == {'IBD','MGB_AD','UPMC_AD'}
    doc = client.get('/api/datasets/IBD/readme/tracker').json()['text']
    assert 'CELEHS_Resource_Catalog.xlsx' in doc and '1840-12-31' in doc
    assert 'README status' not in doc and 'Needs follow-up' not in doc
    assert '25%' not in doc  # Percentiles come from the original README, not invented spreadsheet cells.
    assert client.get('/api/datasets/IBD/download/CELEHS_Resource_Catalog.xlsx').status_code == 404
    answer = ask(client,'Show the IBD spreadsheet entry')
    assert answer['intent'] == 'tracker'
    assert all(f['source']['kind'] == 'tracker' for f in answer['datasets'][0]['facts'])
    assert any(f['source']['label'] == 'Spreadsheet (Datasets!L9)' for f in answer['datasets'][0]['facts'])


def test_tracker_range_does_not_become_monthly_ad_coverage(client):
    result = ask(client,'What is the UPMC AD date distribution?')
    assert result['datasets'][0]['date_summary'] is None
    assert '2004' in result['answer'] and '2023' in result['answer']
    assert 'not verified coverage of a particular monthly file' in result['answer']
    assert 'Date percentiles are not documented' in result['answer']


def test_research_request_names_relevant_monthly_files(client):
    result = ask(client,'I want to study monthly codified and NLP feature counts in the MGB IBD cohort. Which files should I start with?')
    assert [f['file'] for f in result['datasets'][0]['files']] == ['codified_data_monthly_fake_data.csv','NLP_data_monthly_fake_data.csv']
    assert 'IBD monthly codified counts' in result['answer']
    assert 'IBD monthly NLP counts' in result['answer']


def test_apoe_excerpt_is_short_and_does_not_include_unrelated_files(client):
    result = ask(client,'Where can I find MGB AD APOE information for a genetic analysis?')
    assert 'APOE_SNPs.csv' in result['answer']
    assert 'Monthly_codified.RData' not in result['answer']
    assert 'komap_pred_imputed' not in result['answer']
    assert len(result['answer']) < 500


@pytest.mark.parametrize('question', [
    'Use the fake IBD rows to tell me which treatment is most effective.',
    'Can I estimate treatment effects from synthetic IBD data?',
])
def test_fake_data_cannot_be_used_for_clinical_conclusions(client, monkeypatch, question):
    async def should_not_run(*args): raise AssertionError('Synthetic clinical conclusions must not reach inference')
    monkeypatch.setattr(client.app.state.agent, 'interpret', should_not_run)
    result = client.post('/api/chat',json={'query':question}).json()
    assert result['intent'] == 'synthetic_limit' and result['datasets'] == []
    assert 'cannot' in result['answer'] and 'clinical conclusions' in result['answer']
    assert 'Which specific treatment' not in result['answer']


@pytest.mark.parametrize('question', [
    'Can the IBD monthly counts identify exact medication start and stop dates?',
    'Can I get precise start and stop dates for medication from IBD monthly counts?',
])
def test_monthly_precision_answer_is_based_on_schema(client, question):
    result = ask(client, question)
    assert result['intent'] == 'date_precision' and result['compact']
    assert 'not exact medication start or stop dates' in result['answer']
    assert 'validated treatment-event definitions' in result['answer']
    assert result['sources'] and result['datasets'] == []


def test_comparison_has_a_conclusion_and_distinguishes_codified_from_nlp(client):
    result = ask(client,'Compare the monthly count columns for MGB AD and UPMC AD')
    conclusion = result['comparison']
    assert 'column names differ' in result['intro']
    assert conclusion['details'] == [
        'Codified: MGB AD uses `Group_Code` and `N`; UPMC AD uses `feature_id` and `Group_Code_Count`.',
        'NLP: MGB AD uses `cui` and `N`; UPMC AD uses `feature_id` and `N`.']
    assert 'not establish' in conclusion['caution']
    assert len(conclusion['sources']) == 2
    assert any(s['kind'] == 'schema' for s in result['sources'])
    assert result['answer'].index('column names differ') < result['answer'].index('patientnum, month')


def test_comparison_is_scoped_to_requested_kind(client):
    result = ask(client,'Compare MGB AD and UPMC AD monthly NLP columns')
    assert len(result['comparison']['details']) == 1
    assert result['comparison']['details'][0].startswith('NLP:')
    assert 'Group_Code_Count' not in result['answer']


def test_comparison_is_not_specific_to_one_dataset_pair(client):
    result = ask(client,'Compare IBD and MGB AD monthly codified columns')
    assert result['comparison']['details'] == ['Codified: MGB IBD uses `Rollup_Code` and `N`; MGB AD uses `Group_Code` and `N`.']
    assert 'UPMC' not in result['answer']


def test_single_dataset_and_non_schema_queries_have_no_comparison(client):
    assert ask(client,'Show MGB AD monthly columns')['comparison'] is None
    assert ask(client,'Compare patient counts for MGB AD and UPMC AD')['comparison'] is None

