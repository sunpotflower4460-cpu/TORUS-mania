"""Search for first 3D returns within single zebrafish tracking segments."""

import csv
import json
from collections import Counter
from zipfile import ZipFile

import numpy as np
from numcodecs import Blosc

from experiments import embryo_history_sources as sources
from experiments.common import save_summary

STORE = "tracks_zebrafish_bundle.zarr/"
PATH = "tracks_to_points/"


def read_array(archive, member, prefix=STORE):
    meta = json.loads(archive.read(prefix + member + "/.zarray"))
    shape, chunks = tuple(meta["shape"]), tuple(meta["chunks"])
    if meta["compressor"]["id"] != "blosc" or shape[1:] != chunks[1:]:
        raise ValueError(f"Unexpected chunk encoding for {member}")
    decoder = Blosc()
    data = np.empty(shape, dtype=meta["dtype"])
    for index, start in enumerate(range(0, shape[0], chunks[0])):
        suffix = ".".join([str(index)] + ["0"] * (len(shape) - 1))
        packed = archive.read(prefix + member + "/" + suffix)
        chunk = np.frombuffer(decoder.decode(packed), dtype=data.dtype).reshape(
            (-1, *shape[1:])
        )
        length = min(chunks[0], shape[0] - start)
        data[start : start + length] = chunk[:length]
    return data


def original_tracks(raw):
    with ZipFile(sources.source(raw, "zebrafish-tracks.zarr.zip")) as archive:
        meta = json.loads(archive.read(STORE + "points/.zattrs"))
        shape = json.loads(archive.read(STORE + "points/.zarray"))["shape"]
        if meta["fields"] != ["z", "y", "x"] or meta["values_per_point"] != 3:
            raise ValueError("Unexpected spatial fields")
        pointers = read_array(archive, PATH + "indptr")
        indices = read_array(archive, PATH + "indices")
        xyz = read_array(archive, PATH + "data")[:, ::-1]
        slots = shape[1] // meta["values_per_point"]
        frames, frame_slot = np.divmod(indices, slots)
        reverse_pointers = read_array(archive, "points_to_tracks/indptr")
        mapped = np.diff(reverse_pointers)
        if (
            mapped.max() != 1
            or mapped.sum() != len(indices)
            or not np.all(mapped[indices] == 1)
        ):
            raise ValueError("The archive does not have one branch per occupied point")
        branch_at_point = read_array(archive, "points_to_tracks/indices")
        branch_rows = np.repeat(np.arange(len(pointers) - 1), np.diff(pointers))
        if not np.array_equal(branch_at_point[reverse_pointers[indices]], branch_rows):
            raise ValueError("Track and point indices disagree")
        # Cross-check a deterministic sample directly against the per-frame positions.
        sample_frames = np.linspace(0, shape[0] - 1, num=12, dtype=int)
        for frame in sample_frames:
            member = STORE + "points/" + str(frame) + ".0"
            data = np.frombuffer(
                Blosc().decode(archive.read(member)), dtype=np.float32
            ).reshape(-1, 3)
            take = frames == frame
            if not np.array_equal(xyz[take, ::-1], data[frame_slot[take]]):
                raise ValueError(
                    f"Points and track coordinates disagree at frame {frame}"
                )
    if pointers[-1] != len(frames) or not np.isfinite(xyz).all():
        raise ValueError("Lengths or positions are invalid")
    return frames, xyz, pointers, float(meta["extent_xyz"]), shape[0]


def split_at_gaps(frames, pointers):
    """Keep each run within its original branch and consecutive frame slots."""
    is_branch_start = np.zeros(len(frames), dtype=bool)
    is_branch_start[pointers[:-1]] = True
    changes = np.diff(frames)
    bad = np.flatnonzero((changes < 1) & ~is_branch_start[1:]) + 1
    bad_branches = np.unique(np.searchsorted(pointers, bad, side="right") - 1)
    is_segment_start = is_branch_start.copy()
    is_segment_start[1:] |= changes != 1
    starts = np.flatnonzero(is_segment_start)
    stops = np.r_[starts[1:], len(frames)]
    branches = np.searchsorted(pointers, starts, side="right") - 1
    good = ~np.isin(branches, bad_branches)
    return starts[good], stops[good], branches[good], len(bad_branches)


def rotation(path, cumulative):
    samples = np.linspace(0, cumulative[-1], 33)
    nonduplicate = np.r_[True, np.diff(cumulative) > 0]
    coords = np.column_stack(
        [
            np.interp(samples, cumulative[nonduplicate], axis[nonduplicate])
            for axis in path.T
        ]
    )
    centered = coords - coords.mean(axis=0)
    _, singular, plane = np.linalg.svd(centered, full_matrices=False)
    flat = centered @ plane[:2].T
    angles = np.unwrap(np.arctan2(flat[:, 1], flat[:, 0]))
    total = np.abs(np.diff(angles)).sum()
    net = abs(angles[-1] - angles[0])
    aspect = float(singular[1] / singular[0])
    winding = float(net / (2 * np.pi))
    consistency = float(net / total) if total else 0.0
    return aspect, winding, consistency


def path_distances(path):
    departure = np.linalg.norm(path - path[0], axis=1)
    steps = np.linalg.norm(np.diff(path, axis=0), axis=1)
    return (
        departure,
        np.maximum.accumulate(departure),
        np.r_[0, np.cumsum(steps)],
        np.r_[0, np.maximum.accumulate(steps)],
    )


def score(path, distances, scale, tolerance, min_points):
    gap, excursion, length, largest_step = distances
    traveled = (excursion >= 0.02 * scale) & (length >= 0.05 * scale)
    if not traveled[-1]:
        return "insufficient_travel", None
    # Prevent a path that never leaves a proximity ball from passing as a return.
    # All tested tolerances are at most half the minimum required excursion.
    eligible = (gap[min_points - 1 :] <= tolerance * scale) & traveled[min_points - 1 :]
    returned = np.flatnonzero(eligible)
    if returned.size == 0:
        return "no_near_return", None
    index = int(returned[0] + min_points - 1)
    result = {
        "end_offset": index,
        "return_gap": float(gap[index]),
        "furthest_distance": float(excursion[index]),
        "path_length": float(length[index]),
        "largest_step": float(largest_step[index]),
    }
    if largest_step[index] > 0.5 * excursion[index]:
        return "jump", result
    aspect, winding, consistency = rotation(path[: index + 1], length[: index + 1])
    result.update(aspect=aspect, winding=winding, direction_consistency=consistency)
    passes = aspect >= 0.15 and winding >= 0.8 and consistency >= 0.75
    return ("curving_return" if passes else "nonrotational_return"), result


def calibrate():
    angle = np.linspace(0, 2 * np.pi, 81)
    # A constant orthogonal, 3D rotation of an originally planar circle.
    basis = np.array([[1, 0, 0], [0, 0.6, 0.8], [0, -0.8, 0.6]])
    circle = (
        32
        * np.column_stack([np.cos(angle), np.sin(angle), np.zeros(len(angle))])
        @ basis
    )
    outward = np.linspace(0, 60, 41)
    reverse = np.r_[outward, outward[-2::-1]]
    controls = {
        "tilted_circle": circle,
        "circle_truncated_at_270_degrees": circle[:61],
        "straight_out_and_back": np.column_stack([reverse, reverse * 0, reverse * 0]),
        "directed_half_arc": circle[:41],
        "helix_with_same_endpoint_in_xy_only": 32
        * np.column_stack([np.cos(angle), np.sin(angle), angle / np.pi]),
    }
    return {
        key: score(path, path_distances(path), 1021.0, 0.005, 10)[0]
        for key, path in controls.items()
    }


SCREENS = {
    "primary": (0.005, 10),
    "half_radius": (0.0025, 10),
    "double_radius": (0.01, 10),
    "at_least_20_observations": (0.005, 20),
    "start_every_10_observations_after_first": (0.005, 10),
}


def audit_viewer(raw):
    path = sources.source(raw, "shah-viewer-data.js")
    payload = json.loads(path.read_text().partition("=")[2].strip().rstrip(";"))
    (dataset,) = payload["sets"]
    states = [state["name"] for state in dataset["states"]]
    return {
        "doi": "10.1038/s41467-019-13625-0",
        "states": states,
        "dimensions": payload["dim"],
        "display_entity_count": int(
            np.unique(np.concatenate(dataset["entities"])).size
        ),
        "included_as_continuous_observations": False,
        "reason": "The paper links the viewer to long-term trajectories and describes their statistical-velocity assembly. The viewer's original state identifies the pre-bundling positions, without trace-level provenance that establishes original short detections.",
    }


def scan(frames, xyz, pointers, scale):
    starts, stops, branches, bad = split_at_gaps(frames, pointers)
    lengths = stops - starts
    total = {name: Counter() for name in SCREENS}
    plotted = {
        "return": None,
        "closest_nonreturn": None,
    }
    returns = []
    for index in np.flatnonzero(lengths >= 10):
        left, right = int(starts[index]), int(stops[index])
        duration = right - left
        path = xyz[left:right].astype(float)
        distances = path_distances(path)
        for name, (tolerance, min_points) in SCREENS.items():
            if (
                name == "start_every_10_observations_after_first"
                or duration < min_points
            ):
                continue
            status, observation = score(path, distances, scale, tolerance, min_points)
            total[name][status] += 1
            if name != "primary" or observation is None:
                continue
            branch = int(branches[index]) + 1  # InTracktive track ID = CSR row + 1.
            entry = {
                "track_id": branch,
                "start_frame": int(frames[left]),
                "return_frame": int(frames[left + observation["end_offset"]]),
                "observations_available": duration,
                **observation,
            }
            if status == "curving_return":
                returns.append(entry)
                if (
                    plotted["return"] is None
                    or entry["return_gap"] < plotted["return"]["return_gap"]
                ):
                    plotted["return"] = {
                        **entry,
                        "xyz_relative_to_start": (
                            path[: observation["end_offset"] + 1] - path[0]
                        ).tolist(),
                    }
            if status == "nonrotational_return":
                previous = plotted["closest_nonreturn"]
                if previous is None or entry["return_gap"] < previous["return_gap"]:
                    plotted["closest_nonreturn"] = {
                        **entry,
                        "xyz_relative_to_start": (
                            path[: observation["end_offset"] + 1] - path[0]
                        ).tolist(),
                    }
        # Explore returns that started after the first position of the tracklet.
        for start in range(10, duration - 9, 10):
            suffix = path[start:]
            status, _ = score(suffix, path_distances(suffix), scale, 0.005, 10)
            total["start_every_10_observations_after_first"][status] += 1
    return {
        "continuous_intervals": len(starts),
        "intervals_with_10_or_20_or_40_observations": [
            int(np.count_nonzero(lengths >= threshold)) for threshold in (10, 20, 40)
        ],
        "nonmonotone_branches_excluded": bad,
        "longest_continuous_interval_observations": int(lengths.max()),
        "screen_counts": {
            key: dict(sorted(value.items())) for key, value in total.items()
        },
        "example_paths": plotted,
    }, returns


def run(raw, out):
    frames, xyz, pointers, scale, n_frames = original_tracks(raw)
    observed, returns = scan(frames, xyz, pointers, scale)
    controls = calibrate()
    viewer = audit_viewer(raw)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "candidate_returns.tsv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "track_id",
                "start_frame",
                "return_frame",
                "observations_available",
                "end_offset",
                "return_gap",
                "furthest_distance",
                "path_length",
                "largest_step",
                "aspect",
                "winding",
                "direction_consistency",
            ],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(returns)
    counts = observed["screen_counts"]["primary"]
    save_summary(
        out,
        {
            "experiment": "E62",
            "evidence": "volumetric microscopy-derived automated tracking of cells",
            "dataset": "Virtual Embryo Zoo Danio r. tracks_zebrafish_bundle.zarr.zip",
            "public_shah_viewer_provenance_audit": viewer,
            "observations": len(frames),
            "frames_in_archive": n_frames,
            "branch_ids": len(pointers) - 1,
            "unit": "archive coordinate unit",
            "extent_xyz_from_archive": scale,
            "minimum_departure": 0.02 * scale,
            "minimum_path_length": 0.05 * scale,
            "primary_return_radius": 0.005 * scale,
            "track_analysis": observed,
            "calibration_controls": controls,
            "scope": "Consecutive available frames and original branch IDs only; no imposed periodic boundaries or registration beyond the archived coordinates. No unobserved frames or lineage links filled. Cell tracks and nutrient, mechanical or total energy flux are distinct measurements.",
            "checks": {
                "forward_and_reverse_csr_point_assignments_and_sample_positions_agree": True,
                "3d_circle_recovered": controls["tilted_circle"] == "curving_return",
                "four_open_or_retracing_controls_rejected": sum(
                    status == "curving_return" for status in controls.values()
                )
                == 1,
                "segment_count_matches_primary_screen": sum(counts.values())
                == observed["intervals_with_10_or_20_or_40_observations"][0],
                "export_contains_all_primary_returns": len(returns)
                == counts.get("curving_return", 0),
                "visualization_states_distinct": viewer["states"]
                == ["original", "bundled"],
            },
        },
        __file__,
        sources.__file__,
    )
