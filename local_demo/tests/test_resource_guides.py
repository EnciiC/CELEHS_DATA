import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from local_demo.app import app
from local_demo.resource_guides import ResourceLibrary, ROOT


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def ask(client, query, previous=None):
    r=client.post('/api/chat',json={'query':query,'previous_dataset_ids':previous or [],'use_llm':False})
    assert r.status_code == 200
    return r.json()


def test_new_member_and_real_data_download_scope(client):
    result=ask(client,'I am new. What can I find here?')
    assert result['intent']=='resource_inventory'
    assert len(result['inventory']['resources'])==14
    assert len(result['inventory']['datasets'])==3
    result=ask(client,'Can I download the real patient notes from here?')
    assert result['intent']=='data_access' and not result['resources'] and not result['datasets']
    assert 'required permission' in result['answer']
    result=ask(client,'I want to connect variants to genes. What should I look at?')
    assert result['intent']=='resource_research'


def test_hosted_guides_use_same_sources_and_correct_engine(monkeypatch):
    import asyncio
    from local_demo.agent import Agent
    from local_demo.catalog import Catalog
    monkeypatch.setenv('CATALOG_PROVIDER','cloudflare')
    catalog=Catalog()
    assert len(catalog.library.entries)==14
    agent=Agent(catalog)
    async def select(system,context,schema):
        return {'resource_ids':['ZX_AOU'],'intent':'location'}
    agent.structured=select
    result=asyncio.run(agent.answer('Is All of Us data stored on O2?'))
    assert result['engine']=='hosted_llm'
    assert result['model']=='@cf/openai/gpt-oss-20b'
    assert 'no O2 participant-level copy' in result['answer']


def test_general_overview_does_not_become_access_instructions():
    import asyncio
    from local_demo.agent import Agent
    from local_demo.catalog import Catalog
    agent=Agent(Catalog())
    async def overinterpret(system,context,schema):
        return {'resource_ids':['ZX_FAVOR_VARIANT'],'intent':'access'}
    agent.structured=overinterpret
    result=asyncio.run(agent.answer('Tell me about FAVOR variant regulatory relations.'))
    assert result['intent']=='resource_overview'
    assert '295,763 rsIDs' in result['answer']


def test_all_readmes_are_registered_unmodified_and_not_payloads(client):
    library=client.app.state.catalog.library
    assert len(library.entries)==14
    assert len(library.summaries('datasets'))==3
    assert len(library.summaries('derived'))==11
    assert library.summaries('models')==[]
    manifest=json.loads((ROOT/'source_manifest.json').read_text(encoding='utf8'))
    for receipt in manifest['entries']:
        r=client.get('/api/resources/'+receipt['id']+'/download/readme')
        assert r.status_code==200
        assert hashlib.sha256(r.content).hexdigest()==receipt['sha256']
    assert client.get('/api/resources/ZX_AOU/download/data.csv').status_code==404
    assert client.get('/api/resources/../registry.json').status_code==404


def test_all_of_us_never_turns_introduction_into_o2_data_copy(client):
    result=ask(client,'Is All of Us data stored on O2?')
    assert result['datasets']==[]
    assert len(result['resources'])==1
    resource=result['resources'][0]
    assert resource['id']=='ZX_AOU'
    assert 'No O2 participant-level copy' in result['answer']
    assert resource['locations'][0]['kind']=='guide'
    assert resource['locations'][1]['kind']=='external'
    assert '/dataset-handoffs/all-of-us-workbench.md' in resource['locations'][0]['value']


def test_access_guide_and_workbench_open_questions_are_source_based(client):
    result=ask(client,'How do I get started with All of Us?')
    assert result['intent']=='resource_start'
    assert 'authorized research account' in result['answer']
    result=ask(client,'What remains unresolved for All of Us?')
    assert 'billing' in result['answer'] and 'successor' in result['answer']


def test_distinct_matrix_sources_and_ancestry_scope(client):
    result=ask(client,'Compare FAS UKB and CRAFT')
    assert {r['id'] for r in result['resources']}=={'ZX_FAS','ZX_CRAFT'}
    assert 'FAS only; no O2 copy' in result['answer']
    assert 'Storage: O2' in result['answer']
    assert 'not original matrix generation' in result['answer']
    result=ask(client,'Which files and ancestries are included in MVP multi-ancestry data?')
    assert 'AFR, AMR, EAS, and EUR' in result['answer']
    assert 'every preserved CRAFT runtime' in result['answer']


def test_public_reference_is_distinct_from_collaborator_export(client):
    result=ask(client,'Is FAVOR gene disease data public?')
    assert 'collaborator' in result['answer'].lower()
    assert 'governing source terms' in result['answer']
    result=ask(client,'Is PrimeKG public?')
    assert 'public CC0' in result['answer']


def test_relation_direction_and_private_code_preserved(client):
    result=ask(client,'What files are in the biomedical relation datasets?')
    assert 'indication2drug' in result['answer'] and 'indication2gene' in result['answer']
    assert 'lm_test_dis_gene.jsonl' in result['answer'] and 'lm_test_path_gene.jsonl' in result['answer']
    result=ask(client,'What code is documented for CRAFT?')
    assert '--build ukb_sign' in result['answer']
    assert '8a12d517dd5f4a87a569bace9038ce5f9c506938' in result['answer']


def test_readme_contact_is_not_inferred_owner_and_licence_is_not_assumed(client):
    resource=client.get('/api/resources/ZX_UMLS').json()
    assert resource['contact']=='Zongxin Yang' and 'owner' not in resource
    result=ask(client,'Can everyone on O2 use UMLS?')
    assert 'licence' in result['answer'] and 'does not automatically authorize' in result['answer']


@pytest.mark.parametrize('query',['Show fake rows for CORAL','Show monthly columns for PrimeKG'])
def test_no_clinical_schema_or_rows_are_invented(client,query):
    result=ask(client,query)
    assert not result['datasets']
    assert 'not supplied' in result['answer'] or 'No fake sample rows' in result['answer']
    assert 'EMPI, month' not in result['answer']


def test_followups_keep_external_resource_and_allow_new_named_resource(client):
    result=ask(client,'How do I get started?', ['ZX_AOU'])
    assert [r['id'] for r in result['resources']]==['ZX_AOU']
    assert result['intent']=='resource_start'
    result=ask(client,'What about PrimeKG?', ['ZX_AOU'])
    assert [r['id'] for r in result['resources']]==['ZX_PRIMEKG']
    result=ask(client,'What remains unresolved?', ['ZX_AOU'])
    assert [r['id'] for r in result['resources']]==['ZX_AOU']
    assert 'successor' in result['answer']
    result=ask(client,'What access requirements apply to All of Us access guide?')
    assert result['intent']=='resource_access'
    assert 'authorized' in result['answer']


def test_empty_models_and_embeddings_not_inferred_from_project_names(client):
    result=ask(client,'What LLM models are stored on O2?')
    assert 'No model-resource README' in result['answer']
    assert result['inventory']['resources']==[]
    result=ask(client,'Do we have an embedding matrix?')
    assert 'No embedding-matrix README' in result['answer']


def test_discovery_does_not_substitute_missing_disease_cohort(client):
    result=ask(client,'Do we have cardiovascular data?')
    assert not result['datasets'] and not result.get('resources')
    result=ask(client,'Which resources connect genes to diseases?')
    assert any(r['id']=='ZX_FAVOR_GENE' for r in result['resources'])


def test_corrupt_snapshot_is_rejected(tmp_path):
    import shutil
    shutil.copytree(ROOT,tmp_path/'guides')
    (tmp_path/'guides/zongxin/ZX_AOU/README_original.md').write_text('modified',encoding='utf8')
    with pytest.raises(ValueError,match='provenance'):
        ResourceLibrary(tmp_path/'guides')
