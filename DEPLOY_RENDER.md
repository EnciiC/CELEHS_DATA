# Put Dataset Finder online

The repository includes a Render web-service configuration and a Cloudflare Workers AI adapter for `@cf/openai/gpt-oss-20b`. Your local Ollama setup remains the default when `CATALOG_PROVIDER` is unset.

The adapter has automated tests with simulated provider responses. Real Cloudflare inference and the Render deployment must still be checked using your account. JSON output support varies by provider; if Cloudflare rejects the schema or returns invalid JSON, the app reports the failure and uses saved documentation. It does not silently retry, switch models, or claim a hosted answer succeeded.

## 1. Cloudflare

1. Open AI > AI Gateway. Create a gateway named `celehs-data` with authentication enabled. Set **Workers AI Billing** to **Unified billing** to use prepaid Gateway credits.
2. Set a gateway-wide monthly spend limit of **$15**, plus a daily limit of **$1** for this initial demo. Apply the rules to all requests on this gateway, not a different model or provider. Keep automatic credit top-ups **off**.
3. Add credits yourself only after checking the final payment total. Cloudflare charges a 5% credit-purchase fee: $20 of credits costs $21 before any tax. Choose a smaller purchase to stay within a $20 total budget. No separate OpenAI account/key is needed for this model.
4. In Workers AI > Use REST API, create a Cloudflare API token scoped to your account with Workers AI Read permission. Use the provided template if the dashboard offers it. An AI Gateway management-only token will not authorize inference.
5. Keep the token private. Copy your Account ID and token directly into Render's Environment settings in step 2. Do not paste the token into chat, GitHub, source files, or the browser frontend.
6. Keep only usage metadata for cost monitoring, without prompt/response payloads. The app sends `cf-aig-collect-log-payload: false`, while retaining token counts, model, cost and status. This does not eliminate the provider's processing of submitted text. [Logging settings](https://developers.cloudflare.com/ai-gateway/observability/logging/).

The app calls the fixed Cloudflare HTTPS model-in-path endpoint with the named gateway header. Confirm in Gateway Analytics that requests use this gateway and Unified billing during the first live test.

Gateway limits are eventually consistent, so in-flight requests can exceed the threshold. A prepaid balance is not an absolute charge cap either. The $15 limit leaves a buffer; keep top-ups off and monitor initial use. The app's request counters reset on restart and cannot replace these provider-side limits.

Sources: [Workers AI model](https://developers.cloudflare.com/workers-ai/models/gpt-oss-20b/), [REST API and prepaid endpoint](https://developers.cloudflare.com/ai-gateway/usage/rest-api/), [Unified billing](https://developers.cloudflare.com/ai-gateway/features/unified-billing/), [spend limits](https://developers.cloudflare.com/ai-gateway/features/spend-limits/).

## 2. Render

Use [Deploy to Render](https://render.com/deploy?repo=https://github.com/EnciiC/CELEHS_DATA), or choose New > Blueprint and select `EnciiC/CELEHS_DATA`. Allow GitHub access to this repository only when connecting your account. Review the proposed service and confirm the **Free** plan before creating it.

The Blueprint reads `render.yaml` and starts one Python web service. No extra database, disk, or GPU is required. Enter these values privately:

| Environment setting | Value |
| --- | --- |
| `CATALOG_PROVIDER` | `cloudflare` (already set by Blueprint) |
| `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare Account ID |
| `CLOUDFLARE_GATEWAY_ID` | `celehs-data` |
| `CLOUDFLARE_API_TOKEN` | Your private Workers AI token |
| `CATALOG_CHAT_ENABLED` | Leave `false` for the first deployment |
| `CATALOG_CLOUD_LIMITS_CONFIRMED` | Leave `false` until step 1 is complete |

Render supplies `PORT` and `RENDER_EXTERNAL_HOSTNAME`. The application allows only that exact Render hostname, plus local development hosts. If you later add a custom domain, set `CATALOG_PUBLIC_ORIGIN=https://your-domain.example` with no trailing slash, path, or port.

Build command: `pip install -r local_demo/requirements.txt`

Start command: `uvicorn local_demo.app:app --host 0.0.0.0 --port $PORT --workers 1 --no-access-log`

After deployment, open Render's assigned URL and `/api/health`. You should be able to browse all three dataset groups, open original READMEs, and view/download synthetic examples while hosted chat is paused. Health checks never call inference. `configured: true` means required settings exist; it does not mean the token has been verified by Cloudflare.

Source: [Render FastAPI setup](https://render.com/docs/deploy-fastapi), [Blueprint reference](https://render.com/docs/blueprint-spec).

## 3. Enable and test hosted questions

Only after confirming Gateway billing and limits, set both `CATALOG_CLOUD_LIMITS_CONFIRMED=true` and `CATALOG_CHAT_ENABLED=true` in Render and redeploy. This authorizes model calls from public users. Disable chat again by setting `CATALOG_CHAT_ENABLED=false` and redeploying; documentation browsing remains available.

Run this small test list:

- **Is IBD data available on O2?** Expected: no; MGB Windows/SFA and Eris. This lookup can answer without a model call.
- **What IBD data do we have?** Expected: raw/codified/NLP resources and monthly laboratory documentation, with source links.
- **What can we do with IBD data?** Expected: the MAJOR project README and documented aims, not a new analysis.
- **Compare the monthly count columns for MGB AD and UPMC AD.** Expected: documented naming differences, with codified and NLP resources distinguished.
- **Do we have cardiovascular data?** Expected: availability is not documented in these three groups; ask a useful follow-up rather than invent a dataset.
- Open one README and preview/download one fake CSV. These operations should create **no inference requests** in Cloudflare.

After a question that actually used the hosted model, `/api/health` should report `verified: true` and the answer should show **Hosted LLM**. Check Cloudflare Analytics for the correct gateway, model, billing and cost. A warning or **Dataset search** label means a source-only fallback; do not present it as verified hosted inference. Note the model's schema compatibility is not proven until this live test passes.

## Operating limits

- One server worker; at most two active chat requests, eight requests per minute and 200 per rolling day **across all visitors in that process**. A question can make two model calls. Counters reset after a restart or redeploy. Do not add workers or replicas without replacing these counters with shared storage.
- Queries are limited to 1,500 characters; request bodies to 16 KB; output to 2,048 generated tokens per model call. No automatic provider retries.
- Anonymous catalog reload is disabled on the public service. To update documents, update the reviewed files in GitHub and redeploy.
- The selected READMEs, metadata and fake examples are public. Real source servers are never connected to by this service. Queries and relevant documentation go to Cloudflare when hosted chat is enabled; users must not submit patient information.
- Render Free may sleep after inactivity and take about a minute to wake. Its local filesystem is temporary; the documentation index is rebuilt on startup. Keep the source documents in GitHub. Review Render's bandwidth/build allowances separately from the model budget. [Free service details](https://render.com/docs/free).
- No real Cloudflare call or public deployment was required for automated tests. Keep credentials out of test fixtures except clearly fake placeholder values.
