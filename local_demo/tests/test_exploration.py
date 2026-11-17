import json

import httpx
import pytest
from fastapi.testclient import TestClient

from local_demo.agent import Agent
from local_demo.app import app
from local_demo.exploration import followup_view


@pytest.fixture
def client():
    with TestClient(app) as client: yield client


def ask(client,q,previous=None):
    body={'query':q,'use_llm':False}
    if previous:
        body.update(previous_dataset_ids=previous.get('context_dataset_ids',[]),
                    selection=previous.get('selection'), pending_topic=previous.get('pending_topic'))
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


def test_registry_linkage_asks_for_scope_then_resolves_a_short_reply(monkeypatch):
    monkeypatch.setenv('CATALOG_PROVIDER', 'cloudflare')
    with TestClient(app) as client:
        query = 'How do I connect the registry labels to EHR'
        question = ask(client, query)
        assert question['intent'] == 'registry_scope'
        assert not question['context_dataset_ids'] and not question['sources']
        assert {item['label'] for item in question['actions']} == {'MGB IBD', 'MGB MS', 'UPMC MS'}
        scoped = ask(client, 'MS', question)
        assert set(scoped['context_dataset_ids']) == {'MGB_MS', 'UPMC_MS'}
        assert 'id_participant' in scoped['answer'] and 'mapping_index' in scoped['answer']
        upmc = ask(client, 'UPMC MS', question)
        assert upmc['context_dataset_ids'] == ['UPMC_MS']
        ibd = ask(client, 'IBD', question)
        assert ibd['context_dataset_ids'] == ['IBD'] and 'baseline_date' in ibd['answer']


def test_ms_registry_question_switches_from_ibd_and_keeps_the_new_context(monkeypatch):
    monkeypatch.setenv('CATALOG_PROVIDER', 'cloudflare')
    with TestClient(app) as client:
        ibd = ask(client, 'How do I link IBD registry data to EHR?')
        ms = ask(client, 'do we have registry data in MS', ibd)
        assert set(ms['context_dataset_ids']) == {'MGB_MS', 'UPMC_MS'}
        assert 'EDSS' in ms['answer'] and 'PDDS' in ms['answer']
        for query in ('How do I connect the registry labels to EHR', 'How do I connect these to EHR?'):
            linked = ask(client, query, ms)
            assert set(linked['context_dataset_ids']) == {'MGB_MS', 'UPMC_MS'}
            assert 'calendar_month' in linked['answer'] and 'PROMOTE' in linked['answer']
            assert all(source['kind'].startswith('ms_') for source in linked['sources'])
        explicit_ibd = ask(client, 'How do I link IBD registry data to EHR?', ms)
        assert explicit_ibd['context_dataset_ids'] == ['IBD']


def test_ms_lab_answers_show_raw_result_location_and_keep_processed_counts_separate(monkeypatch):
    monkeypatch.setenv('CATALOG_PROVIDER', 'cloudflare')
    with TestClient(app) as client:
        broad = ask(client, 'Are lab values available for MS?')
        assert broad['intent'] == 'ms_labs'
        assert 'UPMC MS has raw lab results on O2' in broad['intro']
        assert 'MGB MS provides lab test codes and counts' in broad['intro']
        assert 't0' not in broad['answer']

        upmc = ask(client, 'Are lab values available for UPMC MS?', broad)
        assert upmc['context_dataset_ids'] == ['UPMC_MS']
        assert upmc['answer'].count('ms_obs_fact_') == 4
        assert '/SHARE/UPMC/MS/data_raw/data_codified' in upmc['answer']
        assert 'headerless' in upmc['answer'] and 'reference ranges' in upmc['answer']
        assert 't0' not in upmc['answer'] and 'MGB' not in upmc['answer']
        columns = ask(client, 'What are the columns?', upmc)
        [card] = columns['datasets'][0]['files']
        assert card['show_columns']
        assert card['columns'][5:] == ['Result value', 'Unit', 'Reference low', 'Reference high']

        monthly = ask(client, 'Do the monthly UPMC MS files have lab values?', upmc)
        assert 'raw codified files hold the result values' in monthly['answer']
        [card] = monthly['datasets'][0]['files']
        assert card['name'] == 'Monthly codified EHR'
        mgb = ask(client, 'Are lab values available for MGB MS?', upmc)
        assert 'Result values are absent' in mgb['intro']
        assert 'ms_obs_fact_' not in mgb['answer']


def test_upmc_ms_date_coverage_uses_date_facts_without_cohort_report(monkeypatch):
    monkeypatch.setenv('CATALOG_PROVIDER', 'cloudflare')
    with TestClient(app) as client:
        dates = ask(client, 'What is the UPMC MS date coverage?')
        assert dates['context_dataset_ids'] == ['UPMC_MS'] and dates['intent'] == 'ms_coverage'
        assert 'January 2004 to December 2022' in dates['answer']
        assert 'January 2011 to December 2021' in dates['answer']
        assert '10,466' not in dates['answer']
        assert {source['kind'] for source in dates['sources']} == {'ms_raw'}
        notes = ask(client, 'What is the date range of the raw notes?', dates)
        assert 'November 2021' in notes['answer'] and 'June 2013' in notes['answer']
        assert 'Codified EHR' not in notes['answer']
        report = ask(client, 'Show summary statistics for UPMC MS', dates)
        assert '10,466' in report['answer'] and 'Filtered cohort' not in dates['answer']


def test_hosted_research_followup_is_grounded_in_the_selected_ms_file(monkeypatch):
    for key, value in {
        'CATALOG_PROVIDER': 'cloudflare', 'CATALOG_CHAT_ENABLED': 'true',
        'CATALOG_CLOUD_LIMITS_CONFIRMED': 'true', 'CLOUDFLARE_ACCOUNT_ID': 'a' * 32,
        'CLOUDFLARE_GATEWAY_ID': 'test', 'CLOUDFLARE_API_TOKEN': 'test-only',
    }.items():
        monkeypatch.setenv(key, value)
    replies = iter([
        'Splitting by row can put the same patient_num in training and testing. Split by patient_num instead.',
        'The UPMC_AD files contain a patient_num column.',
    ])

    async def answer_from_documentation(self, instructions, context, schema):
        metadata = context['selected_file']
        assert metadata['dataset'] == 'UPMC MS'
        assert metadata['name'] == 'Monthly NLP concepts'
        assert set(metadata['columns']) == {'patient_num', 'calendar_month', 'cui', 'count', 'n_days'}
        assert set(context) == {'question', 'selected_file'}
        return {'explanation': next(replies)}

    monkeypatch.setattr(Agent, 'structured', answer_from_documentation)
    with TestClient(app) as client:
        file = ask(client, 'Show columns for all_nlp_calendar_month_aggregation.parquet at UPMC')
        body = {
            'query': 'For the UPMC file we just opened, explain why randomly splitting feature rows '
                     'could leak information about the same patient_num between training and test sets.',
            'previous_dataset_ids': file['context_dataset_ids'], 'selection': file['selection'],
        }
        correct = client.post('/api/chat', json=body).json()
        assert correct['engine'] == 'hosted_llm'
        assert correct['context_dataset_ids'] == ['UPMC_MS'] and correct['selection'] == file['selection']
        assert 'Split by patient_num' in correct['answer']
        assert correct['actions'][0]['document']['dataset_id'] == 'UPMC_MS'

        incorrect = client.post('/api/chat', json=body).json()
        assert incorrect['warning'] and 'UPMC_AD' not in incorrect['answer']
        assert incorrect['context_dataset_ids'] == ['UPMC_MS'] and incorrect['selection'] == file['selection']


def test_hosted_study_ideas_use_the_requested_dataset_and_cite_files(monkeypatch):
    monkeypatch.setenv('CATALOG_PROVIDER', 'cloudflare')
    calls = []

    async def suggest(self, url, **request):
        body = request['json']
        assert body['response_format'] == {'type': 'json_object'}
        context = json.loads(body['messages'][-1]['content'])
        calls.append(context)
        assert {file['dataset'] for file in context['files']} == {'UPMC MS'}
        related = next(file for file in context['files'] if file['name'] == 'Monthly NLP concepts')
        result = {'ideas': [{
            'question': 'How do documented concepts vary over follow-up?',
            'approach': 'Summarize concept counts over time using patient_num.',
            'check': 'Check variation in the number of observed periods.',
            'files': [related['id'] if len(calls) < 3 else 'unknown'],
        }]}
        return httpx.Response(200, json={'success': True, 'result': {'response': result}},
                              request=httpx.Request('POST', url))

    monkeypatch.setattr(httpx.AsyncClient, 'post', suggest)
    with TestClient(app) as client:
        agent = client.app.state.agent
        monkeypatch.setattr(type(agent.cloud), 'ready', property(lambda self: True))
        for query in ('What kinds of analyses could I do with UPMC MS data?',
                      'What could I study using all_nlp_calendar_month_aggregation.parquet at UPMC?'):
            answer = client.post('/api/chat', json={'query': query}).json()
            assert answer['engine'] == 'hosted_llm' and answer['context_dataset_ids'] == ['UPMC_MS']
            assert answer['analysis_ideas'][0]['files'] == ['UPMC MS · Monthly NLP concepts']
            assert answer['sources'][0]['kind'] == 'ms_dictionary'
        assert len(calls[0]['files']) > 1 and len(calls[1]['files']) == 1
        rejected = client.post('/api/chat', json={'query': 'What analyses could I do with UPMC MS data?'}).json()
        assert rejected['engine'] == 'catalog' and 'saved study ideas' in rejected['warning']
        assert 'unknown' not in rejected['answer']
        assert ask(client, 'What kinds of analyses could I do?')['intent'] == 'analysis_scope'
        saved = ask(client, 'What kinds of analyses could I do with UPMC MS data?')
        assert saved['engine'] == 'catalog'
        assert 'PDDS change' in saved['analysis_ideas'][0]['question']
        assert 'UPMC MS · Monthly registry labels' in saved['analysis_ideas'][0]['files']


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
