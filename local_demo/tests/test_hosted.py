import asyncio
import importlib
import json

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from local_demo.hosted import CloudflareModel, MODEL, parse_result
from local_demo.hosting import ChatLimits, Hosting


@pytest.fixture
def cloud_env(monkeypatch):
    values = {'CATALOG_PROVIDER': 'cloudflare', 'CATALOG_CHAT_ENABLED': 'true',
              'CATALOG_CLOUD_LIMITS_CONFIRMED': 'true', 'CLOUDFLARE_ACCOUNT_ID': 'a' * 32,
              'CLOUDFLARE_API_TOKEN': 'unit-test-secret-not-a-real-token',
              'CLOUDFLARE_GATEWAY_ID': 'celehs-data', 'RENDER_EXTERNAL_HOSTNAME': 'celehs-data.onrender.com'}
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv('CATALOG_PUBLIC_ORIGIN', raising=False)
    return values


SCHEMA = {'type': 'object', 'properties': {'ids': {'type': 'array', 'items': {'enum': ['IBD']}}},
          'required': ['ids'], 'additionalProperties': False}


def test_cloud_status_never_calls_network(cloud_env, monkeypatch):
    async def fail(*args, **kwargs):
        raise AssertionError('Health must not invoke inference')
    monkeypatch.setattr(httpx.AsyncClient, 'post', fail)
    monkeypatch.setattr(httpx.AsyncClient, 'get', fail)
    status = CloudflareModel().status()
    assert status['enabled'] and not status['verified'] and not status['reachable']
    assert not any(cloud_env['CLOUDFLARE_API_TOKEN'] in str(v) for v in status.values())
    assert 'account' not in status and 'endpoint' not in status


def test_cloud_payload_gateway_billing_and_validation(cloud_env, monkeypatch):
    calls = []
    async def post(self, url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json={'success': True, 'result': {'response': {'ids': ['IBD']}}},
                              request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    model = CloudflareModel()
    assert asyncio.run(model.structured('Select documented IDs.', {'question': 'IBD'}, SCHEMA)) == {'ids': ['IBD']}
    assert model.status()['verified']
    assert len(calls) == 1
    url, request = calls[0]
    assert url.endswith('/ai/run/' + MODEL)
    assert request['headers']['cf-aig-gateway-id'] == 'celehs-data'
    assert request['headers']['cf-aig-collect-log-payload'] == 'false'
    assert request['headers']['cf-aig-max-attempts'] == '1'
    assert request['headers']['Authorization'] == 'Bearer ' + cloud_env['CLOUDFLARE_API_TOKEN']
    assert request['json']['max_tokens'] == 2048 and request['json']['stream'] is False
    assert request['json']['response_format']['json_schema'] == SCHEMA


@pytest.mark.parametrize('setting,value', [('CATALOG_CHAT_ENABLED', 'false'),
    ('CATALOG_CLOUD_LIMITS_CONFIRMED', 'false'), ('CLOUDFLARE_GATEWAY_ID', ''),
    ('CLOUDFLARE_ACCOUNT_ID', '../bad'), ('CLOUDFLARE_API_TOKEN', '')])
def test_missing_config_or_switch_blocks_inference(cloud_env, monkeypatch, setting, value):
    monkeypatch.setenv(setting, value)
    async def fail(*args, **kwargs):
        raise AssertionError('Must not make a paid call')
    monkeypatch.setattr(httpx.AsyncClient, 'post', fail)
    model = CloudflareModel()
    assert not model.ready
    with pytest.raises(ValueError, match='not enabled'):
        asyncio.run(model.structured('system', {}, SCHEMA))


@pytest.mark.parametrize('payload,status', [
    ({'success': True, 'result': {'response': {'ids': ['invented-dataset']}}}, 200),
    ({'success': True, 'result': {'response': {'ids': ['IBD'], 'extra': 'unsafe'}}}, 200),
    ({'success': True, 'result': {'response': 'not JSON'}}, 200),
    ({'success': True, 'result': {'status': 'incomplete', 'response': {'ids': ['IBD']}}}, 200),
    ({'success': False, 'errors': [{'message': 'secret-provider-error'}]}, 200),
    ({'error': 'secret-provider-error'}, 429),
    ({'error': 'secret-provider-error'}, 401)])
def test_invalid_output_and_errors_no_retry_no_leak(cloud_env, monkeypatch, payload, status):
    calls = []
    async def post(self, url, **kwargs):
        calls.append(url)
        return httpx.Response(status, json=payload, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    model = CloudflareModel()
    with pytest.raises(ValueError) as error:
        asyncio.run(model.structured('system', {}, SCHEMA))
    assert len(calls) == 1 and not model.status()['verified']
    assert 'secret' not in str(error.value) and 'cloudflare.com' not in str(error.value)


def test_responses_style_uses_assistant_not_reasoning():
    result = {'output': [{'type': 'reasoning', 'summary': [{'text': 'ignore me'}]},
                        {'type': 'message', 'role': 'assistant', 'content': [
                            {'type': 'output_text', 'text': '{"ids":["IBD"]}'}]}]}
    assert parse_result(result) == {'ids': ['IBD']}


@pytest.mark.parametrize('origin', ['http://example.org', 'https://example.org/path',
                                  'https://user:secret@example.org', 'https://example.org?x=y'])
def test_public_origin_requires_clean_https_origin(cloud_env, monkeypatch, origin):
    monkeypatch.setenv('CATALOG_PUBLIC_ORIGIN', origin)
    with pytest.raises(ValueError):
        Hosting.from_env()


def test_request_limits_and_slot_release():
    async def check():
        limits = ChatLimits(per_minute=3, per_day=2, concurrent=1)
        async with limits.slot():
            with pytest.raises(HTTPException) as err:
                async with limits.slot():
                    pass
            assert err.value.status_code == 429
        assert limits.active == 0
        async with limits.slot():
            pass
        with pytest.raises(HTTPException):
            async with limits.slot():
                pass
    asyncio.run(check())


def test_hosted_app_browsing_paused_chat_and_security(cloud_env, monkeypatch):
    monkeypatch.setenv('CATALOG_CHAT_ENABLED', 'false')
    async def fail(*args, **kwargs):
        raise AssertionError('Browsing or paused chat must not invoke inference')
    monkeypatch.setattr(httpx.AsyncClient, 'post', fail)
    monkeypatch.setattr(httpx.AsyncClient, 'get', fail)
    module = importlib.import_module('local_demo.app')
    # Isolated app with public settings, then restore normal module globals.
    original_app = module.app
    importlib.reload(module)
    try:
        with TestClient(module.app, base_url='https://celehs-data.onrender.com') as client:
            health = client.get('/api/health')
            assert health.status_code == 200 and health.json()['local_only'] is False
            assert health.json()['model']['enabled'] is False
            assert 'unit-test-secret' not in health.text
            assert "frame-ancestors 'none'" in health.headers['content-security-policy']
            for path in ['/', '/docs', '/api/datasets', '/api/datasets/IBD/readme/ibd_project',
                         '/api/datasets/UPMC_AD/schema',
                         '/api/datasets/UPMC_AD/files/Monthly_codified_fake_data.csv/preview',
                         '/api/datasets/IBD/download/IBD_LAB_MONTHLY_README.md']:
                assert client.get(path).status_code == 200
            result = client.post('/api/chat', headers={'Origin': 'https://celehs-data.onrender.com'},
                                 json={'query': 'Is IBD data available on O2?'})
            assert result.status_code == 200 and 'No' in result.json()['answer']
            assert 'paused' in result.json()['warning']
            assert client.post('/api/catalog/reload').status_code == 403
            assert client.post('/api/chat', headers={'Origin': 'https://evil.example'}, json={'query': 'Hi'}).status_code == 403
            assert client.get('/api/health', headers={'Host': 'evil.onrender.com'}).status_code == 400
            assert client.post('/api/chat', content=b'x' * 16385).status_code == 413
            assert client.post('/api/chat', json={'query': 'x' * 1501}).status_code == 422
            client.app.state.chat_limits = ChatLimits(per_day=0)
            limited = client.post('/api/chat', json={'query': 'Hi'})
            assert limited.status_code == 429 and limited.headers['retry-after'] == '60'
    finally:
        module.app = original_app
