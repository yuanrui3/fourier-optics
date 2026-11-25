"""Gate 1 development examples. This module has no model/API integration."""

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import numpy as np
from .optics import (Grid, aperture, crop_center, far_field, fft2c, pad,
                     fourier_mask, filtered_intensity, intensity_display, pattern_view)

DEV_SEED = 20261114
FAMILIES = {
    1: "Aperture to pattern", 2: "Pattern to aperture", 3: "Scale, rotation and shift",
    4: "Slits and gratings", 5: "Fourier-plane filtering", 6: "Symmetry and complements",
}
CONVENTION = (
    "Intensity display: g=log10(1+999 I/Imax)/3; each full plane is normalized to its own peak "
    "before cropping. Source and mask panels show linear amplitude transmission (white=1). "
    "Source/output field: 192 units across; frequency field: [-0.125,0.125) cycles/unit on both axes. "
    "Coordinates: x right, y down. All panels in the same plane share a scale."
)
LINEAR_CONVENTION = CONVENTION.replace("g=log10(1+999 I/Imax)/3", "g=I/Imax (linear control)")


def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array, dtype="<f8").tobytes()).hexdigest()


@dataclass
class Panel:
    label: str
    log: np.ndarray
    linear: np.ndarray
    provenance: dict

    def record(self):
        return {"label": self.label, "provenance": self.provenance,
                "display_sha256": {"log": digest(self.log), "linear": digest(self.linear)}}


@dataclass
class Item:
    family: int
    index: int
    prompt: str
    inputs: list
    options: list
    metadata: dict = field(default_factory=dict)
    correct: int = 0
    foil: int | None = None
    pair_id: str | None = None

    @property
    def id(self):
        return f"dev-f{self.family}-{self.index+1:03}"

    def shuffle(self):
        rng = np.random.default_rng(np.random.SeedSequence([DEV_SEED, self.family, self.index]))
        order = rng.permutation(4).tolist()
        self.options = [self.options[i] for i in order]
        self.correct = order.index(self.correct)
        self.foil = order.index(self.foil) if self.foil is not None else None
        for letter, panel in zip("ABCD", self.options):
            panel.label = letter
        self.metadata["shuffle_order"] = order
        return self

    def convention(self, mode="log"):
        value = CONVENTION if mode == "log" else LINEAR_CONVENTION
        if self.metadata.get("normalization_override"):
            value = value.replace("each full plane is normalized to its own peak before cropping",
                                  "each pattern uses its maximum non-DC native sample before cropping")
        return value

    def record(self):
        return {"id": self.id, "split": "dev", "family": self.family, "family_name": FAMILIES[self.family],
                "seed": DEV_SEED, "pair_id": self.pair_id, "question": self.prompt,
                "display_convention": self.convention(), "linear_display_convention": self.convention("linear"),
                "answer": "ABCD"[self.correct], "look_alike_foil": "ABCD"[self.foil] if self.foil is not None else None,
                "inputs": [p.record() for p in self.inputs], "options": [p.record() for p in self.options],
                "metadata": self.metadata}


def source_panel(amplitude, label="Aperture", provenance=None):
    return Panel(label, amplitude.copy(), amplitude.copy(), provenance or {"kind": "amplitude_transmission"})


def spectrum_panel(amplitude, grid, label="Pattern", spec=None, native=False, hide_dc=False):
    intensity = far_field(amplitude, grid)
    peak = float(intensity.max())
    if hide_dc:
        intensity[grid.m//2, grid.m//2] = 0
        # Only native bins are visible, so normalize to the maximum of those bins.
        # This is the explicit Babinet exception documented in each question.
        peak = float(intensity[::grid.padding, ::grid.padding].max())
    views = []
    for mode in ("log", "linear"):
        displayed = intensity_display(intensity, mode, peak=peak)
        viewed = crop_center(displayed, grid.m//4)
        if native:
            viewed = viewed[::grid.padding, ::grid.padding]
            # Exact nearest-neighbor repetition to common panel size; no invented samples.
            viewed = np.repeat(np.repeat(viewed, grid.padding, 0), grid.padding, 1)
        views.append(viewed)
    return Panel(label, *views, {"kind": "far_field", "aperture": spec,
                               "amplitude_sha256": digest(amplitude), "native_samples": native, "dc_hidden": hide_dc})


def output_panel(amplitude, grid, mask_kind, cutoff=0.018, offset=0.0625):
    mask = fourier_mask(grid, mask_kind, cutoff, offset)
    # Normalize by the full output plane, not the cropped region.
    intensity = filtered_intensity(amplitude, mask, grid, crop=False)
    views = [crop_center(intensity_display(intensity, mode), grid.n) for mode in ("log", "linear")]
    return Panel("Output", *views, {"kind": "4f_intensity", "mask": mask_kind,
                                  "cutoff": cutoff, "offset": offset, "input_sha256": digest(amplitude)})


def base_specs():
    return [
        {"kind": "circle", "radius": 25},
        {"kind": "square", "width": 47},
        {"kind": "slit", "width": 11, "height": 91, "angle": 18},
        {"kind": "triangle", "size": 68, "angle": 12},
        {"kind": "ring", "radius": 33, "inner": 24},
        {"kind": "array", "centres": [[-28, 0], [28, 0]], "element": {"kind": "circle", "radius": 14}},
        {"kind": "array", "centres": [[-25, -25], [25, -25], [-25, 25], [25, 25]], "element": {"kind": "circle", "radius": 11}},
        {"kind": "array", "centres": [[-28, -12], [28, 12]], "element": {"kind": "square", "width": 23}},
        {"kind": "slits", "width": 9, "height": 78, "count": 2, "spacing": 38, "angle": 35},
        {"kind": "array", "centres": [[-28, 0], [28, 0]], "element": {"kind": "triangle", "size": 29}, "angle": 15},
        {"kind": "array", "centres": [[-30, 0], [30, 0]], "element": {"kind": "ring", "radius": 19, "inner": 12}},
        {"kind": "slits", "width": 7, "height": 74, "count": 5, "spacing": 23},
    ]


def scaled(spec, factor):
    spec = deepcopy(spec)
    for key in ("radius", "inner", "width", "height", "size", "spacing", "shift_x", "shift_y"):
        if key in spec:
            spec[key] *= factor
    if "centres" in spec:
        spec["centres"] = [[x*factor, y*factor] for x, y in spec["centres"]]
        spec["element"] = scaled(spec["element"], factor)
    return spec


def matching_items(grid):
    specs = base_specs()
    for i, spec in enumerate(specs):
        a = aperture(grid, spec)
        scale_spec = scaled(spec, 0.66)
        other_spec = specs[(i+3) % len(specs)]
        other_a = aperture(grid, other_spec)
        scale_a = aperture(grid, scale_spec)
        correct = spectrum_panel(a, grid, spec=spec)
        # The intentionally naive foil is a source-plane silhouette placed in
        # the candidate pattern panel. Its provenance never claims it is a DFT.
        foil = Panel("Foil", intensity_display(a*a), intensity_display(a*a, "linear"),
                     {"kind": "naive_source_silhouette", "aperture": spec})
        item = Item(1, i, "Under uniform coherent illumination, which far-field intensity pattern does this aperture produce?",
                    [source_panel(a, provenance={"kind": "aperture", "spec": spec})],
                    [correct, foil, spectrum_panel(scale_a, grid, spec=scale_spec), spectrum_panel(other_a, grid, spec=other_spec)],
                    {"aperture": spec}, foil=1, pair_id=f"forward-inverse-{i+1:03}")
        yield item.shuffle()

        # Binary amplitude foil avoids a unique gray-scale cue in inverse items.
        lookalike = (correct.log >= 0.40).astype(float)
        candidate_arrays = [a, lookalike, scale_a, other_a]
        # Compare spectra numerically: reject phase-retrieval equivalences among
        # candidate apertures, even when the source images look different.
        spectra = [pattern_view(far_field(arr, grid), grid) for arr in candidate_arrays]
        distances = [float(np.sqrt(np.mean((spectra[0]-p)**2))) for p in spectra[1:]]
        if min(distances) < 0.02:
            raise AssertionError(f"Inverse options nearly degenerate for {i}: {distances}")
        item = Item(2, i, "Which of these candidate amplitude apertures produces the shown far-field intensity pattern?",
                    [spectrum_panel(a, grid, spec=spec)],
                    [source_panel(a, provenance={"kind": "aperture", "spec": spec}),
                     source_panel(lookalike, provenance={"kind": "thresholded_pattern_silhouette", "threshold": 0.40, "source_spec": spec}),
                     source_panel(scale_a, provenance={"kind": "aperture", "spec": scale_spec}),
                     source_panel(other_a, provenance={"kind": "aperture", "spec": other_spec})],
                    {"aperture": spec, "inverse_candidate_spectrum_rms": distances}, foil=1, pair_id=f"forward-inverse-{i+1:03}")
        yield item.shuffle()


def transformation_items(grid):
    for i in range(12):
        spec = {"kind": "slit", "width": 16+2*(i%4), "height": 60+4*(i%3), "angle": 10+5*(i%4)}
        a = aperture(grid, spec)
        if i < 4:
            factor = (1.5, 0.7, 1.4, 0.75)[i]
            change = f"Scale both aperture dimensions by {factor:g}, keeping its centre fixed."
            target = scaled(spec, factor)
            candidates = [target, spec, scaled(spec, 1/factor), dict(spec, angle=spec["angle"]+90)]
            operation = {"type": "scale", "factor": factor}
        elif i < 8:
            angle = (30, 45, 60, 90)[i-4]
            change = f"Rotate the aperture {angle} degrees clockwise about its centre."
            target = dict(spec, angle=spec["angle"]+angle)
            # At 90 degrees the opposite rotation is intensity-equivalent; avoid it.
            candidates = [target, spec, dict(spec, angle=spec["angle"]+angle/2), scaled(spec, 0.65)]
            operation = {"type": "rotation", "clockwise_degrees": angle}
        else:
            shift_x, shift_y = (12+3*(i-8), 8-4*(i-8))
            change = f"Translate the aperture by ({shift_x}, {shift_y}) source units, without clipping it."
            target = dict(spec, shift_x=shift_x, shift_y=shift_y)
            candidates = [target, scaled(spec, 0.65), scaled(spec, 1.4), dict(spec, angle=spec["angle"]+90)]
            operation = {"type": "translation", "x": shift_x, "y": shift_y}
        yield Item(3, i, f"The original aperture and pattern are shown. {change} Which intensity pattern results?",
                   [source_panel(a, "Original aperture"), spectrum_panel(a, grid, "Original pattern", spec)],
                   [spectrum_panel(aperture(grid, s), grid, spec=s) for s in candidates],
                   {"original": spec, "target": target, "operation": operation}).shuffle()


def slit_items(grid):
    for i in range(12):
        spec = {"kind": "slits", "width": 7+(i%3), "height": 72, "count": 2, "spacing": 25+2*(i%4)}
        if i < 4:
            target = dict(spec, spacing=spec["spacing"]*1.6)
            alternatives = [spec, dict(spec, spacing=spec["spacing"]*0.65), dict(spec, width=spec["width"]*1.8)]
            instruction = f"Increase centre-to-centre spacing from {spec['spacing']:g} to {target['spacing']:g}; keep slit width and count fixed."
            concept = "spacing_vs_fringe_period"
        elif i < 8:
            target = dict(spec, count=4+(i%2))
            alternatives = [spec, dict(spec, count=3), dict(spec, count=target["count"], spacing=spec["spacing"]*0.7)]
            instruction = f"Increase the number of slits from 2 to {target['count']}; keep slit width and centre spacing fixed."
            concept = "count_vs_fringe_sharpness"
        else:
            target = dict(spec, width=spec["width"]*1.8)
            alternatives = [spec, dict(spec, width=spec["width"]*0.6), dict(spec, spacing=spec["spacing"]*1.6)]
            instruction = f"Increase slit width from {spec['width']:g} to {target['width']:g}; keep slit count and centre spacing fixed."
            concept = "width_vs_envelope"
        a = aperture(grid, spec)
        yield Item(4, i, f"The original grating and pattern are shown. {instruction} Choose the new far-field pattern.",
                   [source_panel(a, "Original grating"), spectrum_panel(a, grid, "Original pattern", spec)],
                   [spectrum_panel(aperture(grid, s), grid, spec=s) for s in [target]+alternatives],
                   {"original": spec, "target": target, "concept": concept}).shuffle()


def generated_input(grid, kind, period=16):
    x, y = grid.xy()
    # Raised-cosine taper prevents a hard outer window from dominating filtering.
    window = np.clip((80-np.abs(x))/12, 0, 1)*np.clip((80-np.abs(y))/12, 0, 1)
    if kind == "grid":
        image = 0.5+0.23*np.cos(2*np.pi*x/period)+0.23*np.cos(2*np.pi*y/period)
    elif kind == "bars":
        image = 0.5+0.45*np.cos(2*np.pi*(x+0.35*y)/period)
    elif kind == "shapes":
        image = aperture(grid, {"kind": "asymmetric"})
    else:
        raise ValueError(kind)
    return image*window


def filter_items(grid):
    kinds = ["vertical_slit", "horizontal_slit", "vertical_slit", "horizontal_slit",
             "pinhole", "blocked_centre", "off_axis_hole", "vertical_slit",
             "horizontal_slit", "pinhole", "blocked_centre", "off_axis_hole"]
    all_kinds = ["pinhole", "blocked_centre", "vertical_slit", "horizontal_slit", "off_axis_hole"]
    for i, kind in enumerate(kinds):
        input_kind = "grid" if i < 7 else ("bars" if i < 9 else "shapes")
        period = 16+4*((i//2)%2)
        a = generated_input(grid, input_kind, period)
        cutoff = 0.014 if "slit" in kind else 0.025
        offset = 1/period
        correct = output_panel(a, grid, kind, cutoff, offset)
        foil = Panel("Foil", intensity_display(a*a), intensity_display(a*a, "linear"),
                     {"kind": "naive_unchanged_input", "input_kind": input_kind})
        distractors = []
        orthogonal = {"vertical_slit": "horizontal_slit", "horizontal_slit": "vertical_slit"}.get(kind)
        priority = ([orthogonal] if orthogonal else [])+[k for k in all_kinds if k != orthogonal]
        if kind == "off_axis_hole":
            # Passing DC or one isolated carrier can give the same envelope;
            # prefer visibly different stripe outputs over that near-equivalence.
            priority = ["vertical_slit", "horizontal_slit", "blocked_centre", "pinhole"]
        for alternative in priority:
            if alternative == kind:
                continue
            panel = output_panel(a, grid, alternative, cutoff, offset)
            if all(np.sqrt(np.mean((panel.log-p.log)**2)) >= 0.06 for p in [correct, foil]+distractors):
                distractors.append(panel)
            if len(distractors) == 2:
                break
        if len(distractors) < 2:
            raise AssertionError(f"Cannot create distinct filter options for {i}")
        mask = fourier_mask(grid, kind, cutoff, offset)
        viewed_mask = crop_center(mask, grid.m//4)
        yield Item(5, i,
                   "The input amplitude and Fourier-plane amplitude mask are shown. Which output intensity results in an ideal coherent 4f system? Output coordinates are registered to the input (the relay's global inversion is removed).",
                   [source_panel(a, "Input amplitude"), source_panel(viewed_mask, "Fourier mask")],
                   [correct, foil]+distractors,
                   {"input": input_kind, "period": period, "mask": kind, "cutoff": cutoff, "offset": offset,
                    "classic_grid_slit": input_kind == "grid" and "slit" in kind}, foil=1).shuffle()


def symmetry_items(grid):
    for i in range(12):
        spec = {"kind": "triangle", "size": 54+4*(i%3), "angle": 13+11*i} if i%2 else {"kind": "asymmetric", "angle": 9+13*i}
        a = aperture(grid, spec)
        if i < 6:
            correct = spectrum_panel(a, grid, spec=spec)
            shifted = Panel("Foil", np.roll(correct.log, 22, axis=1), np.roll(correct.linear, 22, axis=1),
                            {"kind": "rule_violation_shifted_intensity", "shift_pixels": 22})
            silhouette = Panel("Foil", intensity_display(a*a), intensity_display(a*a, "linear"),
                               {"kind": "naive_source_silhouette", "aperture": spec})
            other = scaled(spec, 0.7) if spec["kind"] != "asymmetric" else dict(spec, angle=spec["angle"]+55)
            prompt = "This real amplitude aperture is not symmetric under a 180-degree rotation. Which complete far-field intensity pattern is consistent with it? The optical axis stays at the panel centre."
            options = [correct, shifted, silhouette, spectrum_panel(aperture(grid, other), grid, spec=other)]
            inputs = [source_panel(a)]
            metadata = {"concept": "centrosymmetry", "aperture": spec,
                        "exception": "Includes an explicitly constructed shifted-intensity rule-violation foil, not a simulated real-aperture far field."}
        else:
            # Exact comparison only at native bins where the illuminated square's
            # transform vanishes. All candidate spectra use this same sampling.
            correct = spectrum_panel(1-a, grid, native=True, hide_dc=True, spec={"complement_of": spec})
            other = dict(spec, angle=spec["angle"]+45)
            third = {"kind": "ring", "radius": 30, "inner": 19}
            fourth = {"kind": "slits", "width": 9, "height": 68, "spacing": 36, "count": 3}
            options = [correct]+[spectrum_panel(aperture(grid, s), grid, native=True, hide_dc=True, spec=s) for s in (other, third, fourth)]
            inputs = [source_panel(a, "Original aperture"),
                      spectrum_panel(a, grid, label="Original pattern", native=True, hide_dc=True, spec=spec),
                      source_panel(1-a, "Complementary screen")]
            prompt = (
                "Choose the complementary screen's diffraction pattern. Illumination is uniform over the displayed 192-unit square. "
                "All options show only frequency samples k/192 (repeated as pixels); DC is hidden. "
                "Normalize using the maximum over all non-DC native samples before cropping."
            )
            metadata = {"concept": "babinet_native_bins", "aperture": spec, "native_df": 1/grid.n,
                        "normalization_override": "maximum over all non-DC native samples"}
        yield Item(6, i, prompt, inputs, options, metadata).shuffle()


def generate():
    grid = Grid()
    yield from matching_items(grid)
    yield from transformation_items(grid)
    yield from slit_items(grid)
    yield from filter_items(grid)
    yield from symmetry_items(grid)


def audit(items):
    records = []
    signatures = set()
    for item in items:
        signature = (item.family, item.prompt, tuple(digest(p.log) for p in item.inputs), digest(item.options[item.correct].log))
        if signature in signatures:
            raise AssertionError(f"Duplicate physical question in {item.id}")
        signatures.add(signature)
        rms = [float(np.sqrt(np.mean((a.log-b.log)**2))) for i, a in enumerate(item.options) for b in item.options[i+1:]]
        minimum = min(rms)
        if minimum < 0.02:
            raise AssertionError(f"Near-duplicate options in {item.id}: min RMS {minimum:.5f}")
        for p in item.inputs+item.options:
            for values in (p.log, p.linear):
                if not np.all(np.isfinite(values)) or values.min() < 0 or values.max() > 1+1e-12:
                    raise AssertionError(f"Invalid rendered intensity in {item.id}")
        records.append({"id": item.id, "min_pairwise_log_rms": minimum, "passed": True})
    counts = {str(f): sum(i.family == f for i in items) for f in FAMILIES}
    if any(n != 12 for n in counts.values()) or len({i.id for i in items}) != 72:
        raise AssertionError("Gate 1 needs exactly 12 unique items per family")
    return {"passed": True, "counts": counts, "items": records,
            "note": "Numerical distinctness is not a model visibility test; visual review and model controls remain required."}
