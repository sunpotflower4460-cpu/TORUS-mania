"""Aggregate previously frozen bibliographic evidence and calibrate the shape criteria."""
import argparse
import json
import re
from collections import Counter
from math import sqrt
from pathlib import Path

import numpy as np
from experiments.common import save_summary
from experiments.E03_vortex import topology

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "research/results/E08"
KEYWORD = re.compile(r"\b(?:torus|tori|toroidal|hypertorus|vortex[ -]rings?)\b", re.I)


def proportion(k, n):
    return k / n if n else None


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    center = p + z*z/(2*n)
    radius = z*sqrt(p*(1-p)/n + z*z/(4*n*n))
    scale = 1 + z*z/n
    return [max(0., (center-radius)/scale), min(1., (center+radius)/scale)]


def shape_controls():
    axis = np.linspace(-2, 2, 49)
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    # The tree has a lower trunk and two upper diagonal branches joined at the origin.
    branch = np.minimum((x-z)**2, (x+z)**2)/2
    tree = ((np.where(z<0, x*x, branch) + y*y < .19**2) & (abs(z)<1.1))
    values = {"ring": ((np.hypot(x,y)-1)**2 + z*z < .3**2),
              "solid_ball": (x*x+y*y+z*z < 1.2**2), "tree": tree,
              "plane_wave": np.abs(np.cos(2*np.pi*x)), "uniform_flow_vorticity": np.zeros_like(x)}
    controls = {}
    for name, value in values.items():
        result = topology.component_topology(value, .35)
        controls[name] = {"test": "3D voxel topology", "expected": name == "ring", **result}
    # State spaces use the count of independently adjustable periodic coordinates, not tube thickness.
    for periods in (1, 2):
        controls[f"{periods}_independent_phase"] = {
            "test": "product of explicitly supplied circle coordinates",
            "expected": periods == 2, "candidate": periods == 2, "dimension": periods}
    return controls


def aggregate(rows):
    counts = Counter(r['primary'] for r in rows)
    p, n, u = [counts[k] for k in ("positive","negative","unknown")]
    adopted, known = p+n+u, p+n
    return {"ranked": len(rows), "adopted": adopted, "excluded": counts["excluded"],
            "positive": p, "negative": n, "unknown": u, "evaluable": known,
            "documented_per_adopted": proportion(p, adopted),
            "positive_per_evaluable": proportion(p, known),
            "wilson95_evaluable": wilson(p, known),
            "unknown_per_adopted": proportion(u, adopted),
            "bounds_including_unknown": [proportion(p, adopted), proportion(p+u, adopted)],
            "title_keyword_per_adopted": sum(r["keyword"] for r in rows if r["primary"]!="excluded"),
            "computational_domain_counts": dict(Counter(r["computational_domain"] for r in rows
                                                         if r["primary"]!="excluded")),
            "necessity_independently_demonstrated": 0}


def run(out):
    ranking_path = OUT / "ranking.json"
    ranking = json.loads(ranking_path.read_text())
    coding_path = HERE / "coding.json"
    rows = json.loads(coding_path.read_text())
    titles = {(g["domain"], r["rank"]): r for g in ranking for r in g["items"]}
    for r in rows:
        meta = titles[r["domain"],r["rank"]]
        if meta["doi"] != r["doi"]:
            raise ValueError("Coding and frozen ranking disagree")
        r["keyword"] = bool(KEYWORD.search(meta["title"]))
    summaries = {g["domain"]: aggregate([r for r in rows if r["domain"]==g["domain"]])
                 for g in ranking if g["domain"]!="discovery_only"}
    controls = shape_controls()
    negative = [r for r in controls.values() if not r["expected"]]
    checked = [r for r in rows if r["primary"] in ("positive","negative")]
    checks = {"all_ranks_preserved": len(set((r["domain"],r["rank"]) for r in rows)) == len(rows) == 20,
              "complete_query_snapshot": all(len(g["items"]) == 5 for g in ranking),
              "control_reference": all(r["expected"] == r["candidate"] for r in controls.values())}
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, {"domains": summaries, "rows": rows, "controls": controls,
                       "control_false_positive_count": sum(r["candidate"] for r in negative),
                       "control_negative_count": len(negative),
                       "title_vs_evaluable": dict(Counter(r["primary"] + ("_hit" if r["keyword"] else "_miss")
                                                          for r in checked)),
                       "discovery_only_title_hits": sum(bool(KEYWORD.search(r["title"]))
                              for g in ranking if g["domain"]=="discovery_only" for r in g["items"]),
                       "checks": checks}, __file__, coding_path, ranking_path, topology.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    run(parser.parse_args().out)
