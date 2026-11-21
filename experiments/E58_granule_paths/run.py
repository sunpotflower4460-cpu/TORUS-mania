"""Track resolved fluorescent granules in a single optical view."""

import json
import subprocess
from collections import Counter
from itertools import groupby

import cv2
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.spatial import cKDTree

from experiments import particle_return_sources as sources
from experiments.common import save_summary

FRAME_INTERVAL = 2.0  # acquisition interval from the burned-in time marks
FRAME_SHAPE = (196, 368)
CENTER = (177, 95)
ELLIPSE_RADII = (152, 77)
REDETECT_EVERY = 8
LK_SETTINGS = {
    "winSize": (13, 13),
    "maxLevel": 1,
    "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 18, 0.025),
}


def decode_movie(path):
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-threads",
        "1",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-pix_fmt",
        "gray",
        "-f",
        "rawvideo",
        "-",
    ]
    return np.frombuffer(
        subprocess.run(command, check=True, capture_output=True).stdout, dtype=np.uint8
    ).reshape(-1, *FRAME_SHAPE)


def video_info(path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,nb_frames,r_frame_rate",
        "-of",
        "json",
        str(path),
    ]
    return json.loads(subprocess.run(command, check=True, capture_output=True).stdout)["streams"][0]


def scale_bar(frame):
    rows = frame[167:174, 11:93]
    y = int(np.argmax((rows > 235).sum(axis=1)))
    above = rows[y] > 235
    runs = [list(run) for bright, run in groupby(enumerate(above), key=lambda item: item[1]) if bright]
    left, right = max(runs, key=len)[0][0] + 11, max(runs, key=len)[-1][0] + 11
    return (right - left + 1) / 10.0, [left, right, y + 167]


def ellipse_mask(radius):
    yy, xx = np.indices(FRAME_SHAPE)
    return ((xx - CENTER[0]) / ELLIPSE_RADII[0]) ** 2 + (
        (yy - CENTER[1]) / ELLIPSE_RADII[1]
    ) ** 2 <= radius**2


def peaks(frame, mask):
    f = frame.astype(np.float32)
    score = cv2.GaussianBlur(f, (0, 0), 0.86) - cv2.GaussianBlur(f, (0, 0), 2.8)
    floor = max(2.5, float(np.quantile(score[mask], 0.73)))
    candidate = (cv2.dilate(score, np.ones((5, 5), np.uint8)) == score) & (score >= floor) & mask
    y, x = np.where(candidate)
    order = np.argsort(-score[y, x], kind="stable")
    return np.stack((x[order], y[order]), axis=-1).astype(np.float32)


def patch_similarity(first, second, source, target):
    a = cv2.getRectSubPix(first, (9, 9), tuple(source)).astype(np.float64).ravel()
    b = cv2.getRectSubPix(second, (9, 9), tuple(target)).astype(np.float64).ravel()
    a -= a.mean()
    b -= b.mean()
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denominator) if denominator else 0.0


def track(frames, minimum_similarity=0.72, mask_radius=1.0):
    mask = ellipse_mask(mask_radius)
    active, done = [], []
    stopped = Counter()
    previous = frames[0]
    for t, frame in enumerate(frames):
        bright = peaks(frame, mask)
        if active and len(bright):
            initial = np.array([points[-1] for _, points in active], dtype=np.float32)
            forward, forward_ok, _ = cv2.calcOpticalFlowPyrLK(previous, frame, initial, None, **LK_SETTINGS)
            back, back_ok, _ = cv2.calcOpticalFlowPyrLK(frame, previous, forward, None, **LK_SETTINGS)
            fb_error = np.linalg.norm(initial - back, axis=1)
            snap, index = cKDTree(bright).query(forward)
            targets = bright[index]
            proposed = (
                (forward_ok.ravel() == 1) & (back_ok.ravel() == 1) & (fb_error <= 0.8) & (snap <= 2.1)
            )
            proposed &= np.linalg.norm(initial - targets, axis=1) <= 5.5
            counts = Counter(index[proposed])
            surviving = []
            for i, item in enumerate(active):
                if not proposed[i]:
                    reason = "lost_or_motion_ambiguous"
                elif counts[index[i]] != 1:
                    reason = "two_paths_claimed_one_peak"
                elif patch_similarity(previous, frame, initial[i], targets[i]) < minimum_similarity:
                    reason = "appearance_changed"
                else:
                    item[1].append(targets[i].tolist())
                    surviving.append(item)
                    continue
                stopped[reason] += 1
                done.append(item)
            active = surviving
        elif active:
            stopped["no_peaks"] += len(active)
            done.extend(active)
            active = []
        if t % REDETECT_EVERY == 0:
            occupied = [path[-1] for _, path in active]
            if occupied:
                distance, _ = cKDTree(occupied).query(bright)
                bright = bright[distance >= 5.5]
            for point in bright:
                # The detector already separates newly detected local maxima.
                active.append((t, [point.tolist()]))
        previous = frame
    stopped["video_ended"] += len(active)
    return done + active, stopped


def loop_end(path, radius):
    distances = np.linalg.norm(path - path[0], axis=1)
    distance_travelled = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    far = np.maximum.accumulate(distances)
    possible = (np.arange(len(path)) * FRAME_INTERVAL >= 60) & (distances <= radius)
    possible &= (far >= 5.0) & (distance_travelled >= 14.0)
    for i in np.flatnonzero(possible):
        journey = path[: i + 1]
        shifted = journey - journey.mean(axis=0)
        if np.min(np.linalg.norm(shifted, axis=1)) < 0.8:
            continue
        nxt = np.roll(shifted, -1, axis=0)
        cross = shifted[:, 0] * nxt[:, 1] - shifted[:, 1] * nxt[:, 0]
        area = cross.sum() / 2
        angles = np.arctan2(cross, np.sum(shifted * nxt, axis=1))
        net = abs(angles.sum())
        if abs(area) >= 5.0 and net >= 1.99 * np.pi and net >= 0.65 * np.abs(angles).sum():
            return {
                "end_offset_frames": int(i),
                "departure_um": float(far[i]),
                "closure_um": float(distances[i]),
                "length_um": float(distance_travelled[i]),
                "signed_area_um2": float(area),
                "winding": round(angles.sum() / (2 * np.pi)),
            }
    return None


def fold(path):
    for direction in (1, -1):
        axial = path[:, 0] * direction
        turn = int(np.argmax(axial))
        if turn < 4 or len(path) - turn < 5:
            continue
        section = axial[turn] - 3.0
        before = np.flatnonzero(axial[:turn] <= section)
        after = np.flatnonzero(axial[turn + 1 :] <= section)
        if not len(before) or not len(after):
            continue
        i, j = int(before[-1]), turn + 1 + int(after[0])
        y1 = np.interp(section, axial[i : i + 2], path[i : i + 2, 1])
        y2 = np.interp(section, axial[j - 1 : j + 1][::-1], path[j - 1 : j + 1, 1][::-1])
        separation = abs(y2 - y1)
        if separation >= 1.5:
            return {
                "bounds_frames": [i, j],
                "turn_frame": turn,
                "turn_x_direction": direction,
                "cross_axis_separation_um": float(separation),
            }
    return None


def evaluate(paths, scale, radius=1.0):
    lengths, turns, loops = [], [], []
    for start, coordinate in paths:
        points = np.asarray(coordinate)
        lengths.append((len(points) - 1) * FRAME_INTERVAL)
        if len(points) < 9:
            continue
        smoothed = uniform_filter1d(points, size=5, mode="nearest", axis=0) / scale
        closed = loop_end(smoothed, radius)
        turning = fold(smoothed)
        if closed or turning:
            item = {
                "start_frame": start,
                "end_frame": start + len(points) - 1,
                "xy_pixels": coordinate,
                "closure": closed,
                "fold": turning,
            }
            if closed:
                loops.append(item)
            if turning:
                turns.append(item)
    ages = np.array(lengths)
    return {
        "paths_started": len(paths),
        "track_duration_seconds_quantiles": np.quantile(ages, [0.5, 0.9, 0.99, 1]).tolist(),
        "n_at_least_30_60_120_seconds": [int((ages >= s).sum()) for s in (30, 60, 120)],
        "fold_count": len(turns),
        "loop_count": len(loops),
        "loop_paths": loops,
        "fold_paths": turns,
    }


def coverage_and_directions(paths, scale, frame_count):
    long_enough = Counter()
    bins = [[[], []] for _ in range((frame_count + 29) // 30)]
    for start, positions in paths:
        if len(positions) < 7:
            continue
        smoothed = uniform_filter1d(np.asarray(positions), size=5, axis=0, mode="nearest")
        if (len(positions) - 1) * FRAME_INTERVAL >= 60:
            long_enough["at_least_60s"] += 1
            dep = np.linalg.norm(smoothed - smoothed[0], axis=1).max() / scale
            length = np.linalg.norm(np.diff(smoothed, axis=0), axis=1).sum() / scale
            long_enough["and_departure_at_least_5um"] += int(dep >= 5.0)
            long_enough["and_departure_and_length_at_least_14um"] += int(dep >= 5.0 and length >= 14.0)
        # Use nonoverlapping 12-second steps; these are track segments in one embryo.
        for i in range(0, len(positions) - 6, 6):
            sample = smoothed[i : i + 7]
            avg = (sample.mean(axis=0) - CENTER) / ELLIPSE_RADII
            if abs(avg[0]) > 0.50:
                continue
            radial = abs(avg[1])
            velocity = (sample[-1, 0] - sample[0, 0]) / (scale * 6 * FRAME_INTERVAL)
            group = 0 if radial <= 0.28 else 1 if 0.62 <= radial <= 0.93 else None
            if group is not None:
                bins[(start + i + 3) // 30][group].append(velocity)
    by_time = []
    for i, (center, outside) in enumerate(bins):
        medians = [float(np.median(v)) if v else None for v in (center, outside)]
        by_time.append(
            {
                "seconds": [int(i * 60), int(min((i + 1) * 60, (frame_count - 1) * FRAME_INTERVAL))],
                "n_center_and_shell_segments": [len(center), len(outside)],
                "center_and_shell_median_axial_um_per_s": medians,
                "opposing": bool(min(len(center), len(outside)) >= 5 and medians[0] * medians[1] < 0),
            }
        )
    return dict(long_enough), by_time


def synthetic(add_circles, fade=False):
    """Calibrate image-level tracking on known paths plus independent image noise."""
    frames = 101
    rng = np.random.default_rng(582026)
    angle = 2 * np.pi * np.arange(frames) / 80
    phases = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    x = 27 * np.cos(angle[:, None] + phases)
    y = 27 * np.sin(angle[:, None] + phases)
    if not add_circles:
        y = np.broadcast_to(np.linspace(-37, 37, len(phases)), x.shape)
    trajectories = np.stack((x + 174, y + 90), axis=-1)
    yy, xx = np.indices(FRAME_SHAPE)
    background = 27.0 + 18.0 * ellipse_mask(1.0)
    output = []
    for t, points in enumerate(trajectories):
        image = background + rng.normal(0, 1.7, size=FRAME_SHAPE)
        if not fade or not 37 <= t <= 48:
            for px, py in points:
                image += 65 * np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / 5.1)
        output.append(image.clip(0, 255).astype(np.uint8))
    return output


def calibrate():
    out = {}
    for name, flags in (
        ("circle", (True, False)),
        ("axial_reversal", (False, False)),
        ("temporarily_invisible_circle", (True, True)),
    ):
        paths, stopped = track(synthetic(*flags))
        summary = evaluate(paths, 6.4)
        out[name] = {k: v for k, v in summary.items() if not k.endswith("_paths")}
        out[name]["termination_reasons"] = dict(stopped)
    return out


def run(raw, out):
    cv2.setNumThreads(1)
    controls = calibrate()
    for name in ("granule-plane.mov", "granule-volume.avi"):
        sources.read(raw, name)
    path = raw / "granule-plane.mov"
    frames = decode_movie(path)
    scale, bar = scale_bar(frames[0])
    main_paths, ended = track(frames)
    result = evaluate(main_paths, scale)
    sensitivity = {}
    for name, values in (
        ("closure_0p75_um", (0.75, None, None)),
        ("closure_1p5_um", (1.5, None, None)),
        ("stricter_appearance", (1.0, 0.84, 1.0)),
        ("smaller_mask", (1.0, 0.72, 0.93)),
    ):
        closure, sim, mask = values
        paths = track(frames, sim, mask)[0] if sim is not None else main_paths
        score = evaluate(paths, scale, closure)
        sensitivity[name] = {k: v for k, v in score.items() if not k.endswith("_paths")}
    coverage, directions = coverage_and_directions(main_paths, scale, len(frames))
    longest = sorted(main_paths, key=lambda item: len(item[1]), reverse=True)[:7]
    for start, xy in longest:
        assert start + len(xy) <= len(frames)
    summary = {
        "experiment": "E58",
        "source": "10.1371/journal.pone.0159917.s006",
        "biological_embryos": 1,
        "frame_count": len(frames),
        "acquisition_frame_interval_seconds": FRAME_INTERVAL,
        "duration_seconds": (len(frames) - 1) * FRAME_INTERVAL,
        "pixels_per_um": scale,
        "scale_bar_endpoints_and_row": bar,
        "scope_of_s3": "A rendered movie from volumetric imaging; planar video frames do not give full 3D particle positions.",
        "s3_media": video_info(raw / "granule-volume.avi"),
        "tracking_primary": {
            "ellipse_center": CENTER,
            "ellipse_radii_pixels": ELLIPSE_RADII,
            "minimum_correlation": 0.72,
            "redetection_frames": REDETECT_EVERY,
            "termination_reasons": dict(ended),
            **result,
        },
        "longest_example_tracks": [{"start_frame": a, "xy_pixels": b} for a, b in longest],
        "qualification_coverage": coverage,
        "minute_windows_and_tail": directions,
        "sensitivity": sensitivity,
        "synthetic_controls": controls,
        "checks": {
            "frames_and_scale_match_burned_in_movie": len(frames) == 213 and 6.1 <= scale <= 6.6,
            "rendered_circle_is_detected": controls["circle"]["loop_count"] >= 4,
            "return_along_a_line_is_rejected": controls["axial_reversal"]["loop_count"] == 0,
            "missing_middle_section_is_not_joined": controls["temporarily_invisible_circle"]["loop_count"]
            == 0,
            "all_starts_accounted_for": sum(ended.values()) == len(main_paths),
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, summary, __file__, sources.__file__)


if __name__ == "__main__":
    sources.run_one(run)
