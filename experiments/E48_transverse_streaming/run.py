"""Measure axial counterflow around the circumference of the published 3D PIV section."""

import argparse
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from experiments import measured_return_sources as sources
from experiments.common import save_summary
from experiments.return_energy_data import rgb

ROI = (650, 530, 984, 892)
DENSITY = 1000.
BAR_LEFT, BAR_RIGHT = 673, 968


def read_plane(image):
    left, top, right, bottom = ROI
    pixels = image[top:bottom, left:right]
    yy, xx = np.indices(pixels.shape[:2])
    x, y = left+xx, top+yy
    white = np.min(pixels, axis=2) > 242
    bx, by = x[white], y[white]

    def residual(p):
        cx, cy, rx, ry = p
        return np.hypot((bx-cx)/rx, (by-cy)/ry)-1

    fit = least_squares(residual, [810.,718.,146.,135.], bounds=([770,675,105,100],[850,755,185,175]))
    if not fit.success or not white.any():
        raise ValueError("Could not determine the marked embryo boundary")
    # Use only the transverse panel's own color scale. The longitudinal panel uses a different palette.
    # Trim the dark antialiased frame before decoding the color ramp.
    colorbar = np.median(image[913:923, BAR_LEFT:BAR_RIGHT], axis=0)
    colors = cKDTree(colorbar)
    distances, indices = colors.query(pixels.reshape(-1,3))
    speed_scale = np.linspace(-100,100,len(colorbar))
    speed = speed_scale[indices].reshape(x.shape)
    probe_x = np.array([682, 750, 820, 890, 959])
    _, decoded = colors.query(image[924,probe_x])
    legend_error = np.max(abs(speed_scale[decoded] - speed_scale[probe_x - BAR_LEFT]))
    return (x, y, speed, distances.reshape(x.shape)), fit.x, float(np.sqrt(np.mean(fit.fun**2))), float(legend_error)


def region_stats(v):
    if not v.size:
        return None
    m_per_s = v*1e-9
    return {
        "n_display_pixels": int(v.size), "mean_nm_per_s": float(np.mean(v)), "median_nm_per_s": float(np.median(v)),
        "fraction_at_colorbar_ends_within_2_nm_per_s": float(np.mean(np.abs(v)>=98)),
        "mean_axial_kinetic_density_J_per_m3": float(np.mean(.5*DENSITY*m_per_s**2)),
        "mean_axial_component_advective_flux_W_per_m2": float(np.mean(.5*DENSITY*m_per_s**3)),
    }


def angular_score(plane, ellipse, shade=25, shell=(.78,.92), shift=(0.,0.)):
    x, y, v, mismatch = plane
    cx, cy, rx, ry = ellipse
    dx, dy = (x-cx)/rx-shift[0], (y-cy)/ry-shift[1]
    radius = np.hypot(dx, dy)
    theta = np.mod(np.arctan2(dy, dx), 2*np.pi)
    sector = np.floor(theta * 12/(2*np.pi)).astype(int) % 12
    valid = mismatch <= shade
    core = radius <= .35
    annulus = (radius >= shell[0]) & (radius <= shell[1])
    medians = []
    for i in range(12):
        pair = []
        for region in (core, annulus):
            values = v[(sector==i) & region & valid]
            pair.append(float(np.median(values)) if values.size else None)
        medians.append(pair)
    available = [(core_v,shell_v) for core_v,shell_v in medians if core_v is not None and shell_v is not None]
    return {
        "rgb_tolerance": shade, "shell_radius_fraction": shell, "center_shift_in_radii": shift,
        "core_valid_fraction": float(valid[core].mean()), "shell_valid_fraction": float(valid[annulus].mean()),
        "core": region_stats(v[core & valid]), "shell": region_stats(v[annulus & valid]),
        "sector_medians_core_shell_nm_per_s": medians, "n_sectors_available": len(available),
        "n_sectors_core_posterior_shell_anterior": sum(a > 0 and b < 0 for a,b in available),
    }


def run(raw, out):
    image = rgb(sources.read(raw, "niwayama3.png"))
    plane, ellipse, fit_error, legend_error = read_plane(image)
    cases = {"primary": angular_score(plane, ellipse)}
    for shade in (15, 40):
        cases[f"rgb_{shade}"] = angular_score(plane, ellipse, shade=shade)
    for name, shell in (("inner_shell", (.72,.88)), ("outer_shell", (.82,.95))):
        cases[name] = angular_score(plane, ellipse, shell=shell)
    for name, shift in (("left",(-.05,0)), ("right",(.05,0)), ("up",(0,-.05)), ("down",(0,.05))):
        cases[name] = angular_score(plane, ellipse, shift=shift)
    reference = cases["primary"]
    report = {
        "experiment": "E48", "figure_doi": "10.1371/journal.pone.0159917.g003",
        "data_type": "One displayed transverse slice from 3D MuVi-SPIM/PIV at the C. elegans one-cell stage",
        "density_assumed_kg_per_m3": DENSITY, "ROI_xy_bounds_px": ROI,
        "calibration_bar_rows_cols_half_open": [[913,923],[BAR_LEFT,BAR_RIGHT]], "calibration_nm_per_s": [-100,100],
        "max_legend_error_on_unused_row_nm_per_s": legend_error,
        "ellipse_center_xy_radii_xy_px": ellipse.tolist(), "ellipse_rms_radial_residual": fit_error,
        "cases": cases,
        "energy_scope": "Displayed clipped velocities, assumed density. The axial part of the advected kinetic energy "
                        "excludes transverse motion and pressure and viscous work.",
        "checks": {
            "original_image_size": image.shape[:2] == (1008,1065),
            "dotted_outline_fit_within_five_percent_of_radius": fit_error < .05,
            "unused_legend_row_reproduces_signed_speed_scale": legend_error < 4,
            "primary_core_and_shell_colors_readable": min(reference["core_valid_fraction"], reference["shell_valid_fraction"]) > .80,
            "all_sectors_observed_in_primary_image": reference["n_sectors_available"] == 12,
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    save_summary(out, report, __file__, sources.__file__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=sources.RAW)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.raw, args.out)
