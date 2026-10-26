"""Run actual local-model acceptance questions and save a reviewable report."""

import asyncio
import argparse
import json
from pathlib import Path

import httpx

PROJECT = Path(__file__).resolve().parents[1]
CASES = [
    ('IBD location', 'I wanted to see IBD data, guide me and let me know where I can find it', {'IBD'}, ['no O2 copy', 'IBD monthly codified counts', 'IBD monthly NLP counts']),
    ('AD inventory', 'I wanted to see AD, what we have now', {'MGB_AD','UPMC_AD'}, ['MGB AD', 'UPMC AD', 'Storage: O2', 'Raw and daily-level UPMC AD']),
    ('UPMC schemas', 'Show UPMC AD monthly column names and their types', {'UPMC_AD'}, ['Group_Code_Count', 'feature_id', 'integer64']),
    ('AD comparison', 'Compare the monthly count columns for MGB AD and UPMC AD', {'MGB_AD','UPMC_AD'}, ['Group_Code_Count', 'Group_Code', 'feature_id']),
    ('Microbiome uncertainty', 'I want to study EHR data and the gut microbiome. What is documented?', None, ['microbiome']),
    ('UPMC raw availability', 'Where can I find raw and daily UPMC AD data?', {'UPMC_AD'}, ['raw', 'daily']),
    ('IBD patient counts', 'What is the patient count for IBD?', {'IBD'}, ['56,704', '55,436', 'overlap']),
    ('AD patient count uncertainty', 'What is the patient count for AD?', {'MGB_AD','UPMC_AD'}, ['Not documented', 'rows, not patients']),
    ('Unknown resource', 'Where can I find VINCI heart failure data?', set(), ['VINCI', "can't confirm"]),
    ('Original README retrieval', 'Where can I find MGB AD genetic or APOE data?', {'MGB_AD'}, ['APOE_SNPs.csv']),
    ('Synthetic patient counts', 'How many patients and rows are in the UPMC AD fake data?', {'UPMC_AD'}, ['200 generated patients', '1,000 generated rows']),
    ('Short IBD monthly structure', 'Can you show me what a IBD monthly count data look like', {'IBD'}, ['EMPI, Patient_num, month, year, Rollup_Code, N', 'EMPI, month, year, CUI, N, Patient_num']),
    ('IBD NLP dictionary only', 'Where is the IBD monthly NLP dictionary?', {'IBD'}, ['NLP dictionary']),
    ('MGB AD NLP folder', 'Where can I find MGB AD monthly NLP?', {'MGB_AD'}, ['Storage: O2', 'NLP monthly']),
    ('Greeting', 'hi', set(), ['Hi!', 'What would you like to explore']),
    ('RA next steps', 'I want to study rheumatoid arthritis using MGB data. What is available?', set(), ['rheumatoid', "can't confirm"]),
    ('Help', 'What can you do?', set(), ['find file locations', 'fake sample rows']),
    ('IBD O2 direct answer', 'Is IBD data available on O2?', {'IBD'}, ['No.', 'MGB Windows/SFA and Eris', 'not O2']),
    ('IBD O2 find wording', 'Can we find IBD data on O2', {'IBD'}, ['No.', 'MGB Windows/SFA and Eris', 'not O2']),
    ('AD O2 find wording', 'Can we find AD data on O2?', {'MGB_AD','UPMC_AD'}, ['Yes.', 'stored on O2']),
    ('AD O2 direct answer', 'Is AD data available on O2?', {'MGB_AD','UPMC_AD'}, ['Yes.', 'stored on O2']),
    ('Undocumented Eris copy', 'Is UPMC AD stored on Eris?', {'UPMC_AD'}, ['O2', 'A copy on Eris is not documented']),
    ('Cardiovascular availability', 'do we have cardiovascular data?', set(), ['cardiovascular', "can't confirm"]),
    ('Renal availability', 'Do we have kidney disease data from MGB?', set(), ['kidney', "can't confirm"]),
    ('Oncology availability', 'Do we have oncology data?', set(), ['oncology', "can't confirm"]),
    ('Respiratory availability', 'Do we have respiratory datasets from UPMC?', set(), ['respiratory', "can't confirm"]),
    ('Diabetes availability', 'Is diabetes data available on O2?', set(), ['diabetes', "can't confirm"]),
    ('Simple monthly explanation', 'What does one monthly count row mean?', None, ['patient','month','count']),
    ('Held-out psoriasis topic', 'Do we have psoriasis data?', set(), ['psoriasis', "can't confirm"]),
    ('Cardiovascular followup', 'What about monthly counts?', set(), ['cardiovascular', "can't confirm"]),
    ('IBD reported date distribution', 'Do we know a time distribution for IBD data', {'IBD'}, ['2009-09-18','2015-07-25','2019-06-14','2015-07-06','2019-07-23','2022-08-27','implausible']),
    ('IBD spreadsheet entry', 'Show the IBD spreadsheet entry', {'IBD'}, ['56,704','55,436','1840-12-31','6466-05-01']),
    ('IBD research file recommendation', 'I want to study monthly codified and NLP feature counts in the MGB IBD cohort. Which files should I start with?', {'IBD'}, ['IBD monthly codified counts','IBD monthly NLP counts']),
    ('Short APOE answer', 'Where can I find MGB AD APOE information for a genetic analysis?', {'MGB_AD'}, ['APOE_SNPs.csv']),
    ('Synthetic clinical limit', 'Use the fake IBD rows to tell me which treatment is most effective.', set(), ['cannot','clinical conclusions']),
    ('Monthly medication date precision', 'Can the IBD monthly counts identify exact medication start and stop dates?', set(), ['not exact medication start or stop dates','validated treatment-event definitions']),
]


async def main(only=None):
    output = PROJECT / 'runtime' / 'acceptance_results.json'
    results = json.loads(output.read_text(encoding='utf-8')) if only and output.exists() else []
    cases = [case for case in CASES if not only or case[0] in only]
    if not cases: raise SystemExit('No matching test labels')
    async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
        for label, query, expected_ids, phrases in cases:
            body = {'query':query}
            if label == 'Cardiovascular followup': body['pending_topic'] = 'query:cardiovascular data'
            response = await client.post('http://127.0.0.1:8000/api/chat', json=body)
            response.raise_for_status()
            answer = response.json()
            actual = {item['dataset']['id'] for item in answer['datasets']}
            failures = []
            if expected_ids is not None and actual != expected_ids: failures.append(f'Expected {sorted(expected_ids)}, got {sorted(actual)}')
            for phrase in phrases:
                if phrase.lower() not in answer['answer'].lower(): failures.append('Missing: '+phrase)
            if label == 'Short IBD monthly structure':
                if len(answer['answer']) > 400: failures.append('Monthly response is too long')
                if any(word in answer['answer'] for word in ('CONCEPT_CD', 'Storage:', 'Source location', 'Raw codified')):
                    failures.append('Unrequested details in monthly response')
                if len(answer['datasets'][0]['files']) != 2: failures.append('Expected exactly two monthly files')
            if label == 'IBD NLP dictionary only' and 'CONCEPT_CD' in json.dumps(answer['datasets']):
                failures.append('Unrelated raw lookup in NLP dictionary result')
            if label == 'MGB AD NLP folder':
                files = answer['datasets'][0]['files']
                if len(files) != 1 or not files[0]['location'].endswith('/Monthly_Counts/MGB/NLP/'):
                    failures.append('Expected the complete monthly NLP folder')
                if '1_1501' in json.dumps(answer['datasets']): failures.append('A single NLP batch was recommended instead of the folder')
            if label in {'IBD O2 direct answer', 'IBD O2 find wording', 'AD O2 find wording', 'AD O2 direct answer', 'Undocumented Eris copy'}:
                if not answer.get('compact') or len(answer['answer'].split()) > 45:
                    failures.append('Storage answer is not short and direct')
                if any(s['files'] for s in answer['datasets']): failures.append('Unrequested file inventory')
            if expected_ids:
                if answer['intent'] == 'storage':
                    if answer['interpretation'] != 'verified_storage' or answer['warning'] or not answer['sources']:
                        failures.append('Expected verified, source-backed storage facts without a model error')
                elif answer['engine'] != 'local_llm': failures.append('Local LLM did not produce a valid selection')
            if label in {'Greeting', 'Help'}:
                if answer['engine'] != 'guide' or not answer.get('actions'): failures.append('Expected conversational guidance and follow-up choices')
            if label in {'RA next steps','Unknown resource','Cardiovascular availability','Renal availability','Oncology availability','Respiratory availability','Diabetes availability','Held-out psoriasis topic','Cardiovascular followup'}:
                if answer['engine'] != 'local_llm' or answer.get('interpretation') != 'not_documented' or not answer.get('actions'):
                    failures.append('Expected local-model interpretation and an honest missing-documentation answer')
                if answer['datasets'] or answer['sources']: failures.append('Unrelated datasets were substituted')
            if label == 'Simple monthly explanation':
                if answer['engine'] != 'local_llm' or answer.get('interpretation') != 'explain' or not answer.get('compact'):
                    failures.append('Expected a model-written, source-backed short explanation')
                if not answer['sources'] or len(answer['answer'].split()) > 100: failures.append('Explanation lacks sources or is too long')
            if label == 'IBD reported date distribution':
                view = answer['datasets'][0].get('date_summary')
                if answer['intent'] != 'dates' or not view or len(view['rows']) != 5:
                    failures.append('Expected reported date table, not a generic overview')
                if any(s['files'] for s in answer['datasets']): failures.append('Unrequested fake file inventory in date answer')
            if label == 'Short APOE answer':
                if len(answer['answer']) > 500 or 'komap_pred_imputed' in answer['answer']:
                    failures.append('Unrelated README text in APOE answer')
            if label == 'AD comparison':
                comparison = answer.get('comparison')
                if not comparison or 'column names differ' not in comparison['summary']:
                    failures.append('Missing comparison conclusion')
                elif comparison['details'] != [
                    'Codified: MGB AD uses `Group_Code` and `N`; UPMC AD uses `feature_id` and `Group_Code_Count`.',
                    'NLP: MGB AD uses `cui` and `N`; UPMC AD uses `feature_id` and `N`.']:
                    failures.append('Codified/NLP column differences are conflated')
            if label == 'Synthetic clinical limit' and answer['intent'] != 'synthetic_limit':
                failures.append('Synthetic clinical misuse must be stopped explicitly')
            for section in answer['datasets']:
                for fact in section['facts']:
                    if not fact['id'].startswith(section['dataset']['id'] + ':'): failures.append('Cross-dataset evidence')
            results = [r for r in results if r['test'] != label]
            results.append({'test':label,'passed':not failures,'failures':failures,'response':answer})
            print(f"{'PASS' if not failures else 'FAIL'}: {label} ({answer['elapsed_seconds']}s)", flush=True)
    order = {case[0]: i for i, case in enumerate(CASES)}
    results.sort(key=lambda r: order.get(r['test'], len(order)))
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['# Local demo acceptance run', '', f"Passed: {sum(r['passed'] for r in results)} / {len(results)}", '',
             'These questions evaluate retrieval and evidence selection. No model fine-tuning was performed.', '']
    for item in results:
        lines += ['## '+item['test'], '', 'Question: '+item['response']['query'], '',
                  'Result: '+('PASS' if item['passed'] else 'FAIL'),
                  'Engine: '+item['response']['engine'], '', item['response']['answer'], '']
        if item['failures']: lines += ['Failures: '+ '; '.join(item['failures']), '']
    (PROJECT/'local_demo'/'DEMO_TEST_RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    if not all(r['passed'] for r in results): raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', action='append', help='Run selected test labels, retaining other completed results')
    asyncio.run(main(parser.parse_args().only))

