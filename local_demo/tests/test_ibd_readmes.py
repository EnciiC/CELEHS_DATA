import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from local_demo.app import app
from local_demo.semantic import routing_context, direct_document_request


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def ask(client, query, **extra):
    response = client.post('/api/chat', json={'query': query, 'use_llm': False, **extra})
    assert response.status_code == 200
    return response.json()


def test_additional_original_readmes_are_distinct_and_unchanged(client):
    record = client.get('/api/datasets/IBD').json()
    docs = record['original_documents']
    assert [d['kind'] for d in docs] == ['original', 'ibd_lab', 'ibd_project']
    assert len(client.get('/api/datasets/MGB_AD').json()['original_documents']) == 1
    for doc in docs[1:]:
        readme = client.get(doc['url'])
        assert readme.status_code == 200
        data = readme.json()
        assert data['title'] == doc['label']
        assert data['html'] is None
        original = client.app.state.catalog.root / 'IBD' / doc['file']
        assert data['text'] == original.read_text(encoding='utf-8')
        download = client.get('/api/datasets/IBD/download/' + doc['file'])
        assert download.status_code == 200
        assert download.content == original.read_bytes()
        assert client.get('/api/datasets/IBD/files/' + doc['file'] + '/preview').status_code == 404
    assert client.get('/api/datasets/IBD/readme/private_notes').status_code == 404


def test_inventory_includes_laboratory_data_and_project_documentation(client):
    result = ask(client, 'What IBD data do we have?')
    assert 'monthly laboratory' in result['answer'].lower()
    assert 'MAJOR IBD project' in result['answer']
    files = result['datasets'][0]['files']
    assert len(files) == 3
    lab = next(f for f in files if f.get('id') == 'ibd_lab_monthly')
    assert lab['file'] is None and lab['preview_available'] is False
    assert lab['source_files'] == ['IBD_lab_monthly_summary.rds', 'IBD_lab_monthly_summary.csv']
    assert lab['location'] == '//SMBgpa.partners.org/asw_mgb$/SHARE/IBD_lab_data_yunqing/monthly_summary/'
    assert 'no O2 copy' in result['answer']


def test_monthly_code_count_question_does_not_include_lab_or_project(client):
    result = ask(client, 'Show IBD monthly count columns')
    assert len(result['datasets'][0]['files']) == 2
    assert 'LAB_NAME' not in result['answer'] and 'MAJOR' not in result['answer']


def test_lab_as_an_organization_is_not_a_lab_measurement_filter(client):
    from local_demo.readme_resources import is_lab_query
    assert not is_lab_query('What datasets do we have in our lab?')
    assert not is_lab_query('Show lab resources')
    assert is_lab_query('Show IBD lab data')
    result = ask(client, 'What IBD data do we have in the lab?')
    assert len(result['datasets'][0]['files']) == 3


@pytest.mark.parametrize('query', [
    'Show IBD monthly lab columns',
    'What does the IBD laboratory data look like?',
])
def test_lab_schema_is_source_based_and_does_not_claim_fake_rows(client, query):
    result = ask(client, query)
    section = result['datasets'][0]
    assert len(section['files']) == 1
    file = section['files'][0]
    assert file['columns'] == ['EMPI', 'PATIENT_NUM', 'LAB_NAME', 'UNITS', 'MONTH_START',
                               'YEAR', 'MONTH', 'N_MEASUREMENTS', 'MEAN', 'MIN', 'MAX', 'MEDIAN']
    assert file['file'] is None and file['preview_available'] is False
    assert file['row_meaning'] == 'One patient-lab-unit-calendar-month combination.'
    assert all(s['kind'] == 'ibd_lab' for s in result['sources'])
    assert 'Rollup_Code' not in result['answer'] and 'CUI' not in result['answer']


def test_lab_browse_metadata_has_columns_and_processing_but_no_fake_download(client):
    record = client.get('/api/datasets/IBD').json()
    lab = record['documented_files'][0]
    assert lab['owner'] == 'Enci Cai'
    assert lab['processing_script'].endswith('/monthly_summary/lab_value_monthly_count.R')
    assert next(c['Meaning'] for c in lab['column_descriptions'] if c['Column'] == 'LAB_NAME') == 'Albumin, CRP, ESR, FCP, or Hemoglobin'
    assert len(record['files']) == 3  # Existing fake files only; not a real lab-data endpoint.
    assert client.get('/api/datasets/IBD/download/IBD_lab_monthly_summary.csv').status_code == 404
    assert client.get('/api/datasets/IBD/download/IBD_lab_monthly_summary.rds').status_code == 404


@pytest.mark.parametrize('query', ['Show sample rows for IBD labs', 'Show fake IBD laboratory data'])
def test_no_lab_fake_rows_are_invented(client, query):
    result = ask(client, query)
    assert 'No laboratory sample rows are loaded' in result['intro']
    assert 'No fake laboratory rows have been prepared' in result['answer']
    assert not any(f.get('file') for s in result['datasets'] for f in s['files'])
    assert 'generated patients' not in result['answer']


@pytest.mark.parametrize('query, expected, absent', [
    ('How many patients are in the IBD lab data?', '50,826', '56,704'),
    ('How many rows are in IBD lab data?', '1,694,280', '56,704'),
    ('How many source measurements are in IBD laboratory data?', '5,511,418', '56,704'),
    ('How many patients have CRP in IBD lab data?', '12,842', '50,826'),
])
def test_lab_count_units_are_preserved(client, query, expected, absent):
    result = ask(client, query)
    assert expected in result['answer'] and absent not in result['answer']
    assert result['sources'][0]['kind'] == 'ibd_lab'
    assert 'not recalculated' in result['answer']


def test_lab_dates_are_not_the_older_codified_date_table(client):
    result = ask(client, 'What is the IBD lab date distribution?')
    assert result['datasets'][0]['date_summary'] is None
    assert '1988-08' in result['answer'] and '2025-03' in result['answer']
    assert '2000-11' in result['answer'] and '2024-02' in result['answer']
    assert 'percentiles are not reported' in result['answer']
    assert '1840' not in result['answer'] and '6466' not in result['answer']


@pytest.mark.parametrize('query', [
    'What can we do with IBD data?',
    'What have we done with IBD data?',
    'Show the MAJOR IBD project aims',
])
def test_project_questions_show_five_documented_aims_not_fake_data(client, query):
    result = ask(client, query)
    assert result['intent'] == 'project'
    for aim in range(1, 6):
        assert f'Aim {aim}' in result['answer']
    assert 'MAJOR' in result['answer'] and 'not analyses run by this tool' in result['answer']
    assert result['datasets'][0]['files'] == []
    assert all(s['kind'] == 'ibd_project' for s in result['sources'])


def test_ibd_project_is_not_substituted_for_an_ad_project_request(client):
    result = ask(client, 'What have we done with AD data?')
    assert {s['dataset']['id'] for s in result['datasets']} == {'MGB_AD', 'UPMC_AD'}
    assert 'MAJOR' not in result['answer']
    assert 'project-level README is not loaded' in result['answer']
    assert result['sources'] == []


def test_aim_specific_question_retains_reported_settings_and_rules(client):
    result = ask(client, 'What outcomes were used in IBD Aim 4?')
    assert 'all five criteria' in result['answer']
    assert '6, 12, and 24 months' in result['answer']
    assert 'Aim 4 Treatment Response/' in result['answer']
    assert 'four rules' not in result['answer']
    result = ask(client, 'What outcomes were used in IBD Aim 5?')
    assert 'four rules' in result['answer']
    assert 'New immunomodulator use was not counted as failure' in result['answer']
    assert 'five criteria' not in result['answer']


def test_compare_two_project_aims_keeps_both_definitions(client):
    result = ask(client, 'Compare IBD Aim 4 and Aim 5 outcome rules')
    assert 'all five criteria' in result['answer'] and 'four rules' in result['answer']


def test_aim_two_does_not_claim_all_details_are_complete(client):
    result = ask(client, 'What was done in IBD Aim 2?')
    assert 'seqHMM' in result['answer']
    assert 'should be added by Xin' in result['answer']


def test_router_receives_new_facts_and_unknown_lab_is_not_forced(client):
    catalog = client.app.state.catalog
    context, evidence = routing_context(catalog, 'What IBD data do we have?', [], None)
    assert 'IBD:lab_columns' in evidence and 'IBD:project_aim_5' in evidence
    assert any(f['category'] == 'lab' for f in context['evidence'])
    assert not direct_document_request('Do IBD patients have troponin measurements?', catalog.records)
    assert any(f['source']['kind'] == 'ibd_project' for f in catalog.retrieve_original('IBD registry remission', ['IBD']))


def test_lab_query_does_not_turn_upmc_ibd_into_a_documented_cohort(client):
    result = ask(client, 'Show UPMC IBD lab data')
    assert result['datasets'] == []


def test_new_project_readme_updates_old_unconfirmed_raw_concept_lookup(client):
    result = ask(client, 'Show IBD raw dictionary')
    lookup = result['datasets'][0]['dictionaries'][0]
    assert lookup['location'].endswith('2026-10-05_concept_dimension_full_table.csv')
    assert 'visit_dimension' not in lookup['description']
    assert 'not been loaded or verified' in lookup['description']


def test_original_document_parser_rejects_internal_or_unsafe_registration(tmp_path):
    from local_demo.readme_resources import prepare_readmes
    for item in [{'file':'../secrets.md','kind':'extra'}, {'file':'README.md','kind':'synthetic'}]:
        with pytest.raises(ValueError):
            prepare_readmes({'original_readmes':[item]}, tmp_path)


def test_model_aim_comparison_uses_original_definitions_not_free_form_explanation(client, monkeypatch):
    async def explain(*args):
        return {'mode':'explain', 'dataset_ids':['IBD'], 'intent':'columns', 'short_answer':'A general explanation.',
                'evidence_ids':['IBD:project_aim_4']}, {}
    monkeypatch.setattr(client.app.state.agent, 'interpret', explain)
    result = client.post('/api/chat', json={'query':'Compare IBD Aim 4 and Aim 5 outcome rules'}).json()
    assert result['intent'] == 'project' and result['interpretation'] == 'retrieve'
    assert 'all five criteria' in result['answer'] and 'four rules' in result['answer']
    assert result['warning'] is None


def test_lab_fake_request_does_not_ask_the_model_to_select_nonexistent_examples(client, monkeypatch):
    async def route(*args):
        return {'mode':'retrieve', 'dataset_ids':['IBD'], 'intent':'fake', 'short_answer':'', 'evidence_ids':['IBD:lab_columns']}, {}
    async def unnecessary(*args):
        raise AssertionError('Lab source views do not need fake-evidence selection')
    monkeypatch.setattr(client.app.state.agent, 'interpret', route)
    monkeypatch.setattr(client.app.state.agent, 'select', unnecessary)
    result = client.post('/api/chat', json={'query':'Show fake IBD laboratory data'}).json()
    assert result['warning'] is None and result['engine'] == 'local_llm'
    assert 'No laboratory sample rows are loaded' in result['answer']
