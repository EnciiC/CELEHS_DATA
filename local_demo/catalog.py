"""Read the prepared local catalog and index documentation, never source servers."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from .notes import fake_data_notes
from .document_stats import ibd_date_summaries
from .tracker import load_tracker, tracker_notes
from .readme_resources import prepare_readmes, extra_facts

PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "demo_input"
DATABASE = PROJECT / "runtime" / "catalog.sqlite3"
FOLDERS = ("IBD", "MGB_AD", "UPMC_AD")
LABELS = {"IBD": "MGB IBD", "MGB_AD": "MGB AD", "UPMC_AD": "UPMC AD"}


def english_only(value):
    """Remove appended bilingual annotations in display copies; retain source files."""
    if isinstance(value, str):
        return re.sub(r"(?:[A-Za-z][A-Za-z0-9_-]*)?[\u3400-\u9fff][^|\n]*", "", value).replace(", as confirmed by Enci", "").strip()
    if isinstance(value, list): return [english_only(item) for item in value]
    if isinstance(value, dict): return {key: english_only(item) for key, item in value.items()}
    return value


def original_html(file: Path) -> str:
    """Preserve Word paragraph/table order and basic styles; escape every value."""
    if not file.exists():
        return json.loads(file.with_name('README_original.json').read_text(encoding='utf-8'))['html']
    with zipfile.ZipFile(file) as archive:
        tree = ET.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    w = "{" + ns["w"] + "}"

    def paragraph(node):
        text = english_only("".join(t.text or "" for t in node.findall(".//w:t", ns)))
        if not text: return ""
        style = node.find("w:pPr/w:pStyle", ns)
        name = style.get(w + "val", "").lower() if style is not None else ""
        tag = "h2" if name in {"title", "heading1"} or text in {"MGB", "UPMC", "VA (KDI)"} else "h3" if "heading" in name else "p"
        cls = ' class="doc-path"' if re.match(r"^(?:/|\\\\|[A-Z]:[\\/])", text) else ""
        pieces = re.split(r"((?:/(?:data|n)/|//|\\\\)[^\s,]+)", text)
        rendered = "".join('<code class="doc-inline-path">' + html.escape(part) + '</code>' if i % 2 else html.escape(part) for i, part in enumerate(pieces))
        if node.find("w:pPr/w:numPr", ns) is not None: rendered = "• " + rendered
        if node.find(".//w:rPr/w:b", ns) is not None and len(text) < 160: rendered = "<strong>" + rendered + "</strong>"
        return f"<{tag}{cls}>{rendered}</{tag}>"

    blocks = []
    for node in tree.find("w:body", ns):
        if node.tag == w + "p": blocks.append(paragraph(node))
        elif node.tag == w + "tbl":
            rows, merged = [], {}
            for row in node.findall("w:tr", ns):
                cells, column = [], 0
                before = row.find("w:trPr/w:gridBefore", ns)
                if before is not None:
                    column = int(before.get(w + 'val', '0'))
                    cells.extend({'content':'','colspan':1,'rowspan':1} for _ in range(column))
                for cell in row.findall("w:tc", ns):
                    span = cell.find("w:tcPr/w:gridSpan", ns)
                    width = int(span.get(w + 'val', '1')) if span is not None else 1
                    merge = cell.find("w:tcPr/w:vMerge", ns)
                    continuation = merge is not None and merge.get(w + 'val', 'continue') != 'restart'
                    if continuation and column in merged:
                        merged[column]['rowspan'] += 1
                    else:
                        value = {'content': ''.join(paragraph(p) for p in cell.findall('w:p', ns)), 'colspan': width, 'rowspan': 1}
                        cells.append(value)
                        if merge is not None: merged[column] = value
                        else: merged.pop(column, None)
                    column += width
                rows.append(cells)
            markup = ''.join('<tr>' + ''.join(f'<td colspan="{c["colspan"]}" rowspan="{c["rowspan"]}">{c["content"]}</td>' for c in row) + '</tr>' for row in rows)
            blocks.append('<div class="table-scroll"><table class="document-table">' + markup + '</table></div>')
    return "".join(blocks)


def original_text(file: Path) -> str:
    if not file.exists():
        return json.loads(file.with_name('README_original.json').read_text(encoding='utf-8'))['text']
    with zipfile.ZipFile(file) as archive:
        tree = ET.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in tree.findall(".//w:body//w:p", ns):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns))
        if text.strip():
            paragraphs.append(text.strip())
    return "\n".join(paragraphs)


def site_section(text: str, dataset_id: str) -> str:
    """The shared AD document includes sites outside this demo; index one site."""
    if dataset_id == "IBD":
        return text
    heading = "MGB" if dataset_id == "MGB_AD" else "UPMC"
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        raise ValueError(f"Missing {heading} section in original AD documentation")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip() in {"MGB", "UPMC", "VA (KDI)"}), len(lines))
    return "\n".join(lines[start:end])


def split_chunks(text: str, limit: int = 950) -> list[str]:
    chunks, current = [], ""
    for line in text.splitlines():
        if len(current) + len(line) > limit and current:
            chunks.append(current.strip())
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


class Catalog:
    def __init__(self, root: Path = INPUT, database: Path = DATABASE):
        self.root, self.database = root, database
        self.records: dict[str, dict] = {}
        self.documents: dict[str, dict] = {}
        self.facts: dict[str, list[dict]] = {}
        self.rebuild()

    def connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def rebuild(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        records, documents, facts = {}, {}, {}
        tracker = load_tracker(PROJECT)
        for folder in FOLDERS:
            directory = self.root / folder
            record = english_only(json.loads((directory / "catalog_record.json").read_text(encoding="utf-8")))
            if record["dataset_id"] != folder:
                raise ValueError("Catalog folder and dataset ID differ")
            record["schema"] = english_only(json.loads((directory / "schema.json").read_text(encoding="utf-8")))
            extra_documents = prepare_readmes(record, directory)
            record['original_documents'] = [{
                'kind': 'original', 'label': "Sara's original documentation",
                'description': 'Original team documentation for ' + LABELS[folder] + '.',
                'file': 'README_original.docx' if (directory / 'README_original.docx').exists() else 'README_original.txt',
                'url': f'/api/datasets/{folder}/readme/original',
            }] + [{**{key: doc[key] for key in ('kind', 'label', 'description', 'file')},
                   'url': f"/api/datasets/{folder}/readme/{doc['kind']}"}
                  for doc in record.get('original_readmes', [])]
            record["label"] = LABELS[folder]
            record['tracker_source'] = english_only(tracker.get(folder))
            record['date_summaries'] = (ibd_date_summaries(directory / 'README_original.docx') if (directory / 'README_original.docx').exists()
                else json.loads((directory / 'README_original.json').read_text(encoding='utf-8'))['date_summaries']) if folder == 'IBD' else []
            record["column_descriptions"] = english_only(list(csv.DictReader(
                (directory / "column_dictionary.csv").read_text(encoding="utf-8").splitlines())))
            for file in record["files"]:
                if not file.get("synthetic") or not file["file"].endswith("_fake_data.csv"):
                    raise ValueError("Only explicitly synthetic data files can be served")
                if Path(file["file"]).name != file["file"]:
                    raise ValueError("A registered filename must be a basename")
                with (directory / file["file"]).open(encoding="utf-8", newline="") as handle:
                    rows = csv.DictReader(handle)
                    if rows.fieldnames != file["columns"]:
                        raise ValueError(f"CSV columns differ from schema: {file['file']}")
                    if sum(1 for _ in rows) != file["rows"]:
                        raise ValueError(f"CSV row count differs from metadata: {file['file']}")
            full_original = english_only(original_text(directory / "README_original.docx"))
            documents[folder] = {
                # README.md remains the detailed internal generation/review file.
                # Never expose its review checklist through a public document endpoint.
                "catalog": fake_data_notes(record),
                "synthetic": fake_data_notes(record),
                "original": full_original,
                "original_section": site_section(full_original, folder),
                **extra_documents,
            }
            if record['tracker_source']:
                documents[folder]['tracker'] = tracker_notes(record['tracker_source'])
            records[folder] = record
            facts[folder] = self.build_facts(record, documents[folder])
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, record TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS documents
                  (dataset_id TEXT, kind TEXT, content TEXT, PRIMARY KEY(dataset_id, kind));
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
                  dataset_id UNINDEXED, fact_id UNINDEXED, content, tokenize='unicode61');
                DELETE FROM datasets;
                DELETE FROM documents;
                DELETE FROM chunks;
            """)
            for dataset_id, record in records.items():
                db.execute("INSERT INTO datasets VALUES (?,?)", (dataset_id, json.dumps(record)))
                for kind, content in documents[dataset_id].items():
                    db.execute("INSERT INTO documents VALUES (?,?,?)", (dataset_id, kind, content))
                for fact in facts[dataset_id]:
                    db.execute("INSERT INTO chunks VALUES (?,?,?)",
                               (dataset_id, fact["id"], fact["text"]))
        self.records, self.documents, self.facts = records, documents, facts

    def build_facts(self, r: dict, docs: dict) -> list[dict]:
        dataset_id = r["dataset_id"]
        facts = []

        def add(key, category, text, source="notes"):
            facts.append({"id": f"{dataset_id}:{key}", "dataset_id": dataset_id,
                          "category": category, "text": text,
                          "source": {"kind": source,
                                     "label": "Original README" if source == "original" else "Dataset notes",
                                     "url": f"/api/datasets/{dataset_id}/readme/{source}"}})

        add("overview", "overview", f"{r['label']}: {r['description']}")
        platform = ", ".join(r["storage_platform"])
        suffix = ". There is no O2 copy." if r.get("has_o2_copy") is False else ""
        add("location", "location", f"Storage: {platform}{suffix}")
        add("contact", "contact", f"Contact: {r['contact']}.")
        for i, resource in enumerate(r["resources"]):
            kind = resource["kind"].lower()
            category = "dictionary" if "dictionary" in kind else "processing" if "script" in kind else "file"
            # Keep true source descriptions distinct from synthetic examples.
            text = f"{resource['name']}: {resource.get('description', '')}"
            if resource.get("location"):
                text += f"\nSource location: {resource['location']}"
            if resource.get("alternative_location"):
                text += f"\nAlternative documented path: {resource['alternative_location']}"
            add(f"resource_{i}", category, text, resource.get('source_kind', 'notes'))
            if resource.get('source_kind'):
                facts[-1]['source']['label'] = next(doc['label'] for doc in r['original_documents'] if doc['kind'] == resource['source_kind'])
        for i, dictionary in enumerate(r.get("dictionaries", [])):
            if any(dictionary.get("location") and dictionary.get("location") == item.get("location")
                   for item in r["resources"]):
                continue
            text = f"{dictionary['name']}: {dictionary.get('status', '')}. {dictionary.get('description', '')}"
            if dictionary.get("location"):
                text += f"\nSource location: {dictionary['location']}"
            add(f"dictionary_{i}", "dictionary", text)
        for i, file in enumerate(r["files"]):
            columns = ", ".join(file["columns"])
            text = f"{file['file']} has columns: {columns}. {file['row_meaning']}"
            if file.get("source_r_classes"):
                text += "\nSource R types: " + "; ".join(
                    f"{col}: {typ}" for col, typ in zip(file["columns"], file["source_r_classes"])) + "."
            add(f"schema_{i}", "columns", text)
            fake_patients = file.get("unique_synthetic_patients", r.get("assumptions", {}).get("synthetic_patients"))
            patient_note = f" {fake_patients:,} generated patients." if fake_patients is not None else ""
            add(f"fake_{i}", "fake", f"Synthetic example {file['file']}: {file['rows']:,} generated rows.{patient_note} "
                "It contains no sampled real patient records and is for software demonstration only.")
        if dataset_id == "IBD":
            counts = r["source_counts_from_readme"]
            add("patients", "statistics", f"Sara's original README reports {counts['codified_unique_patients']:,} unique codified patients "
                f"and {counts['nlp_unique_patients']:,} unique NLP patients. The groups overlap; do not add these counts.", "original")
            add("dates", "statistics", "The IBD README contains implausible date extremes. Full date coverage requires review.")
        else:
            add("patients", "statistics", "Patient count for these source files: Not documented. The source preview reports rows, not patients.")
            add("dates", "statistics", "Full monthly cohort date coverage: Not established from the first-row preview. Synthetic date ranges are demo assumptions.")
        for i, summary in enumerate(r.get('date_summaries', [])):
            add(f'date_summary_{i}', 'dates', summary['name'] + ' (' + summary['level'] + '): ' +
                '; '.join(f'{key}: {value}' for key,value in summary['dates'].items()) + '. Reported in README table ' + str(summary['table']) + '; not verified clean monthly-file coverage.', 'original')
        for i, field in enumerate((r.get('tracker_source') or {}).get('fields', [])):
            add(f'tracker_{i}', 'tracker', field['name'] + ': ' + field['value'], 'tracker')
            facts[-1]['source']['label'] = 'Spreadsheet (' + r['tracker_source']['sheet'] + '!' + field['cell'] + ')'
        add("downloads", "downloads", "This demo provides downloads of synthetic CSVs and documentation. "
            "Real source datasets remain on their documented servers; the website does not connect to or download them.")
        add("access", "access", "Specific access approvals and license requirements are not documented in this demo catalog. Confirm access with the contact.")
        add("microbiome", "uncertainty", "Microbiome availability is not documented in the supplied materials. "
            "Confirm this with the contact before treating the dataset as suitable for a study requiring microbiome measurements.")
        for i, text in enumerate(split_chunks(docs["original_section"])):
            digest = hashlib.sha1(text.encode()).hexdigest()[:8]
            add(f"original_{i}_{digest}", "original", text, "original")
        facts.extend(extra_facts(r, docs))
        for doc in r.get('original_readmes', []):
            # Keep each original document independently retrievable and cited.
            for i, text in enumerate(split_chunks(docs[doc['kind']])):
                digest = hashlib.sha1(text.encode()).hexdigest()[:8]
                add(f"original_{doc['kind']}_{i}_{digest}", 'original', text, doc['kind'])
                facts[-1]['source']['label'] = doc['label']
                facts[-1]['format'] = 'markdown'
        return facts

    def summaries(self):
        return [self.summary(r) for r in self.records.values()]

    @staticmethod
    def summary(r):
        return {"id": r["dataset_id"], "name": r["dataset_name"], "label": r["label"],
                "site": r["site"], "description": r["description"],
                "platforms": r["storage_platform"], "contact": r["contact"],
                "fake_files": len(r["files"]), "synthetic_rows": sum(f["rows"] for f in r["files"]),
                'has_tracker':bool(r.get('tracker_source')),
                'original_documents':r.get('original_documents', []),
                'documented_resources':len(r.get('documented_files', []))}

    def find(self, query: str, previous: list[str] | None = None):
        q = query.lower()
        ibd = bool(re.search(r"\bibd\b|inflammatory bowel|crohn|ulcerative|gut|microbiome|炎症性肠|克罗恩|肠道", q))
        ad = bool(re.search(r"\bad\b|alzheimer|dementia|阿尔茨|痴呆", q))
        mgb = bool(re.search(r"\bmgb\b|mass general|massachusetts general", q))
        upmc = bool(re.search(r"\bupmc\b|pittsburgh|匹兹堡", q))
        if re.search(r"\bvinci\b|\bva\b|\bkdi\b|\bms\b|\bra\b|multiple sclerosis|rheumatoid|mimic", q) and not (ibd or ad):
            return []
        candidates = list(self.records)
        explicit = ibd or ad
        if ibd or ad:
            candidates = [i for i in candidates if (ibd and i == "IBD") or (ad and i.endswith("_AD"))]
        if mgb and not upmc:
            candidates = [i for i in candidates if self.records[i]["site"] == "MGB"]
        if upmc and not mgb:
            candidates = [i for i in candidates if self.records[i]["site"] == "UPMC"]
        if explicit:
            return candidates
        if previous and re.search(r"\b(it|its|there|o2|eris|these|those|they|them|their|where|what about|how many|sample|preview|dictionary|columns|monthly|nlp|codified)\b|这些|它们", q):
            return [i for i in previous if i in self.records]
        if re.fullmatch(r'(?:show|list|browse)\s+(?:(?:all|available|current|lab|mgb|upmc)\s+)*datasets?[?.!]*', q.strip()):
            return candidates
        tokens = re.findall(r"[a-z][a-z0-9_]{2,}", q)
        ignored = {"want", "wanted", "see", "show", "tell", "please", "study", "research", "question", "can", "what", "where", "the", "with", "and", "for", "from", "disease", "have", "help", "find", "data", "dataset", "datasets", "available", "currently", "clinical", "ehr", "mgb", "upmc", "using", "would", "like", "there", "does", "any"}
        tokens = [t for t in tokens if t not in ignored][:12]
        if not tokens:
            return []
        expression = " OR ".join('"' + token + '"' for token in tokens)
        with self.connect() as db:
            ids = {row["dataset_id"] for row in db.execute(
                "SELECT DISTINCT dataset_id FROM chunks WHERE chunks MATCH ?", (expression,))}
        return [i for i in candidates if i in ids]

    def retrieve_original(self, query: str, ids: list[str]) -> list[dict]:
        if not ids:
            return []
        ignored = {'where','can','find','want','wanted','study','research','information','analysis','data','dataset','mgb','upmc','the','for','and','what','which','documented'}
        tokens = [t for t in re.findall(r"[a-z][a-z0-9_]{2,}", query.lower()) if t not in ignored][:15]
        if not tokens:
            return []
        expression = " OR ".join('"' + token + '"' for token in tokens)
        with self.connect() as db:
            rows = db.execute("SELECT fact_id, dataset_id FROM chunks WHERE chunks MATCH ? AND fact_id LIKE '%:original_%' ORDER BY rank LIMIT 30",
                              (expression,)).fetchall()
        by_id = {f["id"]: f for i in ids for f in self.facts[i] if f["category"] == "original"}
        selected = []
        for row in rows:
            fact = by_id.get(row["fact_id"])
            if fact and sum(x["dataset_id"] == fact["dataset_id"] for x in selected) < 2:
                if re.search(r'\bapoe\b|genetic', query, re.I):
                    lines = [line for line in fact['text'].splitlines() if re.search(r'apoe|genetic', line, re.I)]
                    if not any('apoe' in line.lower() for line in lines): continue
                    fact = {**fact, 'text':'\n'.join(lines)}
                selected.append(fact)
        return selected

    def downloadable(self, dataset_id: str, filename: str) -> Path:
        record = self.records[dataset_id]
        allowed = {f["file"] for f in record["files"]} | {
            "column_dictionary.csv", "schema.json", "catalog_record.json"} | {
                doc['file'] for doc in record.get('original_documents', [])}
        if filename not in allowed or Path(filename).name != filename:
            raise ValueError("File is not an approved demo download")
        path = (self.root / dataset_id / filename).resolve()
        if path.parent != (self.root / dataset_id).resolve():
            raise ValueError("Path outside dataset folder")
        return path

