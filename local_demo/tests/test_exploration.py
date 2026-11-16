import pytest
from fastapi.testclient import TestClient

from local_demo.app import app
from local_demo.exploration import followup_view


@pytest.fixture
def client():
    with TestClient(app) as client: yield client


def ask(client,q,previous=None):
    body={'query':q,'use_llm':False}
    if previous: body.update(previous_dataset_ids=previous.get('context_dataset_ids',[]),selection=previous.get('selection'))
    r=client.post('/api/chat',json=body)
    assert r.status_code==200
    return r.json()


@pytest.mark.parametrize('q,view',[
    ('tell me more','details'),('Could you elaborate?','details'),('Can you give me more details?','details'),
    ('Tell me about it','details'),('What does it contain?','details'),('More information please','details'),
    ('Could you expand on that?','details'),('Please elaborate on this','details'),
    ('Can you provide more information?','details'),('More about this','details'),
    ('What are its column names?','columns'),('What does it look like?','columns'),
    ('Please show me the columns','columns'),('Can I see a preview?','preview'),
    ('Show me some sample rows from it','preview'),('Where is it?','location'),("What's the path?",'location'),
    ('Show the original README','original'),('How do I get started?','start'),
    ('What about access?','access'),('How do I connect these with our existing EHR?','linkage'),
])
def test_followup_phrases(q,view):
    assert followup_view(q)==view


def test_registry_multiturn_flow_preserves_file_through_mapping_and_readme(client):
    r=ask(client,'Tell me more about MGH treatment-response registry')
    focus=r['selection']['id']
    for q in ['tell me more','What are the columns?','Can I see a preview?','Where is it?',
              'Show the original README','How do I link this with EHR?','Tell me about it']:
        r=ask(client,q,r)
        assert r['selection']['kind']=='file' and r['selection']['id']==focus
        assert r['context_dataset_ids']==['IBD'] and r['warning'] is None
        if 'link' not in q:
            assert [f['name'] for f in r['datasets'][0]['files']]==['MGH treatment-response registry']
    assert 'clinical response at 3 and 12 months' in r['answer']


def test_readme_action_opens_the_source_for_the_current_file(client):
    r=ask(client,'Show columns for combined_daily.RData in MGB AD')
    r=ask(client,'Show the original README',r)
    doc=next(a['document'] for a in r['actions'] if 'document' in a)
    assert doc=={'dataset_id':'MGB_AD','kind':'original'}


def test_switching_subject_clears_old_file_and_ambiguous_group_asks_for_choice(client):
    r=ask(client,'Tell me more about MGH treatment-response registry')
    r=ask(client,'What AD data do we have?',r)
    assert r['selection']['kind']=='choices'
    r=ask(client,'tell me more',r)
    assert r['interpretation']=='exploration_choice' and not r['datasets']
    assert {a['label'] for a in r['actions']}=={'MGB AD','UPMC AD'}
    r=ask(client,'Show UPMC AD Monthly_codified.RData columns',r)
    focus=r['selection']['id']
    r=ask(client,'tell me more',r)
    assert r['selection']['id']==focus and r['context_dataset_ids']==['UPMC_AD']
    assert 'MGH' not in r['answer']


def test_reference_file_start_and_access_remain_file_scoped(client):
    r=ask(client,'Tell me more about MRCONSO.RRF')
    focus=r['selection']['id']
    for q in ['tell me more','Where is it?','How do I get started?','What about access?','Show the original README']:
        r=ask(client,q,r)
        assert r['selection']['id']==focus
        assert [e['id'] for e in r['resources']]==['ZX_UMLS']
    assert r['actions'][0]['document']=={'resource_id':'ZX_UMLS'}


def test_worksheet_focus_and_missing_synthetic_data_are_kept(client):
    r=ask(client,'Show PRISM microbiome score columns')
    assert r['selection']['kind']=='file'
    focus=r['selection']['id']
    r=ask(client,'Can I see a preview?',r)
    assert r['selection']['id']==focus
    f=r['datasets'][0]['files'][0]
    assert f['name']=='PRISM genetic and microbiome scores'
    assert f['file'] is None and not f['show_preview']
    assert 'have not been prepared' in r['intro']


def test_column_meaning_comes_from_the_active_file(client):
    r=ask(client,'Show MGB AD Monthly_codified.RData columns')
    r=ask(client,'What does N mean?',r)
    assert 'Number of occurrences' in r['answer']
    assert r['datasets'][0]['files'][0]['columns']==['N']
    r=ask(client,'Show columns for patient_summary.csv in WEST pulmonary hypertension (BCH)',r)
    r=ask(client,'What does FINALPAH mean?',r)
    assert 'FINALPAH_gold' in r['answer']
    assert r['resources'][0]['selected_file_name']=='patient_summary.csv'


def test_ms_column_followup_with_here_uses_the_selected_upmc_file(monkeypatch):
    monkeypatch.setenv('CATALOG_PROVIDER', 'cloudflare')
    with TestClient(app) as client:
        compared = ask(client, 'Compare monthly NLP columns for MGB MS and UPMC MS')
        assert compared['selection']['kind'] == 'comparison'
        selected = ask(client, 'Show columns for all_nlp_calendar_month_aggregation.parquet at UPMC', compared)
        assert selected['selection']['kind'] == 'file'
        for query in ('What does count mean here', 'What does `count` mean in this file?', 'What does count mean?'):
            response = client.post('/api/lookup', json={
                'query': query, 'previous_dataset_ids': selected['context_dataset_ids'],
                'selection': selected['selection'],
            }).json()
            assert response['context_dataset_ids'] == ['UPMC_MS']
            assert response['selection'] == selected['selection']
            assert 'asserted mention' in response['answer'] and 'count equals n_days' in response['answer']
            assert response['engine'] == 'catalog' and response['warning'] is None
            [file] = response['datasets'][0]['files']
            assert file['columns'] == ['count']
            assert [row['Column'] for row in file['column_descriptions']] == ['count']


def test_no_context_invalid_context_and_separate_sessions_do_not_guess_a_file(client):
    r=ask(client,'tell me more')
    assert r['interpretation']=='exploration_choice'
    response=client.post('/api/chat',json={'query':'tell me more','selection':{'kind':'file','id':'invented'},'use_llm':False}).json()
    assert response['interpretation']=='exploration_choice'
    a=ask(client,'Tell me more about combined_daily.RData in MGB AD')
    b=ask(client,'Tell me more about MRCONSO.RRF')
    assert ask(client,'Where is it?',a)['selection']['id']==a['selection']['id']
    assert ask(client,'Where is it?',b)['selection']['id']==b['selection']['id']


def test_browse_files_expose_selection_and_thanks_keep_it(client):
    record=client.get('/api/datasets/IBD').json()
    selected=record['file_selections']['MGH_data-LLM_project__EMPI_and_patientnum_fake_data.csv']
    r={'selection':selected,'context_dataset_ids':['IBD']}
    r=ask(client,'tell me more',r)
    assert r['datasets'][0]['files'][0]['name']=='MGH treatment-response registry'
    r=ask(client,'thanks',r)
    assert r['selection']['id']==selected['id']
    assert ask(client,'What are the columns?',r)['selection']['id']==selected['id']
