"""Compare curving return candidates with a second reconstruction of the same observations."""

import csv
import json
from collections import defaultdict
from zipfile import ZipFile

import numpy as np
from numcodecs import Blosc
from scipy.spatial import cKDTree

from experiments import embryo_history_sources as sources
from experiments.common import save_summary
from experiments.E62_cell_returns import run as primary
from experiments.E65_crosscheck_returns import archive as reconstruction

SHIFTS = (-30, 0, 30)
CRITERIA = {"primary": (3, 2), "relaxed": (5, 1)}


def requests(original_path, candidates, n_frames):
    query = defaultdict(list)
    for index, item in enumerate(candidates):
        xyz = original_path(index)
        for offset in SHIFTS:
            start = item["start_frame"] + offset
            if start >= 0 and start + len(xyz) <= n_frames:
                for order, point in enumerate(xyz):
                    query[start + order].append((index, offset, order, point))
    return query


def frame_query(archive, stem, needed, stem_size, points_to_track, reverse, indices):
    encoded = archive.read(f"points/{stem}.0")
    block = np.frombuffer(Blosc().decode(encoded), dtype="<f4").reshape(-1, 3)
    mapped = np.flatnonzero(points_to_track[stem * stem_size : (stem + 1) * stem_size])
    rows = block[mapped, ::-1]
    if not needed:
        return rows, []
    labels = indices[reverse[stem * stem_size + mapped]] + 1
    distances, matches = cKDTree(rows).query(
        np.array([task[3] for task in needed]), k=2
    )
    details = []
    for task, (distance, competitor), (match, _) in zip(
        needed, distances, matches, strict=True
    ):
        details.append(
            (
                *task[:3],
                distance,
                competitor - distance,
                int(labels[match]),
                rows[match],
            )
        )
    return rows, details


def match_requests(raw, queries, alignment_frames, n_frames):
    answers = defaultdict(list)
    with ZipFile(sources.source(raw, reconstruction.ARCHIVE)) as bundle:
        shape = json.loads(bundle.read("points/.zarray"))["shape"]
        metadata = json.loads(bundle.read("points/.zattrs"))
        if shape[0] != n_frames or metadata["fields"] != ["z", "y", "x"]:
            raise ValueError("Expected the same number of time slots and z,y,x order")
        slots = shape[1] // 3
        reverse = primary.read_array(bundle, "points_to_tracks/indptr", prefix="")
        indices = primary.read_array(bundle, "points_to_tracks/indices", prefix="")
        occupied = np.diff(reverse)
        if occupied.max() != 1 or reverse[-1] != len(indices):
            raise ValueError("Unexpected point-to-track mapping in second archive")
        for frame in sorted(set(queries) | set(alignment_frames)):
            rows, details = frame_query(
                bundle, frame, queries.get(frame, []), slots, occupied, reverse, indices
            )
            if frame in alignment_frames:
                alignment_frames[frame] = rows
            for index, shift, position, distance, gap, label, xyz in details:
                answers[index, shift].append((position, distance, gap, label, xyz))
    return answers


def analyze(matches, candidate, n_frames, scale):
    results = {}
    for name, (radius, separation) in CRITERIA.items():
        for shift in SHIFTS:
            key = name, shift
            start = candidate["start_frame"] + shift
            stop = candidate["return_frame"] + shift
            if start < 0 or stop >= n_frames:
                results[key] = ("outside_recording", None)
                continue
            series = matches[shift]
            if [point[0] for point in series] != list(range(stop - start + 1)):
                raise ValueError("Expected an answer at all candidate frames")
            furthest_match = max(point[1] for point in series)
            smallest_gap = min(point[2] for point in series)
            if furthest_match > radius or smallest_gap < separation:
                results[key] = ("nearest_detection_unresolved", None)
                continue
            track_ids = {point[3] for point in series}
            if len(track_ids) != 1:
                results[key] = ("alternative_track_id_changes", None)
                continue
            path = np.array([point[4] for point in series], dtype=float)
            status, measure = primary.score(
                path, primary.path_distances(path), scale, 0.005, 10
            )
            row = {
                "alternate_track_id": next(iter(track_ids)),
                "largest_match_distance": float(furthest_match),
                "smallest_distance_to_competing_hit_above_match": float(smallest_gap),
                "alternate_start_xyz": path[0].tolist(),
                "alternate_xyz_relative_to_start": (path - path[0]).tolist(),
                "alternate_return": measure,
            }
            results[key] = (status, row)
    return results


def compare_frame_positions(sample, frames, xyz, alternatives, n_frames):
    rows = []
    for t in sample:
        source = xyz[frames == t]
        row = {"frame": int(t), "number_of_points_in_primary": len(source)}
        for offset in (-10, 0, 10):
            target_frame = t + offset
            if 0 <= target_frame < n_frames:
                distances, _ = cKDTree(alternatives[target_frame]).query(source)
                row[f"exact_matches_with_offset_{offset}"] = int(
                    np.count_nonzero(distances == 0)
                )
        rows.append(row)
    return rows


def check_counts(answers, candidates, n_frames, scale):
    counts = {(name, shift): defaultdict(int) for name in CRITERIA for shift in SHIFTS}
    supported = {name: [] for name in CRITERIA}
    for index, candidate in enumerate(candidates):
        matches = {offset: answers.get((index, offset), []) for offset in SHIFTS}
        result = analyze(matches, candidate, n_frames, scale)
        for (name, shift), (status, details) in result.items():
            counts[name, shift][status] += 1
            if shift == 0 and details is not None:
                supported[name].append(
                    {
                        "primary_track_id": candidate["track_id"],
                        "start_frame": candidate["start_frame"],
                        "last_frame_for_match": candidate["return_frame"],
                        "status": status,
                        **details,
                    }
                )
    return {
        name: {
            str(shift): dict(sorted(counts[name, shift].items())) for shift in SHIFTS
        }
        for name in CRITERIA
    }, supported


def run(raw, out, e62):
    frames, xyz, pointers, scale, n_frames = primary.original_tracks(raw)
    with (e62 / "candidate_returns.tsv").open() as stream:
        candidates = [
            {key: int(row[key]) for key in ("track_id", "start_frame", "return_frame")}
            for row in csv.DictReader(stream, delimiter="\t")
        ]

    def original_path(index):
        row = candidates[index]
        track = row["track_id"] - 1
        begin, end = pointers[track : track + 2]
        start = int(np.searchsorted(frames[begin:end], row["start_frame"]) + begin)
        stop = start + row["return_frame"] - row["start_frame"] + 1
        if stop > end or not np.array_equal(
            frames[start:stop], np.arange(row["start_frame"], row["return_frame"] + 1)
        ):
            raise ValueError("Candidate coordinates no longer match E62")
        return xyz[start:stop]

    query = requests(original_path, candidates, n_frames)
    sample = np.linspace(0, n_frames - 1, 12, dtype=int)
    alternatives = {
        t + offset: None
        for t in sample
        for offset in (-10, 0, 10)
        if 0 <= t + offset < n_frames
    }
    answers = match_requests(raw, query, alternatives, n_frames)
    alignment = compare_frame_positions(sample, frames, xyz, alternatives, n_frames)
    counts, supported = check_counts(answers, candidates, n_frames, scale)
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E65",
            "doi": "10.1038/s41592-025-02778-0",
            "evidence": "two separately distributed automated tracking outputs on the same image sequence",
            "primary_return_candidates": len(candidates),
            "alignment_at_12_timepoints": alignment,
            "match_distance_and_gap_to_second_neighbor": {
                key: list(value) for key, value in CRITERIA.items()
            },
            "counts_by_match_rule_and_time_shift_frames": counts,
            "same_id_for_all_frames_and_3d_rescore": supported,
            "scope": "The second archive is published with Ultrack's sparse-label validation article. Coordinate agreement aligns the same acquisition. Matching IDs are computational cross-checks, without identifying hand-curated red labels or verifying nuclear identity directly in volumes.",
            "checks": {
                "counts_include_each_primary_candidate_per_condition": all(
                    sum(values.values()) == len(candidates)
                    for screens in counts.values()
                    for values in screens.values()
                ),
                "many_more_exact_coordinate_matches_at_the_same_frame": all(
                    row["exact_matches_with_offset_0"]
                    > 10
                    * max(
                        row.get("exact_matches_with_offset_-10", 0),
                        row.get("exact_matches_with_offset_10", 0),
                    )
                    for row in alignment
                ),
            },
        },
        __file__,
        sources.__file__,
        primary.__file__,
        reconstruction.__file__,
    )
