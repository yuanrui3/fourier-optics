# Related work and overlap check

Checked 2026-11-14 against the primary papers and public project/data pages below.

**GOBench** evaluates generated scenes involving direct light, reflection and
refraction, with human optical-authenticity ratings and model agreement with
those ratings. It does not describe simulated wave-optics aperture matching or
Fourier-plane filtering. Our proposed benchmark instead uses deterministic
scalar diffraction, numerical ground truth and discrete answers, without
subjective image-quality judgments. Sources: [paper, sections 1–2](https://arxiv.org/html/2506.00991v1)
and [2026 journal revision](https://doi.org/10.1016/j.jvcir.2026.104885).

**SeePhys** collects 2,000 physics questions from educational sources across
seven domains, with vision-essential and vision-optional problems and several
input modalities. Its public dataset includes optics and diffraction questions;
it would be wrong to claim diffraction reasoning itself is new. The inspected
examples ask for quantities from diagrams, rather than matching freshly
simulated two-dimensional aperture/intensity images. Our distinction is a
procedural stimulus generator, controlled visual foils and paired physical
transformations. Text/image comparisons are also prior art, not our novelty.
Sources: [paper, sections 3–4](https://arxiv.org/html/2505.19099v1),
[official dataset](https://huggingface.co/datasets/SeePhys/SeePhys).

**ImagingBench** is the closest conceptual neighbor: it evaluates computational
imaging, including computer-generated holography, lensless reconstruction and
optical aberration correction, under Expert, Planner and Forward protocols.
Its published task table specifies image reconstruction/generation and lens
design, not four-choice aperture/diffraction matching or an input-plus-4f-mask
output-selection task. Our proposed contribution is a narrower diagnostic of
visual Fourier intuition, with appearance-based foils, visibility controls and
paired forward/inverse questions. We should not claim to be the first
physics-grounded imaging benchmark. Source: [paper, Table II and section III-B](https://arxiv.org/html/2607.07189v1).

**Decision:** no specified stop-condition overlap was found in these published
task descriptions and inspected public examples; proceed to simulator validation.
This is a scoped literature check, not proof that no individual SeePhys question
overlaps. Its complete image corpus and ImagingBench's unreleased evaluation
infrastructure have not been audited. The dataset search endpoint was unavailable
through the web tool. If later inspection identifies either exact simulated task,
stop and bring the evidence to the owner before continuing.
