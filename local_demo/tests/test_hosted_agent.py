import asyncio
import json

import httpx

from local_demo.agent import Agent
from local_demo.catalog import Catalog


def test_hosted_agent_uses_validated_evidence_and_preserves_local_default(monkeypatch):
    for key, value in {'CATALOG_PROVIDER': 'cloudflare', 'CATALOG_CHAT_ENABLED': 'true',
                       'CATALOG_CLOUD_LIMITS_CONFIRMED': 'true', 'CLOUDFLARE_ACCOUNT_ID': 'a' * 32,
                       'CLOUDFLARE_GATEWAY_ID': 'celehs-data', 'CLOUDFLARE_API_TOKEN': 'test-only'}.items():
        monkeypatch.setenv(key, value)
    calls = []
    async def post(self, url, **kwargs):
        context = json.loads(kwargs['json']['messages'][1]['content'])
        calls.append(context)
        fact_ids = [f['id'] for f in context['evidence']
                    if f['dataset_id'] == 'UPMC_AD' and f['category'] == 'columns'][:1]
        if 'candidates' in context:
            value = {'selections': [{'dataset_id': 'UPMC_AD', 'fact_ids': fact_ids}]}
        else:
            value = {'mode': 'retrieve', 'dataset_ids': ['UPMC_AD'], 'intent': 'columns',
                     'subject': 'UPMC AD monthly columns', 'clarification': '', 'short_answer': '',
                     'evidence_ids': fact_ids}
        return httpx.Response(200, json={'success': True, 'result': {'response': value}},
                              request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    agent = Agent(Catalog())
    result = asyncio.run(agent.answer('Show UPMC AD monthly columns'))
    assert len(calls) == 2 and result['warning'] is None
    assert result['model'] == '@cf/openai/gpt-oss-20b'
    text = json.dumps(result)
    assert 'feature_id' in text and 'Group_Code_Count' in text
    assert agent.cloud.last_success
    monkeypatch.delenv('CATALOG_PROVIDER')
    local = Agent(agent.catalog)
    assert local.cloud is None and local.model == 'celehs-catalog'
