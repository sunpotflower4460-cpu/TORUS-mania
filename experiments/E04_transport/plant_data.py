"""Descriptive reanalysis of the five plant worksheets of Brummer et al.'s supplement v1."""
import argparse
import hashlib
import itertools
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

import numpy as np

from experiments.common import save_summary

HASH="2a5a054cd610e39f0b581bde9595b7696f24a385e7dbb0ece133ef1121fbb6ee"


def records(sheet, strings):
    rows=[]
    for row in ET.fromstring(sheet).iterfind(".//{*}row"):
        values={}
        for c in row.findall("{*}c"):
            raw=c.findtext("{*}v")
            if raw is None:
                continue
            col=re.match(r"[A-Z]+",c.get("r")).group()
            values[col]=strings[int(raw)] if c.get("t")=="s" else raw
        if values:
            rows.append(values)
    header=rows[0]
    return [{header[k]:v for k,v in row.items() if k in header} for row in rows[1:]]


def summarize(rows):
    def key(r,col):
        return (r.get("indv",r.get("id","")),r.get(col))
    nodes=defaultdict(list)
    children=defaultdict(list)
    for row in rows:
        nodes[key(row,"nodeid")].append(row)
        children[key(row,"parent")].append(row)
    pair_ratios=[]
    missing = used = terminals = nonbranch = 0
    for group,items in nodes.items():
        if len(items) != 1:
            missing += 1
            continue
        if items[0].get("n") in (None, "NA"):
            if children[group]:
                missing += 1
            else:
                terminals += 1
            continue
        n=int(float(items[0]["n"]))
        if n<2:
            nonbranch += 1
            continue
        offspring=children[group]
        if len(offspring)!=n:
            missing+=1
            continue
        try:
            diameters=[float(r["diameter"]) for r in [items[0],*offspring]]
        except (ValueError,KeyError):
            missing+=1
            continue
        if min(diameters)<=0:
            missing+=1
            continue
        used+=1
        pair_ratios.extend(min(a,b)/max(a,b) for a,b in itertools.combinations(diameters,2))
    return {"segments":len(rows),"complete_branch_points":used,"missing_or_ambiguous":missing,
            "terminal_without_n":terminals,"other_nonbranch":nonbranch,
            "incident_pairs":len(pair_ratios),"mean_min_over_max":float(np.mean(pair_ratios)),
            "quartiles":np.quantile(pair_ratios,[.25,.5,.75]).tolist()}


def run(book,out):
    if hashlib.sha256(book.read_bytes()).hexdigest()!=HASH:
        raise ValueError("The workbook does not match the registered v1 supplement")
    out.mkdir(parents=True,exist_ok=True)
    results={}
    with ZipFile(book) as archive:
        strings=["".join(e.itertext()) for e in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        for i,name in enumerate(("balsa","pinon","ponderosa","roots","tree_tips"),3):
            sheet=archive.read(f"xl/worksheets/sheet{i}.xml")
            results[name]=summarize(records(sheet,strings))
    # Independently check the reported total numbers of segments in Table 1.
    published=[649,2099,312,1231,914]
    checks={"published_segment_counts": [r["segments"] for r in results.values()]==published}
    save_summary(out,{"source_doi":"10.6084/m9.figshare.13370348.v1","license":"CC BY 4.0",
                      "sha256":HASH,"groups":results,"checks":checks},__file__)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("workbook",type=Path)
    p.add_argument("--out",type=Path,default=Path(__file__).resolve().parents[2]/"research/results/E04/plant")
    args=p.parse_args()
    run(args.workbook,args.out)
