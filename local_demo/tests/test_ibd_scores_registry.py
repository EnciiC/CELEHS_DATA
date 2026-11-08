"""Source, preview and retrieval checks for the new local IBD documentation."""
import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from local_demo.app import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def ask(client, query):
    response=client.post('/api/chat',json={'query':query,'use_llm':False})
    assert response.status_code==200
    return response.json()


@pytest.mark.parametrize('question,expected_columns',[
    ('Show PRISM microbiome score columns',7),
    ('What are the Biobank PRS columns?',34),
])
def test_scores_have_documented_schemas_without_fake_data(client,question,expected_columns):
    result=ask(client,question)
    files=result['datasets'][0]['files']
    assert len(files)==1 and len(files[0]['columns'])==expected_columns
    assert files[0]['file'] is None and not files[0]['preview_available']
    assert files[0]['location'].endswith('/Xin/IBD/data/snp_data/deID scores.xlsx')
    assert files[0]['dictionaries']==[]
    assert all(s['kind']=='ibd_scores' for s in result['sources'])
    assert 'Rollup_Code' not in result['answer'] and 'UK Biobank' not in result['answer']


@pytest.mark.parametrize('question,expected_columns',[
    ('Show PRISM endoscopy fake sample rows',11),
    ('Show MGH registry fake sample rows',8),
    ('Show legacy registry fake sample rows',94),
])
def test_registry_previews_preserve_headers_and_generated_ids(client,question,expected_columns):
    result=ask(client,question)
    file=result['datasets'][0]['files'][0]
    assert len(result['datasets'][0]['files'])==1
    assert file['show_preview'] and file['preview_available']
    preview=client.get('/api/datasets/IBD/files/'+file['file']+'/preview?limit=5').json()
    assert preview['synthetic'] and preview['total_rows']==100
    assert len(preview['columns'])==expected_columns and len(preview['rows'])==5
    assert preview['columns']==file['columns']
    id_column='Patient_num' if expected_columns==8 else 'patient_num'
    assert all(row[id_column].startswith('SYN_REG_') for row in preview['rows'])
    assert not file['dictionaries']
    if expected_columns==11:
        assert all(row['modifiedbaronsscore']=='' for row in preview['rows'])
    if expected_columns==94:
        assert all(row['wk30_remis']==row['week52_composite']==row['sex']=='' for row in preview['rows'])
        assert 'week54_crp' in preview['columns'] and 'week52_crp' not in preview['columns']
    record=client.get('/api/datasets/IBD').json()
    dictionary=[r for r in record['column_descriptions'] if r['File']==file['file']]
    assert [r['Column'] for r in dictionary]==file['columns']


def test_raw_statuses_and_file_versions_remain_distinct(client):
    response=ask(client,'Show legacy registry wk14_remis and wk52_remis labels')
    assert 'No clinic visit' in response['answer']
    assert 'no clinic visit' in response['answer']
    assert 'Not w52 yet' in response['answer'] and 'Not wk 52 yet' in response['answer']
    assert 'Stopped' in response['answer']
    response=ask(client,'Show IBD registry file versions')
    assert '338' in response['answer'] and '337' in response['answer']
    assert '(2)' in response['answer']


def test_new_original_readmes_are_served_as_saved(client):
    folder=client.app.state.catalog.root/'IBD'
    for kind,name in [('ibd_scores','IBD_GENETIC_MICROBIOME_README.md'),('ibd_registry','IBD_REGISTRY_README.md')]:
        text=(folder/name).read_text(encoding='utf-8')
        assert client.get('/api/datasets/IBD/readme/'+kind).json()['text']==text
        assert client.get('/api/datasets/IBD/download/'+name).content==(folder/name).read_bytes()
    assert client.get('/api/datasets/IBD/download/deID%20scores.xlsx').status_code==404


def test_registry_to_score_linkage_requires_confirmation(client):
    result=ask(client,'How do I link the IBD registry to microbiome data?')
    assert 'Confirm the identifier mapping' in result['answer']
    assert '±30 days' not in result['answer']  # No registry-to-score rule was supplied.


def test_raw_microbiome_request_does_not_claim_score_workbook_contains_sequence_data(client):
    result=ask(client,'Do we have raw microbiome sequencing or taxon abundance data for IBD?')
    assert result['interpretation']=='verified_readme_topic'
    assert 'does not give a location' in result['answer']
    assert result['datasets'][0]['files']==[]
    assert result['warning'] is None


@pytest.mark.parametrize('query',[
    'MGH treatment-response registry show me more about this',
    'Tell me more about MGH treatment-response registry',
    'Describe the MGH registry',
    'MGH_data-LLM_project__EMPI_and_patientnum.xlsx show me more',
])
def test_named_registry_overview_stays_on_the_requested_file(client,query):
    result=ask(client,query)
    assert result['interpretation']=='verified_readme_topic'
    assert result['intro']=='MGH treatment-response registry'
    assert [s['dataset']['id'] for s in result['datasets']]==['IBD']
    files=result['datasets'][0]['files']
    assert len(files)==1 and files[0]['name']=='MGH treatment-response registry'
    assert 'clinical response at 3 and 12 months' in result['answer']
    assert 'PRISM endoscopy scores' not in result['answer']
    assert 'monthly codified' not in result['answer']
    assert result['warning'] is None
    for f in result['datasets'][0]['facts']:
        assert f['text'] in client.app.state.catalog.documents['IBD'][f['source']['kind']]
    assert {'Show columns','Show 5 fake rows'} <= {a['label'] for a in result['actions']}
    for action in result['actions']:
        followup=ask(client,action['query'])
        assert followup['interpretation']=='verified_readme_topic'
        if action['label']!='How to link with EHR':
            assert [f['name'] for f in followup['datasets'][0]['files']]==['MGH treatment-response registry']


@pytest.mark.parametrize('query,name',[
    ('Tell me more about PRISM endoscopy scores','PRISM endoscopy scores'),
    ('Show me more about the legacy registry','Legacy PRISM treatment-response registry'),
])
def test_specific_file_detail_language_generalizes(client,query,name):
    result=ask(client,query)
    assert result['intro']==name
    assert [f['name'] for f in result['datasets'][0]['files']]==[name]
