import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from local_demo.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:yield c


def ask(client,query):
    r=client.post('/api/chat',json={'query':query,'use_llm':False})
    assert r.status_code==200
    return r.json()


def test_west_readmes_are_dataset_guides_without_inferred_o2_paths_or_fake_files(client):
    inventory=client.get('/api/inventory').json()
    assert len(inventory['datasets'])+len(inventory['resources'])==19
    west=[r for r in inventory['resources'] if r['id'].startswith('KIM_')]
    assert len(west)==2 and all(r['category']=='datasets' for r in west)
    for summary in west:
        detail=client.get('/api/resources/'+summary['id']).json()
        assert detail['contact']=='Kim Greco' and detail['location_label']=='Raw data source'
        assert detail['locations']==[] and detail['has_columns'] and not detail['has_access']
        assert 'files' not in detail and 'fake_files' not in detail and 'O2' not in detail['storage']
        original=client.get('/api/resources/'+summary['id']+'/download/readme')
        assert hashlib.sha256(original.content).hexdigest()==detail['sha256']
        assert original.content==client.app.state.catalog.library.entries[summary['id']]['source_path'].read_bytes()
        assert client.get('/api/resources/'+summary['id']+'/download/fake_data.csv').status_code==404


def test_west_general_discovery_and_source_counts(client):
    result=ask(client,'What WEST datasets do we have?')
    assert {r['id'] for r in result['resources']}=={'KIM_WEST_SA','KIM_WEST_PH'}
    assert not result['datasets']
    assert '7,822' in result['answer'] and '14,305' in result['answer']
    assert 'BCH E3 server' in result['answer'] and 'BCH MAPS server' in result['answer']


@pytest.mark.parametrize('query,expected,label',[
 ('Show the patient summary columns for WEST severe asthma','KIM_WEST_SA','FINALSA'),
 ('Show the patient summary columns for pulmonary hypertension','KIM_WEST_PH','FINALPAH'),
])
def test_disease_specific_columns_do_not_mix_west_cohorts(client,query,expected,label):
    result=ask(client,query)
    assert [r['id'] for r in result['resources']]==[expected]
    tables=[b['table'] for b in result['resources'][0]['blocks'] if 'table' in b]
    assert len(tables)==1 and len(tables[0]['rows'])==9
    assert any(r['Column']==label for r in tables[0]['rows'])
    assert 'COUNT' not in [r['Column'] for r in tables[0]['rows']]


def test_time_and_silver_label_definitions_come_from_the_dictionary(client):
    result=ask(client,'What does TIME mean for WEST severe asthma?')
    rows=result['resources'][0]['blocks'][0]['table']['rows']
    assert len(rows)==1 and rows[0]['Column']=='TIME'
    assert 'months since first asthma code' in rows[0]['Meaning']
    result=ask(client,'How is FINALPAH_silver defined for pulmonary hypertension?')
    rows=result['resources'][0]['blocks'][0]['table']['rows']
    assert len(rows)==1 and rows[0]['Column']=='FINALPAH_silver'
    assert 'PheCode 415.2 appeared 2+ times' in rows[0]['Meaning']


def test_processing_scripts_and_paper_are_readme_content(client):
    for name,rid in [('severe asthma','KIM_WEST_SA'),('pulmonary hypertension','KIM_WEST_PH')]:
        result=ask(client,'What code is used for '+name+'?')
        assert 'train.py' in result['answer'] and 'eval.py' in result['answer']
        original=client.app.state.catalog.library.entries[rid]['original']
        for block in result['resources'][0]['blocks']:
            if block['text']:assert block['text'] in original
            for link in block.get('links',[]):assert link['url'] in original


def test_note_discovery_does_not_treat_west_sequences_as_supplied_notes(client):
    result=ask(client,'Do we have any note data?')
    assert {r['id'] for r in result['resources']}=={'ZX_4CE','ZX_CORAL'}
