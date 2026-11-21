"""Trace a fluorescent nucleus from one seed in downsampled 3D microscopy."""

import json
from zipfile import ZipFile

import numpy as np
from numcodecs import Blosc
from scipy.ndimage import gaussian_filter, maximum_filter

from experiments import embryo_history_sources as sources
from experiments.common import save_summary
from experiments.E62_cell_returns import run as closure
from experiments.E66_image_only_track import archive as images

SCALE = np.array([4.0, 4.0, 16.0])  # XYZ archive units per level-2 image voxel.
TRACK_ID = 251354
RADII = (18, 22, 26)


def image_peaks(block, origin):
    smooth = gaussian_filter(block.astype(np.float32), sigma=(0.65, 1.0, 1.0))
    median = np.median(smooth)
    mad = np.median(np.abs(smooth - median))
    if mad == 0:
        return np.empty((0, 3))
    peak_mask = (smooth == maximum_filter(smooth, size=3)) & (smooth > median + 3 * mad)
    # Require two neighbors for per-axis interpolation, even at the crop edge.
    for axis in range(3):
        bounds = (slice(None),) * axis
        peak_mask[bounds + (0,)] = False
        peak_mask[bounds + (-1,)] = False
    coordinates = np.array(np.nonzero(peak_mask)).T
    intensities = smooth[tuple(coordinates.T)]
    refined = coordinates.astype(float)
    for axis in range(3):
        offset = np.eye(3, dtype=int)[axis]
        left = smooth[tuple((coordinates - offset).T)]
        right = smooth[tuple((coordinates + offset).T)]
        curvature = left - 2 * intensities + right
        adjustment = np.divide(
            0.5 * (left - right),
            curvature,
            out=np.zeros_like(curvature),
            where=curvature != 0,
        )
        refined[:, axis] += np.clip(adjustment, -0.5, 0.5)
    return (refined[:, ::-1] + origin) * SCALE


def extract_peaks(raw, seed):
    center = np.round(seed / SCALE).astype(int)
    span = np.array([22, 22, 6])
    origin = center - span
    stop = center + span + 1
    with ZipFile(sources.source(raw, images.ARCHIVE)) as archive:
        level = json.loads(archive.read(f"{images.LEVEL}/.zarray"))
        all_metadata = json.loads(archive.read(".zattrs"))
        datasets = all_metadata["multiscales"][0]["datasets"]
        level_scaling = np.array(
            datasets[int(images.LEVEL)]["coordinateTransformations"][0]["scale"]
        )[-3:]
        xy_level_zero = datasets[0]["coordinateTransformations"][0]["scale"][-1]
        if not np.allclose(level_scaling[::-1] / xy_level_zero, SCALE):
            raise ValueError("Unexpected archive scale for registration")
        shape = tuple(level["chunks"][-3:])
        if not ((0 <= origin).all() and (stop <= shape[::-1]).all()):
            raise ValueError("Seed-centered region must fit the selected image chunk")
        rois = []
        for frame in images.FRAMES:
            member = f"{images.LEVEL}/{frame}/0/0/0/0"
            raw_data = Blosc().decode(archive.read(member))
            volume = np.frombuffer(raw_data, dtype=level["dtype"]).reshape(shape)
            roi = volume[
                tuple(
                    slice(a, b) for a, b in zip(origin[::-1], stop[::-1], strict=True)
                )
            ]
            rois.append(image_peaks(roi, origin))
    return rois


def seeded_path(peaks_by_frame, seed, radius):
    path = []
    for peaks in peaks_by_frame:
        if not len(peaks):
            break
        prediction = path[-1].copy() if path else seed.copy()
        if len(path) > 1:
            prediction += 0.5 * (path[-1] - path[-2])
        distances = np.linalg.norm(peaks - prediction, axis=1)
        index = int(distances.argmin())
        if distances[index] > radius:
            break
        path.append(peaks[index])
    return np.asarray(path).reshape(-1, 3)


def evaluate(path, reference, scale):
    distances = np.linalg.norm(path - reference[: len(path)], axis=1)
    compared = len(path)
    closure_results = {}
    for radius in (0.005, 0.01):
        if compared >= 10:
            status, measures = closure.score(
                path, closure.path_distances(path), scale, radius, 10
            )
        else:
            status, measures = "insufficient_observations", None
        closure_results[str(radius)] = {"status": status, "measures": measures}
    return {
        "number_of_frames_tracked": compared,
        "completed_all_frames": compared == len(reference),
        "distances_from_paper_linked_tracking": distances.tolist(),
        "median_distance": float(np.median(distances)) if compared else None,
        "max_distance": float(distances.max()) if compared else None,
        "fraction_of_target_frames_within_16": float(
            np.count_nonzero(distances <= 16) / len(reference)
        ),
        "matches_image_position_criterion": bool(
            compared == len(reference)
            and np.median(distances) <= 8
            and np.count_nonzero(distances <= 16) >= 0.9 * len(reference)
        ),
        "image_path_relative_to_first_position": (path - path[0]).tolist()
        if compared
        else [],
        "first_image_position_xyz": path[0].tolist() if compared else None,
        "return_screen_by_neighborhood_radius_fraction": closure_results,
    }


def run(raw, out, e62, e65):
    data = json.loads((e65 / "summary.json").read_text())
    matches = [
        row
        for row in data["same_id_for_all_frames_and_3d_rescore"]["relaxed"]
        if row["status"] == "curving_return"
    ]
    candidate = max(
        matches, key=lambda row: row["alternate_return"]["furthest_distance"]
    )
    if candidate["primary_track_id"] != TRACK_ID or (
        candidate["start_frame"],
        candidate["last_frame_for_match"],
    ) != (images.FRAMES.start, images.FRAMES.stop - 1):
        raise ValueError("Image input is fixed for the registered candidate")
    seed = np.array(candidate["alternate_start_xyz"])
    reference = seed + np.array(candidate["alternate_xyz_relative_to_start"])
    primary = json.loads((e62 / "summary.json").read_text())
    peaks = extract_peaks(raw, seed)
    screens = {
        str(radius): evaluate(
            seeded_path(peaks, seed, radius),
            reference,
            primary["extent_xyz_from_archive"],
        )
        for radius in RADII
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E66",
            "experiment_role": "image-only tracking of one preselected E65 candidate",
            "doi": "10.1038/s41592-025-02778-0",
            "E62_track_id": TRACK_ID,
            "E65_track_id": candidate["alternate_track_id"],
            "start_through_stop_frames_inclusive": [
                images.FRAMES.start,
                images.FRAMES.stop - 1,
            ],
            "pyramid_level": int(images.LEVEL),
            "channel": 0,
            "xy_and_z_archive_units_per_image_voxel": SCALE.tolist(),
            "starting_seed_xyz_in_archive_units": seed.tolist(),
            "image_peak_count_by_frame": [len(coords) for coords in peaks],
            "path_screen_by_prediction_radius": screens,
            "scope": "A deterministic brightness-peak tracker uses one coordinate seed and then image peaks. The pyramid's coarse axial resolution and neighboring nuclei could limit correspondence. This is the same acquisition as the compared tracks and a single selected branch.",
            "checks": {
                "source_input_includes_all_31_registered_frames": len(peaks)
                == len(reference)
                == 31,
                "multiple_candidate_peaks_per_frame_in_seed_region": all(
                    len(coords) > 1 for coords in peaks
                ),
            },
        },
        __file__,
        images.__file__,
        closure.__file__,
        sources.__file__,
    )
