import pytest
from fastapi.testclient import TestClient

from local_demo.app import app


@pytest.fixture
def client():
    with TestClient(app) as client: yield client


def ask(client,q,previous=None):
    body={'query':q,'use_llm':True}
    if previous: body.update(selection=previous.get('selection'),previous_dataset_ids=previous.get('context_dataset_ids',[]))
    response=client.post('/api/chat',json=body)
    assert response.status_code==200
    return response.json()


@pytest.mark.parametrize('q',[
    'Compare MGB AD and UPMC AD',
    'Compare the monthly count columns for MGB AD and UPMC AD',
    'How do AD monthly counts from MGB and UPMC differ?',
    'Compare MGB and UPMC AD',
    'What is the difference between MGB AD and UPMC AD?',
    'Contrast MGB AD with UPMC AD',
    'Show MGB AD versus UPMC AD side-by-side',
])
def test_ad_comparison_does_not_need_interpretation_or_model_selection(client,q):
    async def forbidden(*args,**kwargs):
        pytest.fail('A comparison between known subjects must not depend on the model')
    client.app.state.agent.structured=forbidden
    r=ask(client,q)
    assert r['interpretation']=='verified_comparison' and r['warning'] is None
    assert set(r['selection']['ids'])=={'MGB_AD','UPMC_AD'}
    assert r['engine']=='catalog' and r['comparison_table']['rows'] and r['sources']


@pytest.mark.parametrize('q,expected',[
    ('Compare monthly codified and NLP counts for IBD',{'IBD'}),
    ('Compare MGB AD daily codified and UPMC AD monthly NLP',{'MGB_AD','UPMC_AD'}),
    ('Compare MGH treatment-response registry and PRISM endoscopy scores',{'IBD'}),
    ('Compare MGH registry and legacy registry',{'IBD'}),
    ('Compare the PRISM and Biobank scores',{'IBD'}),
    ('Compare FAS and CRAFT',{'ZX_FAS','ZX_CRAFT'}),
    ('Compare 4CE and CORAL',{'ZX_4CE','ZX_CORAL'}),
    ('Compare FAVOR gene-disease relations and PrimeKG',{'ZX_FAVOR_GENE','ZX_PRIMEKG'}),
    ('Compare MRCONSO.RRF and MRREL.RRF',{'ZX_UMLS'}),
    ('Compare IBD and All of Us',{'IBD','ZX_AOU'}),
    ('Compare WEST severe asthma and WEST pulmonary hypertension',{'KIM_WEST_SA','KIM_WEST_PH'}),
])
def test_comparison_across_resource_types_files_and_granularities(client,q,expected):
    r=ask(client,q)
    assert r['interpretation']=='verified_comparison'
    assert set(r['context_dataset_ids'])==expected
    assert len(r['selection']['ids'])>=2 and r['sources'] and r['warning'] is None


def test_count_comparison_never_uses_fake_rows_as_cohort_counts(client):
    r=ask(client,'Compare patient counts for MGB AD and UPMC AD')
    row=next(row for row in r['comparison_table']['rows'] if row['Field']=='Documented patient / cohort count')
    assert row['MGB AD']==row['UPMC AD']=='Not documented for these files.'
    assert not any(number in r['answer'] for number in ['126,370,653','723,473,066','1,000','200 generated'])


@pytest.mark.parametrize('q',[
    'Compare MGB AD with UPMC MS',
    'Compare MGB AD with unknown_resource.csv',
    'Compare Monthly_codified.RData with Monthly_NLP.RData',
    'Compare MGB AD',
])
def test_unknown_and_ambiguous_targets_are_clarified_not_silently_substituted(client,q):
    r=ask(client,q)
    assert r['interpretation']=='comparison_clarification'
    assert not r['datasets'] and not r['resources']
    assert r['warning'] is None and r['comparison'] is None


def test_comparison_followups_keep_the_pair_and_nlp_scope(client):
    r=ask(client,'Compare MGB AD and UPMC AD monthly NLP columns')
    original=r['selection']['ids']
    r=ask(client,'What about storage?',r)
    assert r['selection']['ids']==original and r['selection']['data_kinds']==['nlp']
    assert [row['Field'] for row in r['comparison_table']['rows']]==['Storage']
    r=ask(client,'What about the columns?',r)
    assert r['selection']['ids']==original
    assert 'Group_Code_Count' not in r['answer'] and 'Rollup_Code' not in r['answer']
    assert r['comparison']['details']==['NLP: MGB AD uses `cui` and `N`; UPMC AD uses `feature_id` and `N`.']
    r=ask(client,'Can I combine them?',r)
    assert 'does not establish' in r['intro']
    r=ask(client,'What IBD data do we have?',r)
    assert r['context_dataset_ids']==['IBD'] and r['selection']['kind']!='comparison'


def test_comparison_from_current_file_and_unknown_schemas(client):
    r=ask(client,'Tell me more about MRCONSO.RRF')
    r=ask(client,'Compare this with MRREL.RRF',r)
    assert r['interpretation']=='verified_comparison'
    assert len(r['selection']['ids'])==2
    r=ask(client,'What about the columns?',r)
    assert 'not documented' in r['intro']
    assert not r['datasets']


def test_external_guide_label_does_not_force_access_comparison(client):
    r=ask(client,'Compare All of Us access guide and MGB AD')
    assert r['selection']['view']=='overview'
    storage=next(row for row in r['comparison_table']['rows'] if row['Field']=='Storage')
    assert 'No O2 participant-level copy' in storage['All of Us access guide']


@pytest.mark.parametrize('field',['overview','columns','location','counts','dates','access','code'])
def test_structured_picker_bypasses_language_routing(client,field):
    async def forbidden(*args,**kwargs): pytest.fail('The comparison picker must not call a model')
    client.app.state.agent.structured=forbidden
    response=client.post('/api/compare',json={'entity_ids':['MGB_AD','UPMC_AD'],'field':field})
    assert response.status_code==200
    result=response.json()
    assert result['selection']['ids']==['MGB_AD','UPMC_AD']
    assert result['selection']['view']==field and result['warning'] is None


def test_picker_options_and_input_validation(client):
    options=client.get('/api/comparison-options').json()['options']
    assert len({o['id'] for o in options})==len(options)
    assert any('endoscopy agent output' in o['label'] for o in options)
    assert any('MGH treatment-response' in o['label'] for o in options)
    for ids in [['MGB_AD','missing'],['MGB_AD','MGB_AD'],['MGB_AD']]:
        assert client.post('/api/compare',json={'entity_ids':ids}).status_code==422


def test_monthly_kinds_are_aligned_in_separate_table_rows(client):
    r=ask(client,'Compare the monthly count columns for MGB AD and UPMC AD')
    rows={row['Field']:row for row in r['comparison_table']['rows']}
    codified=rows['Monthly codified columns'];nlp=rows['Monthly NLP columns']
    assert 'Group_Code_Count' in codified['UPMC AD'] and 'Group_Code' in codified['MGB AD']
    assert '`cui`' in nlp['MGB AD'] and 'Group_Code_Count' not in nlp['UPMC AD']


def test_subgroup_counts_are_not_replaced_by_overall_patient_counts(client):
    r=ask(client,'Compare patient counts for patients with kidney disease in IBD and MGB AD')
    assert r['interpretation']=='comparison_clarification'
    assert '56,704' not in r['answer'] and not r['datasets']
    assert r['selection']['kind']=='comparison'
