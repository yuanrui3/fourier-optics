# Gate 1: simulator and visual-review package

**Awaiting the owner's review.** All 44 numerical checks passed;
72 development items are available, with 12 per family. There are no model
results, no paid API requests and no GPU use. No test items were generated.

Open the [review gallery](gate1/index.html). It includes full-resolution cards,
linear-display controls, and expandable answer keys and simulation metadata.
The [related-work note](../docs/related.md) found no stop-condition overlap in
the inspected sources, while acknowledging that it is not an exhaustive audit.

## Physics validation

Reproduce every value below with `.\run.cmd validate`.
Frequencies are cycles per source unit. Energy uses the stated integration
weights; errors are relative except shift error, which is relative to peak.

| Check | Measured | Expected | Error |
|---|---:|---:|---:|
| circular aperture first dark ring | 0.025411994 | 0.0254097894 | 8.68e-05 |
| single slit first zero width 40 | 0.025001562 | 0.025 | 6.25e-05 |
| double slit fringe period spacing 32 | 0.03125 | 0.03125 | 0 |
| double slit fringe period spacing 64 | 0.015625 | 0.015625 | 0 |
| physical parseval energy | 1783.53711 | 1783.53711 | 2.55e-16 |
| integer shift intensity invariance | 1.13758262e-15 | 0 | 1.14e-15 |

Additional checks cover real-amplitude centrosymmetry, sampled Babinet equality,
open/closed 4f masks, transmitted energy, grid/slit orientation, source-resolution
refinement and padding consistency. Doubling 4f padding for the 12 development
setups gives a worst linear-intensity RMS error of 0.009477 of the
reference peak and a worst log-display RMS error of 0.023014
of the display range. Limits were fixed at 0.01 and 0.03 respectively.
See [all measured checks and tolerances](validation.json).

## Contact sheets

Reproduce the counts, images and option-distance audit with `.\run.cmd gate1`.

| Family | Items | Contact sheets |
|---|---:|---|
| 1. Aperture to pattern | 12 | [Log](gate1/family-1-log.png) / [Linear](gate1/family-1-linear.png) |
| 2. Pattern to aperture | 12 | [Log](gate1/family-2-log.png) / [Linear](gate1/family-2-linear.png) |
| 3. Scale, rotation and shift | 12 | [Log](gate1/family-3-log.png) / [Linear](gate1/family-3-linear.png) |
| 4. Slits and gratings | 12 | [Log](gate1/family-4-log.png) / [Linear](gate1/family-4-linear.png) |
| 5. Fourier-plane filtering | 12 | [Log](gate1/family-5-log.png) / [Linear](gate1/family-5-linear.png) |
| 6. Symmetry and complements | 12 | [Log](gate1/family-6-log.png) / [Linear](gate1/family-6-linear.png) |

Each item has four seeded, shuffled options. Families 1, 2 and 5 mark a
designated naive appearance foil in the reviewer manifest. Forward and
inverse items share pair IDs. All options passed the distinctness audit; the
smallest pairwise log-display RMS distance is 0.065792. That numerical
distance is not a perceptual visibility guarantee. Same/different model
controls remain part of Gate 2.

## Decisions for the physics review

- Intensity uses `log10(1+999 I/Imax)/3`, normalized before cropping. Linear
  controls preserve geometry and option order. Aperture and mask maps show
  linear amplitude transmission.
- Babinet items use only non-DC native DFT samples under a finite square
  illumination window. The condition is stated in every such question; it is
  not an assertion about all frequencies of the padded image.
- 4f output coordinates remove the relay's global inversion. Real asymmetric
  masks retain complex fields before intensity is computed.
- Naive silhouettes and one symmetry-rule-violation foil are deliberately
  constructed wrong candidates. They are identified as such in provenance.

Please assess physics, option ambiguity, foil plausibility and visual legibility
before full-set/harness development. The full [conventions](../docs/conventions.md)
describe the sampled-model limits. Text twins, controls, model selection and the
60-item free-tier pilot are still pending Gate 1 approval.

Reproducibility check: `.\run.cmd audit` regenerates item records, checks saved
PNG hashes and verifies the recorded code and validation hashes.
