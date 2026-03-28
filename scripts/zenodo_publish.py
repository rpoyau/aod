#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import string
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def http_json(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_file(bucket_url: str, path: Path, token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }
    with path.open("rb") as fh:
        req = urllib.request.Request(
            f"{bucket_url}/{urllib.parse.quote(path.name)}",
            data=fh.read(),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))


def load_concept_doi(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        return s
    return ""


def save_concept_doi(path: Path, doi: str) -> None:
    path.write_text(f"{doi}\n", encoding="utf-8")


def render_metadata(template_path: Path, tag: str, repo_url: str) -> dict:
    raw = template_path.read_text(encoding="utf-8")
    rendered = string.Template(raw).safe_substitute(TAG=tag, REPO_URL=repo_url)
    return json.loads(rendered)


def find_latest_version_id(base_url: str, token: str, concept_doi: str) -> int:
    query = urllib.parse.urlencode({"q": f'conceptdoi:"{concept_doi}"', "sort": "mostrecent", "size": 1})
    data = http_json("GET", f"{base_url}/api/records?{query}", token)
    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        raise RuntimeError(f"No Zenodo record found for concept DOI {concept_doi}")
    return int(hits[0]["id"])


def get_record(base_url: str, token: str, record_id: int) -> dict:
    return http_json("GET", f"{base_url}/api/records/{record_id}", token)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True)
    p.add_argument("--metadata", default=str(ROOT / ".zenodo.json"))
    p.add_argument("--doi-file", default=str(ROOT / ".zenodo_doi"))
    p.add_argument("--tag", required=True)
    p.add_argument("--repo-url", required=True)
    p.add_argument("--sandbox", action="store_true")
    p.add_argument("--preview", action="store_true")
    p.add_argument("--token-env", default="ZENODO_TOKEN")
    args = p.parse_args()

    token = os.environ.get(args.token_env, "").strip()
    if not token:
        print(f"Missing token in ${args.token_env}", file=sys.stderr)
        return 2

    base_url = "https://sandbox.zenodo.org" if args.sandbox else "https://zenodo.org"
    bundle = Path(args.bundle).resolve()
    metadata = render_metadata(Path(args.metadata), args.tag, args.repo_url)
    doi_file = Path(args.doi_file).resolve()
    concept_doi = load_concept_doi(doi_file)

    if concept_doi:
        latest_id = find_latest_version_id(base_url, token, concept_doi)
        resp = http_json("POST", f"{base_url}/api/deposit/depositions/{latest_id}/actions/newversion", token)
        latest_draft_url = resp["links"]["latest_draft"]
        draft = http_json("GET", latest_draft_url, token)
    else:
        draft = http_json("POST", f"{base_url}/api/deposit/depositions", token, {})

    deposition_id = draft["id"]
    bucket_url = draft["links"]["bucket"]
    upload_file(bucket_url, bundle, token)
    updated = http_json("PUT", f"{base_url}/api/deposit/depositions/{deposition_id}", token, {"metadata": metadata})

    if args.preview:
        print(json.dumps({
            "mode": "preview",
            "deposit_id": deposition_id,
            "html": updated["links"].get("html") or updated["links"].get("latest_draft_html")
        }, indent=2))
        return 0

    published = http_json("POST", f"{base_url}/api/deposit/depositions/{deposition_id}/actions/publish", token)
    record_id = int(published.get("record_id") or published.get("record", {}).get("id") or deposition_id)
    record = get_record(base_url, token, record_id)
    concept_doi_out = record.get("conceptdoi") or published.get("conceptdoi") or record.get("doi") or published.get("doi", "")
    if concept_doi_out and re.match(r"^10\.(5072|5281)/zenodo\.\d+$", concept_doi_out):
        save_concept_doi(doi_file, concept_doi_out)

    print(json.dumps({
        "mode": "published",
        "deposit_id": deposition_id,
        "record_id": record_id,
        "doi": record.get("doi") or published.get("doi"),
        "conceptdoi": concept_doi_out,
        "record_url": record.get("links", {}).get("self_html") or published.get("record_url") or published.get("doi_url")
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
