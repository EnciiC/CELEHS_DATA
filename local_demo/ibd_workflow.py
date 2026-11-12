"""Answer practical IBD cohort and processing questions from the workflow guide."""

import re

from .readme_resources import fact, section, source


COHORT = 'Select the historical MAJOR cohort'
BUILD = 'Build and save the derived files'
LINK = 'Link registry treatment outcomes to EHR'

QUESTIONS = {
    COHORT: 'How do I filter and select eligible IBD patients?',
    BUILD: 'How do I build and save derived IBD data?',
    LINK: 'Show the IBD registry-to-EHR linkage step by step.',
}


def ibd_workflow_answer(catalog, query, previous):
    record = catalog.records.get('IBD')
    guide = catalog.documents.get('IBD', {}).get('ibd_workflow')
    q = query.lower()
    explicit = re.search(r'\bibd\b|inflammatory bowel|\bmajor\b', q)
    if not (record and guide and (explicit or previous == ['IBD'])):
        return None
    if re.search(r'\b(?:upmc|vinci|kdi|ad|alzheimer|ms|multiple sclerosis|endoscopy agent)\b', q):
        return None
    linkage = re.search(r'\blink\w*\b|\bmatch\w*\b|\bjoin\b|align|connect', q)
    how = re.search(r'\bhow\b|\bsteps?\b|step.by.step|workflow|pipeline', q)
    if linkage and how and 'registry' in q and 'ehr' in q and re.search(r'step|workflow|pipeline', q):
        heading = LINK
    elif re.search(r'\bfilter\w*\b|eligib|\bvalid\b|exclusion|inclusion|cohort flow|55[ ,]?651', q) or (
        how and re.search(r'\b(?:select|start|build|construct|define)\b', q) and 'cohort' in q
    ):
        heading = COHORT
    elif re.search(r'\bderived\b', q) and (
        how or re.search(r'\b(?:make|build|create|save|process|produce|scripts?|where)\b', q)
    ):
        heading = BUILD
    elif 'more_sensitivity' in q or (re.search(r'\br scripts?\b', q) and re.search(r'cohort|filter|process', q)):
        heading = BUILD
    else:
        return None
    steps = section(guide, heading)
    if heading == COHORT:
        steps += '\n\n' + section(guide, 'R scripts and contact')
    citation = source(record, 'ibd_workflow', heading)
    evidence = fact(record, 'ibd_workflow_answer', 'processing', steps, 'ibd_workflow', heading, True)
    actions = [{'label': other, 'query': question} for other, question in QUESTIONS.items() if other != heading]
    actions.append({'label': 'Read the derived data guide', 'document': {'dataset_id': 'IBD', 'kind': 'ibd_workflow'}})
    return {'query': query, 'engine': 'catalog', 'model': None, 'intent': 'ibd_workflow',
            'interpretation': 'verified_ibd_workflow', 'intro': heading, 'answer': heading + '\n\n' + steps,
            'datasets': [{'dataset': catalog.summary(record), 'facts': [evidence], 'files': [],
                          'dictionaries': [], 'offer_preview': False}],
            'sources': [citation], 'context_dataset_ids': ['IBD'], 'pending_topic': None,
            'warning': None, 'compact': False, 'actions': actions, 'elapsed_seconds': 0}
