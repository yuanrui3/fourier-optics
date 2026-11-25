"""Numerics depend only on NumPy. Coordinates and frequencies use arbitrary units.

Arrays use image coordinates (x right, y down). Uniform coherent illumination,
real amplitude transmission, paraxial far field, and ideal coherent 4f filtering.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Grid:
    n: int = 192
    dx: float = 1.0
    padding: int = 4

    def __post_init__(self):
        if self.n < 8 or self.n % 2 or self.dx <= 0 or self.padding < 1:
            raise ValueError("Require even n >= 8, dx > 0, integer padding >= 1")
        if not isinstance(self.padding, int):
            raise ValueError("Padding must be an integer")

    @property
    def m(self):
        return self.n * self.padding

    @property
    def df(self):
        return 1 / (self.m * self.dx)

    def xy(self):
        axis = (np.arange(self.n) - self.n // 2) * self.dx
        return np.meshgrid(axis, axis)

    def frequencies(self):
        axis = np.fft.fftshift(np.fft.fftfreq(self.m, d=self.dx))
        return np.meshgrid(axis, axis)


def fft2c(field):
    return np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(field), norm="ortho"))


def ifft2c(spectrum):
    return np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(spectrum), norm="ortho"))


def pad(field, factor=4):
    if field.ndim != 2 or field.shape[0] != field.shape[1]:
        raise ValueError("Expected a square two-dimensional field")
    if not isinstance(factor, int) or factor < 1:
        raise ValueError("Padding factor must be a positive integer")
    n = field.shape[0]
    before = (factor * n - n) // 2
    after = factor * n - n - before
    return np.pad(field, ((before, after), (before, after)))


def crop_center(array, n):
    if n > min(array.shape):
        raise ValueError("Crop exceeds array")
    start = (array.shape[0] - n) // 2
    return array[start:start + n, start:start + n]


def far_field(amplitude, grid):
    """Riemann-sum Fourier transform: F = dx**2 sum A exp(-2pi i f.x).

    sum(abs(A)**2)*dx**2 == sum(I)*df**2 to roundoff (discrete Parseval).
    Absolute propagation prefactors are omitted; displayed patterns are relative.
    """
    if amplitude.shape != (grid.n, grid.n):
        raise ValueError("Amplitude does not match grid")
    transformed = fft2c(pad(amplitude, grid.padding)) * grid.m * grid.dx**2
    return np.abs(transformed)**2


def filter_field(amplitude, mask, grid, crop=True):
    """Ideal coherent 4f system in registered, parity-corrected coordinates.

    Mask is real amplitude transmission, including asymmetric off-axis masks.
    Keep the complex output until the final intensity operation.
    """
    if amplitude.shape != (grid.n, grid.n) or mask.shape != (grid.m, grid.m):
        raise ValueError("Field/mask shape does not match grid")
    if not np.isrealobj(mask) or np.any((mask < 0) | (mask > 1)):
        raise ValueError("This version accepts real masks with transmission in [0, 1]")
    output = ifft2c(fft2c(pad(amplitude, grid.padding)) * mask)
    return crop_center(output, grid.n) if crop else output


def filtered_intensity(amplitude, mask, grid, crop=True):
    return np.abs(filter_field(amplitude, mask, grid, crop=crop))**2


def aperture(grid, spec, supersample=4):
    """Cell-averaged real amplitude, rasterized from analytic geometry.

    Supersampling reduces boundary rasterization error, not Fourier-plane aliasing.
    Features must remain well resolved at the underlying dx.
    """
    x, y = grid.xy()
    result = np.zeros_like(x)
    offsets = ((np.arange(supersample) + 0.5) / supersample - 0.5) * grid.dx
    for oy in offsets:
        for ox in offsets:
            result += _geometry(x + ox, y + oy, spec)
    return result / supersample**2


def _geometry(x, y, spec):
    x = x - spec.get("shift_x", 0)
    y = y - spec.get("shift_y", 0)
    angle = np.deg2rad(spec.get("angle", 0))
    u = np.cos(angle) * x + np.sin(angle) * y
    v = -np.sin(angle) * x + np.cos(angle) * y
    kind = spec["kind"]
    if kind == "circle":
        return u*u + v*v <= spec.get("radius", 26)**2
    if kind == "ring":
        r2 = u*u + v*v
        return (r2 <= spec.get("radius", 32)**2) & (r2 >= spec.get("inner", 20)**2)
    if kind in ("square", "slit", "rectangle"):
        w = spec.get("width", 48)
        h = spec.get("height", w)
        return (np.abs(u) < w/2) & (np.abs(v) < h/2)
    if kind == "triangle":
        size = spec.get("size", 62)
        h = np.sqrt(3) * size / 2
        return (v >= -2*h/3) & (v <= h/3) & (np.abs(u) <= (v + 2*h/3)/np.sqrt(3))
    if kind == "slits":
        inside = np.zeros_like(u, dtype=bool)
        for centre in (np.arange(spec.get("count", 2)) - (spec.get("count", 2)-1)/2)*spec.get("spacing", 32):
            inside |= (np.abs(u-centre) < spec.get("width", 8)/2) & (np.abs(v) < spec.get("height", 80)/2)
        return inside
    if kind == "array":
        inside = np.zeros_like(u, dtype=bool)
        for cx, cy in spec["centres"]:
            inside |= _geometry(u-cx, v-cy, spec["element"])
        return inside
    if kind == "asymmetric":
        return ((u+22)**2+(v+16)**2 < 15**2) | ((u-24)**2+(v+7)**2 < 10**2) | ((u+8)**2+(v-26)**2 < 18**2)
    raise ValueError(f"Unknown aperture {kind}")


def fourier_mask(grid, kind, cutoff=0.018, offset=0.0625):
    fx, fy = grid.frequencies()
    if kind == "pinhole":
        value = fx*fx + fy*fy <= cutoff**2
    elif kind == "blocked_centre":
        value = fx*fx + fy*fy >= cutoff**2
    elif kind == "vertical_slit":
        value = np.abs(fx) <= cutoff
    elif kind == "horizontal_slit":
        value = np.abs(fy) <= cutoff
    elif kind == "off_axis_hole":
        value = (fx-offset)**2 + fy*fy <= cutoff**2
    elif kind == "open":
        value = np.ones_like(fx)
    elif kind == "closed":
        value = np.zeros_like(fx)
    else:
        raise ValueError(f"Unknown mask {kind}")
    return value.astype(float)


def intensity_display(intensity, mode="log", peak=None):
    """Fixed mapping: log10(1+999 I/Imax)/3, or linear I/Imax.

    Peak comes from the full computed plane before cropping unless supplied.
    An all-zero plane maps to black. No auto contrast after cropping or resizing.
    """
    values = np.asarray(intensity, dtype=float)
    if np.any(values < -1e-12) or not np.all(np.isfinite(values)):
        raise ValueError("Display expects finite nonnegative intensity")
    peak = float(values.max()) if peak is None else float(peak)
    relative = np.clip(values / peak, 0, 1) if peak > 0 else np.zeros_like(values)
    if mode == "linear":
        return relative
    if mode == "log":
        return np.log10(1 + 999 * relative) / 3
    raise ValueError("Mode must be log or linear")


def pattern_view(intensity, grid, mode="log", native_samples=False):
    # Fixed field of view: [-1/(8 dx), +1/(8 dx)) on each frequency axis.
    view = crop_center(intensity_display(intensity, mode), grid.m // 4)
    return view[::grid.padding, ::grid.padding] if native_samples else view


def complement_pattern(amplitude, grid):
    """Finite illuminated square W=1 on the source canvas, sampled at k/(n dx).

    F(W) is exactly zero at nonzero native DFT bins, even after zero padding.
    Hide DC and use the same unblocked peak for both complements. Interpolated
    frequencies between these bins do not satisfy this equality.
    """
    intensity = far_field(1-amplitude, grid)
    intensity[grid.m//2, grid.m//2] = 0
    return intensity
