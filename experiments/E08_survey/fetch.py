"""Freeze Crossref rankings. Save public bibliographic fields; keep response text local."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUERIES = {"fluid": "starting jet", "plant": "leaf venation",
           "phase": "coupled oscillators", "space": "cosmic topology", "discovery_only": "toroidal vortex"}


def fetch(destination):
    raw = ROOT / "data/raw/E08"
    raw.mkdir(parents=True, exist_ok=True)
    records = []
    for domain, term in QUERIES.items():
        params = {"query.title": term, "filter": "from-pub-date:2010-01-01,until-pub-date:2024-12-31,type:journal-article",
                  "rows": 5, "sort": "score", "order": "desc"}
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
        entry = {"domain": domain, "query_url": url, "items": []}
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                payload = response.read()
            (raw / (domain + ".json")).write_bytes(payload)
            entry["sha256"] = hashlib.sha256(payload).hexdigest()
            for rank, work in enumerate(json.loads(payload)["message"]["items"], 1):
                entry["items"].append({"rank": rank, "doi": work["DOI"].lower(), "title": work["title"][0],
                                      "published": work["published"]["date-parts"][0],
                                      "has_abstract": bool(work.get("abstract"))})
        except (OSError, ValueError) as error:
            entry["error"] = str(error)
        records.append(entry)
        time.sleep(3)
    destination.parent.mkdir(exist_ok=True, parents=True)
    destination.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New snapshot path (keeps original rankings intact)")
    args = parser.parse_args()
    if args.destination.exists():
        parser.error("Choose a new snapshot path")
    fetch(args.destination)
