import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_demo.catalog import Catalog
from local_demo.agent import Agent
from local_demo.readme_topics import match_topic, prepare_topics, topic_answer


@pytest.fixture
def catalog(tmp_path):
    return Catalog(database=tmp_path/'catalog.sqlite3')


@pytest.mark.parametrize('query',[
    'Tell me about the IBD registry data',
    'Do we have remission labels at 14 and 52 weeks?',
    'What registry data do we have from Ashwin?',
])
def test_registry_discovery_uses_source_cohorts_not_ehr_counts(catalog,query):
    result=topic_answer(catalog,query,[])
    assert result['interpretation']=='verified_readme_topic'
    assert '461' in result['answer'] and '338' in result['answer']
    assert 'week-14' in result['answer'] and 'week-52' in result['answer']
    assert '56,704' not in result['answer']
    assert len(result['datasets'][0]['files'])==2
    assert all(s['kind']=='ibd_project' for s in result['sources'])
    assert 'Ashwin' not in result['answer']  # Search alias, not a source attribution.


@pytest.mark.parametrize('query,previous',[
    ('How do I link the IBD registry data with EHR?',[]),
    ('How do I connect these with our existing EHR?',['IBD']),
    ('How do I link remission labels to EHR?',[]),
])
def test_registry_linkage_preserves_time_index_mapping_and_sensitivity(catalog,query,previous):
    agent=Agent(catalog)
    async def forbidden(*args,**kwargs):
        pytest.fail('A registered source-section lookup must not call the model')
    agent.structured=forbidden
    result=asyncio.run(agent.answer(query,previous=previous,use_llm=True))
    assert result['warning'] is None and result['interpretation']=='verified_readme_topic'
    assert 'baseline_date' in result['answer']
    assert 'deduplicated mapping' in result['answer']
    assert 'any same-drug occurrence within plus or minus 30 days' in result['answer']
    assert 'earliest same-drug occurrence within plus or minus 30 days' in result['answer']
    assert 'stricter sensitivity cohort' in result['answer']
    assert 'UST/USK and RIS to anti-IL-12/23' in result['answer']
    assert '388' not in result['answer']  # Historical linkage checks stay separate.
    mapping=result['datasets'][0]['files'][0]
    assert mapping['location'].endswith('/EMPI_to_Patient_num_full_mapping.csv')
    assert mapping['columns']==['EMPI','Patient_num']
    assert mapping['file'] is None
    for f in result['datasets'][0]['facts']:
        assert f['text'] in catalog.documents['IBD']['ibd_project']


def test_registry_locations_and_outcomes_are_source_backed(catalog):
    locations=topic_answer(catalog,'Where are the IBD registry files?',[])
    files=locations['datasets'][0]['files']
    assert len(files)==2
    assert files[0]['location'].endswith('traetment response_for informatics_nodupl_mergedpatient_num_forXin_Feb6.xlsx')
    assert files[1]['location'].endswith('MGH_data-LLM_project__EMPI_and_patientnum (2).xlsx')
    assert '338' in files[1]['description'] and '461' not in files[1]['description']
    assert all(f['file'] is None and f['columns']==[] for f in files)
    result=topic_answer(catalog,'What outcomes are defined in the IBD registry?',[])
    assert 'Remission versus no response.' in result['answer']
    assert 'Remission or partial response versus no response.' in result['answer']
    assert '69' in result['answer'] and '97' in result['answer']
    assert '3-month' in result['answer']  # Preserve source table labels.


def test_registry_does_not_invent_samples_or_full_column_dictionary(catalog):
    result=topic_answer(catalog,'Show fake sample rows for the IBD registry',[])
    assert 'Fake sample rows are not available' in result['intro']
    assert all(f['file'] is None for f in result['datasets'][0]['files'])
    result=topic_answer(catalog,'Show IBD registry columns',[])
    assert '`drugsubstudy`' in result['answer'] and '`baseline_date`' in result['answer']
    assert 'Group_Code_Count' not in result['answer'] and 'Rollup_Code' not in result['answer']


def test_registry_assessment_labels_are_not_presented_as_monthly_files(catalog):
    from local_demo.presentation import file_views
    files=file_views(catalog.records['IBD'],'What monthly IBD data do we have?','overview')
    assert len(files)==3 and not any(f.get('topic_id') for f in files)


def test_named_inventory_includes_registry_without_depending_on_model(catalog):
    agent=Agent(catalog)
    async def forbidden(*args,**kwargs):
        pytest.fail('A clear named-dataset inventory should use saved metadata')
    agent.structured=forbidden
    result=asyncio.run(agent.answer('What IBD data do we have?',use_llm=True))
    assert result['warning'] is None and result['interpretation']=='verified_overview'
    assert 'registry remission outcomes' in result['answer']
    assert len(result['datasets'][0]['files'])==5


@pytest.mark.parametrize('query,previous',[
    ('Show UPMC IBD registry data',[]),
    ('How do I link the IBD registry to microbiome data?',[]),
    ('How do I connect these with EHR?',[]),
    ('How do I connect these with EHR?',['MGB_AD']),
    ('Run a remission prediction model using IBD registry data',[]),
])
def test_unconfirmed_source_tasks_and_ambiguous_context_do_not_use_shortcut(catalog,query,previous):
    assert match_topic(catalog,query,previous) is None


def test_registration_reuses_another_project_without_ibd_branches():
    document='# Example project\n\n## Outcome records\n\nDocumented labels from follow-up visits.\n\nCohort file: `//example/project/outcomes.csv`\n\n## Joining records\n\n1. Match the project identifier.\n2. Use the documented index visit.\n'
    record={'dataset_id':'EXAMPLE','dataset_name':'Example project','label':'Example project',
            'resources':[],'documented_files':[],
            'original_readmes':[{'kind':'project_source','label':'Example project README','file':'PROJECT.md'}],
            'readme_topics':[{'id':'outcomes','name':'Example follow-up labels','readme_kind':'project_source',
                              'aliases':['follow-up labels'],'overview':{'heading':'Outcome records','paragraphs':1},
                              'files_section':'Outcome records','views':{'linkage':[{'heading':'Joining records'}]}}]}
    prepare_topics(record,{'project_source':document})
    fake_catalog=SimpleNamespace(records={'EXAMPLE':record},summary=lambda r:{'id':r['dataset_id'],'label':r['label']})
    result=topic_answer(fake_catalog,'How do I link Example follow-up labels?',[])
    assert 'Match the project identifier' in result['answer']
    assert result['sources'][0]['kind']=='project_source'
    assert record['documented_files'][0]['location']=='//example/project/outcomes.csv'


def test_missing_registered_section_fails_instead_of_filling_a_guess():
    record={'readme_topics':[{'id':'labels','readme_kind':'source','overview':{'heading':'Missing'}}]}
    with pytest.raises(ValueError,match='Missing README section'):
        prepare_topics(record,{'source':'# Existing README'})
