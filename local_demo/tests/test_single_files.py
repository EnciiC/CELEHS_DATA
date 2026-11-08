import pytest
from fastapi.testclient import TestClient

from local_demo.app import app
from local_demo.single_files import file_inventory,match_files


@pytest.fixture
def client():
    with TestClient(app) as client: yield client


def ask(client,q):
    response=client.post('/api/chat',json={'query':q,'use_llm':False})
    assert response.status_code==200
    return response.json()


@pytest.mark.parametrize('query,parent,filename',[
    ('Tell me more about combined_daily.RData in MGB AD','MGB_AD','combined_daily_fake_data.csv'),
    ('Show MGB AD Daily_codified.RData columns','MGB_AD','Daily_codified_fake_data.csv'),
    ('Show UPMC AD Monthly_codified.RData columns','UPMC_AD','Monthly_codified_fake_data.csv'),
    ('Tell me more about codified_data_monthly.RData in IBD','IBD','codified_data_monthly_fake_data.csv'),
    ('Show fake rows for MGB AD NLP monthly','MGB_AD','NLP_monthly_fake_data.csv'),
])
def test_single_clinical_file_never_expands_to_parent_inventory(client,query,parent,filename):
    r=ask(client,query)
    assert [s['dataset']['id'] for s in r['datasets']]==[parent]
    assert [f['file'] for f in r['datasets'][0]['files']]==[filename]
    assert len(r['datasets'][0]['facts'])<=1 and r['warning'] is None


@pytest.mark.parametrize('query,parent,filename',[
    ('Tell me more about MRCONSO.RRF','ZX_UMLS','MRCONSO.RRF'),
    ('Show kg.csv in PrimeKG v2.1 knowledge graph','ZX_PRIMEKG','kg.csv'),
    ('Tell me more about gene_snp_tissue_alex_cleaned.csv','ZX_EQTL','gene_snp_tissue_alex_cleaned.csv'),
    ('Where is lm_test_dis_gene.jsonl?','ZX_RELATIONS','lm_test_dis_gene.jsonl'),
    ('Show gwas_catalog_v1.0-associations_e109_r2023-04-24.tsv','ZX_GWAS','gwas_catalog_v1.0-associations_e109_r2023-04-24.tsv'),
])
def test_named_reference_file_isolated_with_original_readme_source(client,query,parent,filename):
    r=ask(client,query)
    assert [e['id'] for e in r['resources']]==[parent]
    entry=r['resources'][0]
    assert entry['selected_file_name']==filename
    assert len(entry['blocks'])==1
    assert r['sources'][0]['url']==f'/api/resources/{parent}/readme'
    assert not r['datasets']


@pytest.mark.parametrize('query',[
    'Show Monthly_codified.RData columns',
    'Tell me more about patient_summary.csv',
    'Show deID scores.xlsx columns',
    'Show fake rows for traetment response_for informatics_nodupl_mergedpatient_num_forXin_Feb6.xlsx in MGB IBD',
])
def test_ambiguous_filename_offers_distinct_resolvable_choices(client,query):
    r=ask(client,query)
    assert r['interpretation']=='ambiguous_file' and not r['datasets'] and not r['resources']
    assert len(r['actions'])>=2
    for a in r['actions']:
        chosen=ask(client,a['query'])
        assert chosen['interpretation']!='ambiguous_file'
        assert len(chosen.get('datasets',[]))+len(chosen.get('resources',[]))==1
        if chosen['datasets']: assert len(chosen['datasets'][0]['files'])==1


def test_readme_only_ad_columns_preserve_source_order_and_do_not_invent_raw_headers(client):
    r=ask(client,'Show UPMC AD 2026-04-06_UPMC_survival_outcome.csv columns')
    f=r['datasets'][0]['files'][0]
    assert f['columns']==['patient_num','date_last_code','date_first_code','date_first_cui',
        'date_last_cui','t0','date_first_nh_code','date_first_nh_code_post_t0','date_death']
    assert f['file'] is None
    r=ask(client,'Show UPMC AD raw codified data columns')
    assert r['datasets'][0]['files'][0]['columns']==[]
    assert 'source columns are unnamed' in r['intro']
    assert 'common_ontology_code' in r['answer']


def test_unknown_score_file_is_not_assigned_a_schema_or_fake_rows(client):
    r=ask(client,'Show fake sample rows for Biobank_snp_merged.RDS in MGB IBD')
    f=r['datasets'][0]['files'][0]
    assert f['columns']==[] and f['file'] is None and not f['show_preview']
    assert 'have not been prepared' in r['intro']


def test_unsupported_qualifier_or_execution_does_not_use_exact_file_shortcut(client):
    catalog=client.app.state.catalog
    assert not match_files(catalog,'Run a model on kg.csv',[])
    assert not match_files(catalog,'Show cancer patients in combined_daily.RData in MGB AD',[])


def test_all_registered_fake_files_have_exact_downloadable_headers(client):
    for parent,record in client.app.state.catalog.records.items():
        for f in record['files']:
            r=client.get(f"/api/datasets/{parent}/files/{f['file']}/preview?limit=5")
            assert r.status_code==200
            data=r.json()
            assert data['synthetic'] and data['columns']==f['columns'] and len(data['rows'])==5


@pytest.mark.parametrize('label,parent',[('MGB AD','MGB_AD'),('UPMC AD','UPMC_AD'),('MGB IBD','IBD')])
def test_plain_named_dataset_details_do_not_depend_on_model_routing(client,label,parent):
    async def forbidden(*args,**kwargs):
        pytest.fail('A plain named inventory request should use the saved metadata')
    client.app.state.agent.structured=forbidden
    response=client.post('/api/chat',json={'query':'Tell me more about '+label,'use_llm':True})
    result=response.json()
    assert result['interpretation']=='verified_overview'
    assert [s['dataset']['id'] for s in result['datasets']]==[parent]
    assert result['warning'] is None
