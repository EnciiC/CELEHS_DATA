"""Small, question-specific views of documented resources (no generated facts)."""

import re
from .readme_resources import is_lab_query


def scope(query):
    q = query.lower()
    level = "monthly" if "monthly" in q or "calendar month" in q else "daily" if "daily" in q or "day-level" in q else "raw" if "raw" in q else None
    if "raw" in q and ("daily" in q or "day-level" in q) and "monthly" not in q: level = "raw_daily"
    kinds = [kind for kind in ("codified", "nlp") if re.search(rf"\b{kind}\b", q)]
    return level, kinds


def matches(name, level, kinds):
    name = name.lower()
    # Names, not storage paths: a Daily file can live in Monthly_Counts.
    if level == "monthly" and "monthly" not in name: return False
    if level == "daily" and not any(x in name for x in ("daily", "day-level")): return False
    if level == "raw" and not any(x in name for x in ("raw", "mart")): return False
    if level == "raw_daily" and not any(x in name for x in ("raw", "mart", "daily", "day-level")): return False
    if len(kinds) == 1:
        if kinds[0] == "nlp" and "nlp" not in name: return False
        if kinds[0] == "codified" and "nlp" in name: return False
    return True


def dictionaries_for(record, name):
    items = record.get("dictionaries", [])
    if record["dataset_id"] != "IBD": return items
    name = name.lower()
    if "raw" in name or "mart" in name:
        return [d for d in items if "CONCEPT_CD" in d["name"]]
    return [d for d in items if ("nlp" in d["name"].lower()) == ("nlp" in name) and "CONCEPT_CD" not in d["name"]]


def file_views(record, query, purpose):
    if is_lab_query(query) and record.get('documented_files'):
        return [{**item, 'show_columns': purpose in {'columns', 'preview', 'fake'},
                 'show_preview': False, 'show_types': False}
                for item in record['documented_files']]
    level, kinds = scope(query)
    if not level and purpose in {"columns", "preview", "fake", "overview", "dictionary", "research"}:
        level = "monthly"
    files = [f for f in record["files"] if matches(f["file"], level, kinds)]
    result = []
    for file in files:
        resource = next((r for r in record["resources"] if file.get("source_path") and r.get("location") == file["source_path"]), None)
        if resource is None:
            is_nlp = "nlp" in file["file"].lower()
            file_level = "monthly" if "monthly" in file["file"].lower() else "daily" if "daily" in file["file"].lower() else "raw"
            resource = next((r for r in record["resources"] if matches(r["name"], file_level, ["nlp" if is_nlp else "codified"]) and "dictionary" not in r["kind"].lower() and "script" not in r["kind"].lower()), {})
        result.append({"name": resource.get("name", file["file"].replace("_fake_data.csv", "")),
                       "file": file["file"], "columns": file["columns"],
                       "types": file.get("source_r_classes", []),
                       "location": resource.get("location", file.get("source_path")),
                       "alternative_location": resource.get("alternative_location"),
                       "dictionaries": dictionaries_for(record, resource.get("name", file["file"])),
                       "show_columns": purpose in {"columns", "preview"},
                       "show_types": bool(re.search(r"\btype|class", query.lower())),
                       "show_preview": purpose == "preview"})
    if purpose in {'overview', 'research'} and not kinds and level == 'monthly' and not re.search(r'\bcounts?\b|raw|daily', query, re.I):
        result += record.get('documented_files', [])
    return result


def location_views(record, query):
    level, kinds = scope(query)
    if is_lab_query(query) and record.get('documented_files'):
        return record['documented_files']
    # A general location question offers raw, daily and monthly folders by name.
    return [{"name": r["name"], "location": r.get("location"),
             "alternative_location": r.get("alternative_location"), "columns": [],
             "dictionaries": dictionaries_for(record, r["name"]), "show_columns": False}
            for r in record["resources"] if "dictionary" not in r["kind"].lower()
            and "script" not in r["kind"].lower() and matches(r["name"], level, kinds)]


def answer_views(record, query, purpose):
    if purpose == "location": return location_views(record, query)
    if purpose in {"columns", "preview", "overview", "dictionary", "fake", "research"}:
        return file_views(record, query, purpose)
    return []
