"""Retest the largest candidate from E65 using more detailed 3D images."""

import json

import numpy as np
from numcodecs import Blosc
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.signal import correlate

from experiments.common import save_summary
from experiments.E66_image_only_track import run as earlier
from experiments.E67_half_resolution import archive

SCALE = np.array([2.0, 2.0, 8.0])  # Archive units per level-1 voxel in XYZ.
SPACING = SCALE[::-1]
PATCH_HALF = np.array([2, 6, 6])  # ZYX.
SEARCH_RADIUS = 22
CUTOFFS = (0.50, 0.65, 0.80)


def crop_slices(lower, upper):
    return tuple(slice(a, b) for a, b in zip(lower, upper, strict=True))


def volumes(source, seed):
    if archive.content_hash(source) != archive.EXPECTED_MANIFEST_SHA:
        raise ValueError("Unexpected level-1 archive version")
    level = json.loads((source / archive.LEVEL / ".zarray").read_text())
    info = json.loads((source / ".zattrs").read_text())["multiscales"][0]["datasets"]
    calibration = [row["coordinateTransformations"][0]["scale"][-3:] for row in info]
    inferred_units = (
        np.array(calibration[int(archive.LEVEL)][::-1]) / calibration[0][-1]
    )
    if not np.allclose(inferred_units, SCALE):
        raise ValueError("Archive dimensions no longer agree with preregistered units")
    chunk_shape = tuple(level["chunks"][-3:])
    center = np.rint(seed[::-1] / SPACING).astype(int)
    span = np.array([12, 44, 44])
    low, high = center - span, center + span + 1
    if np.any(low < 0) or np.any(high > chunk_shape):
        raise ValueError("The registered crop falls outside the retrieved Z chunk")
    frames = []
    for t in archive.FRAMES:
        contents = (source / archive.LEVEL / str(t) / "0/0/0/0").read_bytes()
        volume = np.frombuffer(Blosc().decode(contents), dtype=level["dtype"]).reshape(
            chunk_shape
        )
        frames.append(volume[crop_slices(low, high)].astype(float))
    return frames, low


def crop_patch(frame, position):
    return frame[crop_slices(position - PATCH_HALF, position + PATCH_HALF + 1)]


def template_match(frame, template, predicted, radius):
    search_voxels = np.ceil(radius / SPACING).astype(int)
    center = np.rint(predicted).astype(int)
    lo = np.maximum(PATCH_HALF, center - search_voxels)
    hi = np.minimum(np.array(frame.shape) - PATCH_HALF - 1, center + search_voxels)
    if np.any(lo > hi):
        return None
    window = frame[crop_slices(lo - PATCH_HALF, hi + PATCH_HALF + 1)]
    centered = template - template.mean()
    window = window - window.mean()
    ones = np.ones(template.shape)
    numerator = correlate(window, centered, mode="valid", method="fft")
    sums = correlate(window, ones, mode="valid", method="fft")
    squared = correlate(window**2, ones, mode="valid", method="fft")
    variance = np.maximum(squared - sums**2 / centered.size, 0)
    norm = np.sqrt(variance * np.sum(centered**2))
    similarity = np.divide(
        numerator, norm, where=norm > 1e-8, out=np.full_like(numerator, -np.inf)
    )
    grid = np.moveaxis(np.indices(similarity.shape), 0, -1)
    distance_squared = np.sum(((grid + lo - predicted) * SPACING) ** 2, axis=-1)
    merit = np.where(
        distance_squared <= radius**2,
        similarity - 0.05 * distance_squared / radius**2,
        -np.inf,
    )
    index = np.unravel_index(merit.argmax(), merit.shape)
    if not np.isfinite(merit[index]):
        return None
    return lo + np.array(index), float(np.clip(similarity[index], -1, 1))


def template_trace(frames, seed_xyz, low, cutoff):
    seed_voxel = np.rint(seed_xyz[::-1] / SPACING - low).astype(int)
    template = crop_patch(frames[0], seed_voxel)
    path = [seed_voxel]
    confidence = []
    stop_correlation = None
    for frame in frames[1:]:
        predicted = path[-1].astype(float)
        if len(path) >= 2:
            predicted += 0.5 * (path[-1] - path[-2])
        candidate = template_match(frame, template, predicted, SEARCH_RADIUS)
        if candidate is None:
            break
        locate, quality = candidate
        if quality < cutoff:
            stop_correlation = quality
            break
        path.append(locate)
        confidence.append(quality)
    return ((np.array(path) + low) * SPACING)[:, ::-1], confidence, stop_correlation


def bright_peaks(volume, low):
    data = gaussian_filter(volume, sigma=(1.3, 2.0, 2.0))
    median = np.median(data)
    mad = np.median(np.abs(data - median))
    mask = (data == maximum_filter(data, size=(5, 5, 5))) & (data > median + 3 * mad)
    where = np.argwhere(mask)
    where = where[np.all((where > 0) & (where < np.array(data.shape) - 1), axis=1)]
    peak = data[tuple(where.T)]
    refined = where.astype(float)
    for axis, shift in enumerate(np.eye(3, dtype=int)):
        left, right = [data[tuple((where + sign * shift).T)] for sign in (-1, 1)]
        curvature = left + right - 2 * peak
        offset = np.divide(
            0.5 * (left - right),
            curvature,
            out=np.zeros_like(curvature),
            where=curvature != 0,
        )
        refined[:, axis] += np.clip(offset, -0.5, 0.5)
    return ((refined + low) * SPACING)[:, ::-1]


def shape_at(grid, center):
    z, y, x = grid - np.asarray(center)[:, None, None, None]
    main = np.exp(-((z / 1.3) ** 2 + (y / 3.2) ** 2 + (x / 3.0) ** 2) / 2)
    texture = 0.6 * np.exp(
        -(((z + 0.5) / 0.7) ** 2 + ((y - 2) / 1.2) ** 2 + ((x - 1) / 0.8) ** 2)
    )
    return main + texture


def calibration():
    grid = np.indices((17, 33, 52))
    centers = np.array([[8, 13 + t, 14 + 2 * t] for t in range(9)])
    frames = [shape_at(grid, p) + 2 * i for i, p in enumerate(centers)]
    expected = (centers * SPACING)[:, ::-1]
    fitted, _, _ = template_trace(frames, expected[0], np.zeros(3), 0.65)
    removed = frames.copy()
    removed[4] = np.full_like(removed[4], 100.0)
    interrupted, _, _ = template_trace(removed, expected[0], np.zeros(3), 0.65)
    return {
        "directed_translation_continuous_points": len(fitted),
        "maximum_forward_error": float(
            np.max(np.linalg.norm(fitted - expected[: len(fitted)], axis=1))
        ),
        "points_before_signal_loss": len(interrupted),
    }


def run(raw, out, previous):
    base = json.loads((previous / "E62/summary.json").read_text())
    validation = json.loads((previous / "E65/summary.json").read_text())
    candidate = next(
        row
        for row in validation["same_id_for_all_frames_and_3d_rescore"]["relaxed"]
        if row["primary_track_id"] == earlier.TRACK_ID
    )
    start = np.array(candidate["alternate_start_xyz"])
    reference = start + np.array(candidate["alternate_xyz_relative_to_start"])
    # The final frame position only seeds the reverse path. Neither fitting
    # direction receives any intermediate reference point.
    movie, low = volumes(raw, start)
    scale = base["extent_xyz_from_archive"]
    screens = {}
    for cutoff in CUTOFFS:
        for direction in ("forward", "reverse"):
            expected, frames = (
                (reference, movie)
                if direction == "forward"
                else (reference[::-1], movie[::-1])
            )
            coords, qualities, stopped = template_trace(
                frames, expected[0], low, cutoff
            )
            comparison = earlier.evaluate(coords, expected, scale)
            comparison["final_distance_from_own_start"] = float(
                np.linalg.norm(coords[-1] - coords[0])
            )
            comparison["maximum_distance_from_own_start"] = float(
                np.linalg.norm(coords - coords[0], axis=1).max()
            )
            screens[f"{direction}, {cutoff:.2f}"] = {
                **comparison,
                "tracked_normalized_correlations": qualities,
                "correlation_at_stopping_frame_below_threshold": stopped,
            }
    peaks = [bright_peaks(frame, low) for frame in movie]
    baseline = earlier.evaluate(
        earlier.seeded_path(peaks, start, SEARCH_RADIUS), reference, scale
    )
    nearest_diagnostic = [
        float(np.linalg.norm(rows - pos, axis=1).min()) if len(rows) else None
        for rows, pos in zip(peaks, reference, strict=True)
    ]
    control = calibration()
    out.mkdir(parents=True, exist_ok=True)
    save_summary(
        out,
        {
            "experiment": "E67",
            "doi": "10.1038/s41592-025-02778-0",
            "archive_primary_track_id": earlier.TRACK_ID,
            "paper_linked_track_id": candidate["alternate_track_id"],
            "frames_inclusive": [archive.FRAMES.start, archive.FRAMES.stop - 1],
            "image_level": int(archive.LEVEL),
            "image_channel": 0,
            "images_source_manifest_sha256": archive.EXPECTED_MANIFEST_SHA,
            "archive_units_xyz_per_voxel": SCALE.tolist(),
            "recorded_peak_method_comparison": baseline,
            "normalized_template_match": screens,
            "reference_start_xyz": start.tolist(),
            "centered_reference_track_xyz": (reference - start).tolist(),
            "nearest_brightness_peak_given_reference_distance": nearest_diagnostic,
            "scope": "Two seeded directions and the comparison positions come from the same green-channel acquisition and do not add a second embryo or an independent fluorescent identity marker. The image peak diagnostics use all reference positions and are kept outside the blinded tracking comparison.",
            "synthetic_controls": control,
            "checks": {
                "translated_texture_recovered": control[
                    "directed_translation_continuous_points"
                ]
                == 9
                and control["maximum_forward_error"] < 1e-8,
                "blank_frame_censors_without_filling": control[
                    "points_before_signal_loss"
                ]
                == 4,
                "all_registered_target_frames_available": len(movie)
                == len(reference)
                == 31,
            },
        },
        __file__,
        archive.__file__,
        earlier.__file__,
    )
