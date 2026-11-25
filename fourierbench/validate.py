"""Independent analytic tests and numerical invariants; exits nonzero on failure."""

import json
import platform
from pathlib import Path
import numpy as np
from .optics import Grid, aperture, fft2c, pad, far_field, fourier_mask, filter_field, filtered_intensity, intensity_display


def zero_crossing(axis, values, expected):
    lo, hi = expected*0.65, expected*1.35
    indexes = np.where((axis[:-1] >= lo) & (axis[:-1] < hi) & (values[:-1]*values[1:] < 0))[0]
    if not len(indexes):
        raise AssertionError("No bracketed first zero")
    i = indexes[0]
    return float(axis[i] - values[i]*(axis[i+1]-axis[i])/(values[i+1]-values[i]))


def run(output=Path("reports/validation.json")):
    checks = []
    def check(name, measured, expected, tolerance, error=None, unit="relative error"):
        error = abs(measured-expected)/abs(expected) if error is None else error
        checks.append(dict(name=name, measured=float(measured), expected=float(expected),
                           error=float(error), tolerance=tolerance, error_unit=unit, passed=bool(error <= tolerance)))

    grid = Grid(256, 1.0, 8)
    axis = np.fft.fftshift(np.fft.fftfreq(grid.m, grid.dx))
    expected_ring = 3.8317059702075125/(2*np.pi*24)
    circle = aperture(grid, dict(kind="circle", radius=24), supersample=8)
    field = fft2c(pad(circle, grid.padding))
    measured_ring = zero_crossing(axis, field[grid.m//2].real, expected_ring)
    check("circular_aperture_first_dark_ring", measured_ring, expected_ring, 0.006)

    for width in (12, 24, 40):
        source = aperture(grid, dict(kind="slit", width=width, height=100))
        transform = fft2c(pad(source, grid.padding))
        expected = 1/width
        measured = zero_crossing(axis, transform[grid.m//2].real, expected)
        check(f"single_slit_first_zero_width_{width}", measured, expected, 0.003)

    # Independent double-slit expression from the actual single-slit transform:
    # I_double/(4 I_single) = cos^2(pi*d*f). Locate envelope-divided minima;
    # do not measure biased raw-intensity peaks under a sloping envelope.
    single = aperture(grid, dict(kind="slit", width=8, height=100))
    single_i = far_field(single, grid)[grid.m//2]
    for spacing in (32, 64):
        pair = aperture(grid, dict(kind="slits", width=8, height=100, spacing=spacing, count=2))
        row = far_field(pair, grid)[grid.m//2]
        valid = (axis >= 0) & (axis <= 0.1) & (single_i > single_i.max()*0.04)
        normalized = row[valid]/(4*single_i[valid])
        expected_curve = np.cos(np.pi*spacing*axis[valid])**2
        residual = np.max(np.abs(normalized-expected_curve))
        check(f"double_slit_analytic_modulation_spacing_{spacing}", residual, 0, 1e-11, residual, "absolute max error")
        positions = np.where(valid)[0]
        minima = positions[1:-1][(normalized[1:-1] < normalized[:-2]) & (normalized[1:-1] < normalized[2:])]
        period = float(np.median(np.diff(axis[minima])))
        check(f"double_slit_fringe_period_spacing_{spacing}", period, 1/spacing, 0.01)

    energy_source = float(np.sum(circle**2)*grid.dx**2)
    energy_far = float(far_field(circle, grid).sum()*grid.df**2)
    check("physical_parseval_energy", energy_far, energy_source, 1e-12)
    shifted = np.roll(circle, (17, -23), axis=(0, 1))
    original_i, shifted_i = far_field(circle, grid), far_field(shifted, grid)
    error = float(np.max(np.abs(original_i-shifted_i))/original_i.max())
    check("integer_shift_intensity_invariance", error, 0, 1e-12, error, "relative to peak")

    g = Grid(128, 1.0, 4)
    source = aperture(g, dict(kind="asymmetric"))
    original = far_field(source, g)
    # Periodic index reversal, NOT np.flip (which is off by one on even grids).
    inv = (-np.arange(g.m)) % g.m
    unshifted = np.fft.ifftshift(original)
    sym_err = float(np.max(np.abs(unshifted-unshifted[np.ix_(inv, inv)]))/original.max())
    check("real_amplitude_centrosymmetry", sym_err, 0, 1e-12, sym_err, "relative to peak")
    complement = far_field(1-source, g)[::g.padding, ::g.padding]
    original_native = original[::g.padding, ::g.padding]
    diff = np.abs(complement-original_native)
    diff[g.n//2, g.n//2] = 0
    babinet_error = float(diff.max()/original_native.max())
    check("babinet_nonzero_native_frequency_bins", babinet_error, 0, 1e-12, babinet_error, "relative to aperture peak")

    opened = filter_field(source, fourier_mask(g, "open"), g)
    error = float(np.max(np.abs(opened-source)))
    check("4f_open_mask_identity", error, 0, 1e-12, error, "absolute amplitude error")
    blocked = filtered_intensity(source, fourier_mask(g, "closed"), g, crop=False)
    check("4f_closed_mask_zero", float(blocked.max()), 0, 1e-24, float(blocked.max()), "absolute intensity error")
    mask = fourier_mask(g, "vertical_slit")
    spectral = fft2c(pad(source, g.padding))*mask
    expected_energy = float(np.sum(np.abs(spectral)**2))
    output_field = filter_field(source, mask, g, crop=False)
    check("4f_transmitted_energy", float(np.sum(np.abs(output_field)**2)), expected_energy, 1e-12)
    assert expected_energy <= np.sum(source**2)*(1+1e-12)

    # Analytic periodic sinusoidal grid: a vertical Fourier slit retains y
    # modulation (horizontal bars). Padding=1 here is an intentional exact
    # periodic test; all finite-scene review items use padding=4.
    periodic = Grid(128, 1, 1)
    x, y = periodic.xy()
    inp = 0.5+0.2*np.cos(2*np.pi*x/16)+0.2*np.cos(2*np.pi*y/16)
    for kind, coord in (("vertical_slit", y), ("horizontal_slit", x)):
        field = filter_field(inp, fourier_mask(periodic, kind, cutoff=0.01), periodic)
        expected = 0.5+0.2*np.cos(2*np.pi*coord/16)
        error = float(np.max(np.abs(field-expected)))
        check(f"grid_{kind}_orientation", error, 0, 1e-12, error, "absolute amplitude error")

    # Refining dx at fixed physical support checks boundary discretization.
    fine = Grid(512, 0.5, 4)
    fine_a = aperture(fine, dict(kind="circle", radius=24), supersample=4)
    fine_f = fft2c(pad(fine_a, fine.padding))
    fine_axis = np.fft.fftshift(np.fft.fftfreq(fine.m, fine.dx))
    fine_zero = zero_crossing(fine_axis, fine_f[fine.m//2].real, expected_ring)
    check("circle_first_zero_refined_grid", fine_zero, expected_ring, 0.006)
    check("circle_first_zero_resolution_agreement", measured_ring, fine_zero, 0.003)

    # Padding only adds samples: common Fourier coordinates must agree.
    small = Grid(128, 1, 2)
    large = Grid(128, 1, 4)
    p2 = far_field(source, small)
    p4 = far_field(source, large)[::2, ::2]
    error = float(np.max(np.abs(p2-p4))/p4.max())
    check("padding_common_frequency_agreement", error, 0, 1e-12, error, "relative to peak")

    # A finite FFT implements periodic coherent filtering. Check the actual
    # development scenes against twice the padding BEFORE accepting their items.
    # Tolerances are 1% RMS of the reference peak in linear intensity and 3%
    # RMS of the unit display range; neither is a claim of perceptual identity.
    from .items import generated_input
    filter_kinds = ["vertical_slit", "horizontal_slit", "vertical_slit", "horizontal_slit",
                    "pinhole", "blocked_centre", "off_axis_hole", "vertical_slit",
                    "horizontal_slit", "pinhole", "blocked_centre", "off_axis_hole"]
    coarse_g, reference_g = Grid(192, 1, 4), Grid(192, 1, 8)
    for i, kind in enumerate(filter_kinds):
        scene = "grid" if i < 7 else ("bars" if i < 9 else "shapes")
        period = 16+4*((i//2)%2)
        cutoff = 0.014 if "slit" in kind else 0.025
        source = generated_input(coarse_g, scene, period)
        coarse_i = filtered_intensity(source, fourier_mask(coarse_g, kind, cutoff, 1/period), coarse_g)
        reference_i = filtered_intensity(source, fourier_mask(reference_g, kind, cutoff, 1/period), reference_g)
        error = float(np.sqrt(np.mean((coarse_i-reference_i)**2))/reference_i.max())
        check(f"4f_padding_convergence_{i+1:02}_linear", error, 0, 0.01, error, "RMS / reference peak")
        display_error = float(np.sqrt(np.mean((intensity_display(coarse_i)-intensity_display(reference_i))**2)))
        check(f"4f_padding_convergence_{i+1:02}_log", display_error, 0, 0.03, display_error, "RMS / display range")

    result = {"schema_version": 1, "python": platform.python_version(), "numpy": np.__version__,
              "device": "CPU", "passed": all(c["passed"] for c in checks), "checks": checks}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    for c in checks:
        print(f"{'PASS' if c['passed'] else 'FAIL'} {c['name']}: error={c['error']:.3g} limit={c['tolerance']:.3g}")
    if not result["passed"]:
        raise SystemExit(1)
    return result
