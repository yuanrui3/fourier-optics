# Physics, numerical and display conventions

## Physical model

Illumination is monochromatic, spatially coherent and uniform over the stated
source support. Transmission is real and lies in [0,1]. Polarization, vector
diffraction, near-field propagation, detector noise and lens aberrations are
outside this version. Source coordinates are arbitrary length units; frequency
coordinates are cycles per source unit. To map onto a physical focal plane,
use x_f = wavelength * focal_length * f_x (and likewise for y).

The far field is I = |F{A}|^2. The implementation uses centered NumPy FFTs with
orthonormal normalization, then multiplies the complex field by M*dx^2 for an
M-by-M padded array. Thus the result is a Riemann-sum Fourier transform with
physical integration weights: sum(|A|^2)*dx^2 = sum(I)*df^2, df=1/(M dx).
This is exact discrete Parseval conservation, not proof of continuum accuracy.

An ideal coherent 4f output is |F^-1{M F{A}}|^2. The field remains complex until
the final magnitude square; applying an asymmetric mask does not justify
discarding its imaginary part. Output coordinates are registered to the input,
removing the global inversion of the physical two-lens relay. Masks act on
amplitude, not intensity. Binary masks have transmission zero or one.

## Sampling and finite support

Review items use 192-by-192 source samples at dx=1, 4-by-4 subpixel averaging
of analytic aperture geometry, and 4x zero padding per dimension (768-square
FFT). The narrowest generated geometric features are several source pixels
wide. The simulation is still a sampled approximation to scalar diffraction;
"exact ground truth" means deterministic numerical answers within this model.

Padding samples the same far field more finely; it cannot recover undersampled
source geometry. Hard edges are not band limited. Validation therefore checks
both the known analytic zeros and a finer spatial grid. For coherent filtering,
finite FFT domains give periodic boundaries, and cropping discards light outside
the displayed output. Energy checks use the entire padded output, never only
the crop. Additional padding-convergence checks bound this approximation for
the development filter scenes. These checks are not a universal alias-free
guarantee for arbitrary future parameters.

## Display

Every question states the convention. The primary intensity mapping is

    g(I) = log10(1 + 999 * I/Imax) / 3.

The linear control is g(I)=I/Imax. Both map to grayscale [0,255]. Imax is taken
over the full computed intensity plane before cropping, separately for each
panel; absolute throughput is intentionally not tested. Source and mask panels
show linear amplitude transmission, white=1. An all-zero intensity is black.
No histogram equalization or per-crop contrast stretching is performed.

The source/output crop spans [-96,96) units. The frequency crop spans
[-0.125,0.125) cycles/unit on each axis. Axes use image coordinates: x increases
rightwards, y downwards, and positive described rotations are clockwise.
Nearest-neighbor enlargement preserves the computed samples. Contact sheets
are thumbnail previews; individual cards are the intended full-resolution
stimuli. Each card has four shuffled options, with no answer annotation.

## Babinet's principle: the finite-window caveat

For a finite illuminated square W, the complementary aperture is W-A, so
F(W-A)=F(W)-F(A). It is generally false that the intensities match everywhere
except a single centre pixel in a zero-padded image: F(W) has sidelobes.

The six complement examples compare only native Fourier samples k/(192 dx).
At every nonzero such two-dimensional DFT bin, F(W)=0 exactly. They still use
the padded FFT, then retain only these samples, hide DC, and repeat samples
as pixels without interpolation. The normalization uses the maximum over all
non-DC native samples before the frequency crop. Every complement question
states this exception. The result is a deliberately discrete Babinet test,
not a claim about arbitrary off-grid frequencies or a literal one-pixel beam stop.

## Distractors and inverse ambiguity

Families 1, 2 and 5 designate one naive appearance foil. Forward foils copy
the source silhouette; inverse foils threshold the displayed diffraction
image into a binary transmissive screen; filter foils leave the input unchanged.
These are deliberately wrong candidate constructions, not purported physical
forward solutions. Other options use related aperture or mask simulations.
Symmetry examples additionally include a translated-intensity rule-violation
foil. Its synthetic provenance is explicit in the reviewer manifest.

Every inverse item's alternative apertures are transformed and checked against
the target, because distinct apertures can be intensity-equivalent. In particular,
translations and inversion of real apertures must not be separate candidate
answers. Displayed options also undergo a pairwise RMS-distance audit. This
audit excludes numerical duplicates, not perceptual difficulty; the owner's
review and subsequent model same/different controls remain necessary.

## Reference equations

- [University of Texas: Two-Dimensional Fourier Optics](https://farside.ph.utexas.edu/teaching/315/Waves/node98.html)
  gives the aperture transform and circular-aperture diffraction relation.
- [Eric Aristidi: Fourier Optics course, coherent optical filtering](https://www-n.oca.eu/aristidi/Cours/FourierOptics_Course.pdf)
  describes Fourier-plane filtering and grid experiments.

No reference figures or photographs are included in the stimuli.
