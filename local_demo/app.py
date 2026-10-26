from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .agent import Agent
from .catalog import Catalog, PROJECT, INPUT, original_html
from .notes import short_notes
from .presentation import file_views
from .hosting import Hosting, ChatLimits


@asynccontextmanager
async def lifespan(app):
    app.state.hosting = Hosting.from_env()
    app.state.chat_limits = ChatLimits()
    app.state.catalog = Catalog()
    app.state.agent = Agent(app.state.catalog)
    yield


app = FastAPI(title="CELEHS Dataset Demo API", version="0.1.0", lifespan=lifespan,
              docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(Hosting.from_env().hosts))


@app.middleware("http")
async def local_origin(request: Request, call_next):
    hosting = request.app.state.hosting
    if request.method == "POST":
        if request.headers.get("origin") not in hosting.origins | {None}:
            return JSONResponse({"detail": "This API accepts same-origin requests only"}, status_code=403)
        # Bound JSON bodies, including chunked requests, before Pydantic parses them.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 16384:
                return JSONResponse({"detail": "Request is too large"}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    if hosting.public:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


def record(request, dataset_id):
    item = request.app.state.catalog.records.get(dataset_id)
    if item is None: raise HTTPException(404, "Unknown dataset")
    return item


@app.get("/api/health")
async def health(request: Request):
    status = await request.app.state.agent.status()
    return {"status": "ok", "datasets": len(request.app.state.catalog.records), "local_only": not request.app.state.hosting.public,
            "model": status}


@app.get("/docs", include_in_schema=False)
def api_docs():
    # Self-contained local guide; no CDN scripts are needed during the demo.
    return FileResponse(PROJECT / "local_demo" / "static" / "api.html")


@app.get("/api/datasets")
def datasets(request: Request, q: str = ""):
    catalog = request.app.state.catalog
    ids = catalog.find(q) if q.strip() else list(catalog.records)
    return {"datasets": [catalog.summary(catalog.records[i]) for i in ids], "total": len(ids)}


@app.get("/api/datasets/{dataset_id}")
def detail(dataset_id: str, request: Request):
    r = record(request, dataset_id)
    return {**r, "documents": [
        {"kind": "notes", "label": "Dataset notes", "url": f"/api/datasets/{dataset_id}/readme/notes"},
        {"kind": "synthetic", "label": "How the fake data were made", "url": f"/api/datasets/{dataset_id}/readme/synthetic"},
        *r.get('original_documents', []),
        *([{"kind":"tracker", "label":"Spreadsheet entry", "url":f"/api/datasets/{dataset_id}/readme/tracker"}] if r.get('tracker_source') else [])],
        "synthetic_only": True, "file_details": file_views(r, '', 'browse')}


@app.get("/api/datasets/{dataset_id}/readme/{kind}")
def readme(dataset_id: str, kind: str, request: Request, files: str = Query(default='', max_length=1800)):
    r = record(request, dataset_id)
    if kind == 'notes':
        requested = files.split(',') if files else None
        if requested and any(f not in {item['file'] for item in r['files']} for f in requested):
            raise HTTPException(422, 'Unknown file for dataset notes')
        return {'dataset_id': dataset_id, 'kind': kind, 'text': short_notes(r, requested), 'html': None, 'scope_note': None}
    allowed = {"catalog", "synthetic", "original", "original_section", "tracker"} | {
        doc['kind'] for doc in r.get('original_readmes', [])}
    if kind not in allowed or kind not in request.app.state.catalog.documents[dataset_id]:
        raise HTTPException(404, "Unknown document")
    return {"dataset_id": dataset_id, "kind": kind,
            "text": request.app.state.catalog.documents[dataset_id][kind],
            "html": original_html(INPUT / dataset_id / "README_original.docx") if kind == "original" else None,
            "title": next((doc['label'] for doc in r.get('original_documents', []) if doc['kind'] == kind), None),
            "scope_note": "The original AD document also covers other sites; only the selected MGB or UPMC section is indexed for this demo." if dataset_id != "IBD" and kind == "original" else
                'Original project documentation. Reported analyses and results have not been independently verified by this tool.' if kind == 'ibd_project' else
                'Original laboratory documentation. Counts and coverage are reported in this README, not calculated by this tool.' if kind == 'ibd_lab' else None}


@app.get("/api/datasets/{dataset_id}/schema")
def schema(dataset_id: str, request: Request):
    return record(request, dataset_id)["schema"]


@app.get("/api/datasets/{dataset_id}/files/{filename}/preview")
def preview(dataset_id: str, filename: str, request: Request, limit: int = Query(default=10, ge=1, le=50)):
    r = record(request, dataset_id)
    registered = next((f for f in r["files"] if f["file"] == filename), None)
    if not registered: raise HTTPException(404, "Only registered synthetic data files can be previewed")
    path = request.app.state.catalog.downloadable(dataset_id, filename)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= limit: break
    return {"filename": filename, "synthetic": True, "columns": registered["columns"], "rows": rows,
            "total_rows": registered["rows"], "note": "Generated demo records; not real patient data."}


@app.get("/api/datasets/{dataset_id}/download/{filename}")
def download(dataset_id: str, filename: str, request: Request):
    r = record(request, dataset_id)
    try: path = request.app.state.catalog.downloadable(dataset_id, filename)
    except ValueError: raise HTTPException(404, "File is not an approved demo download")
    if filename == 'column_dictionary.csv':
        # Export the same English display copy, not the bilingual source bytes.
        # A UTF-8 BOM also helps Excel recognize punctuation and symbols correctly.
        rows = r['column_descriptions']
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        return Response(output.getvalue().encode('utf-8-sig'), media_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition':'attachment; filename="column_dictionary.csv"'})
    return FileResponse(path, filename=filename)


class Question(BaseModel):
    query: str = Field(min_length=1, max_length=1500)
    previous_dataset_ids: list[str] = Field(default_factory=list, max_length=3)
    use_llm: bool = True
    pending_topic: str | None = Field(default=None, max_length=80)


@app.post("/api/chat")
@app.post("/api/search")
async def chat(question: Question, request: Request):
    query = question.query.strip()
    if not query: raise HTTPException(422, "Enter a question")
    agent = request.app.state.agent
    if request.app.state.hosting.public:
        # Chat can remain source-only during setup; no paid calls until both switches are on.
        use_llm = question.use_llm and bool(agent.cloud and agent.cloud.ready)
        async with request.app.state.chat_limits.slot():
            result = await agent.answer(query, question.previous_dataset_ids, use_llm, question.pending_topic)
        if result.get('engine') == 'local_llm':
            result['engine'] = 'hosted_llm'
        if question.use_llm and not use_llm:
            result['warning'] = 'Hosted chat is paused. This answer uses saved documentation; you can also browse datasets.'
        return result
    return await agent.answer(query, question.previous_dataset_ids, question.use_llm, question.pending_topic)


@app.post("/api/catalog/reload")
def reload_catalog(request: Request):
    if request.app.state.hosting.public:
        raise HTTPException(403, "Update the source repository and redeploy to refresh public documentation")
    request.app.state.catalog.rebuild()
    return {"datasets": request.app.state.catalog.summaries(), "status": "reloaded"}


app.mount("/", StaticFiles(directory=PROJECT / "local_demo" / "static", html=True), name="web")

