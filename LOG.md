# Decision log

- 2026-11-14: Reuse the existing empty local Git repository; no second checkout, push, global configuration or background service is needed.
- 2026-11-14: Complete Gate 1 only in this session; the owner's visual physics review precedes full-set and harness work.
- 2026-11-14: The scoped related-work audit found no specified stop-condition overlap; disclose its limits in docs/related.md rather than claim exhaustive novelty.
- 2026-11-14: Use the bundled Python runtime read-only and put all generated files inside this project; avoid installing or modifying system packages.
- 2026-11-14: Use NumPy for every numerical optical operation and Pillow only for raster layout; a plotting stack is unnecessary.
- 2026-11-14: Use a local CMD launcher because PowerShell script execution is disabled; leave execution policy and every system setting unchanged.
- 2026-11-14: Normalize each complete intensity plane to its own peak and apply log10(1+999 I/Imax)/3; preserve paired linear controls because dynamic range can change apparent difficulty.
- 2026-11-14: Use registered 4f coordinates, retaining complex output amplitude until squaring; this removes the relay's global inversion without hiding asymmetric-mask physics.
- 2026-11-14: Restrict complement questions to nonzero native DFT samples of a finite uniformly illuminated square; this makes Babinet equality exact at the stated samples instead of neglecting window sidelobes.
- 2026-11-14: Treat naive silhouette and shifted-intensity foils as explicitly constructed wrong candidates; record their provenance separately from physically propagated distractors.
- 2026-11-14: Reject inverse candidates with equivalent displayed spectra and all near-duplicate options; numerical distinctness remains separate from a model's visibility check.
- 2026-11-14: Validate 4f finite-domain error against doubled padding with pre-set 1% linear and 3% log RMS limits; padding alone is not an aliasing guarantee.
- 2026-11-14: Visual review replaced repeated grid setups, added orthogonal-stripe distractors, retained an Airy ring in inverse look-alike foils, and avoided DC/isolated-carrier near-equivalence in off-axis options.
- 2026-11-14: Complement items include the original native-sample pattern to isolate the complement rule; their wording specifies sampling without stating the answer.
- 2026-11-14: Keep the initial review generator dev-only and record the hypotheses now; defer model selection, API access, text twins and the 60-item pilot until after Gate 1 approval.

- 2026-11-15: User preference: open questionnaires and review galleries directly in the visible app panel when presenting them for review; a link alone was easy to miss.
- 2026-11-18: Research recent mathematical progress alongside pending Gate 1, as requested; keep all work CPU-only and local, without starting the full benchmark or changing the reviewed simulator.
- 2026-11-18: Prioritize identifiability after rendering, coherent-mask equivalences, and shortcut diagnostics; generic phase-retrieval theorems do not certify cropped four-choice images.
- 2026-11-18: Independently verify a known homometric six-slit pair, opposite-hole equality, periodic filtering formulas, finite-window Babinet, and the central-curvature/covariance identity; keep original figures and reproducible results separate from Gate 1 artifacts.
- 2026-11-18: Recommend separately scoring copyable invariance controls and adding conditional foil attraction before the main run; record these as proposals, leaving PLAN.md predictions and Gate 1 questions unchanged pending review.
- 2026-11-25: User authorized creating a public GitHub repository and pushing this project; publish source, documentation, research results and the Gate 1 review gallery, excluding the machine-specific console log and existing ignored secret/cache files.
- 2026-11-25: Preserve file bytes with .gitattributes so Git's automatic line-ending conversion cannot invalidate the saved source and artifact hashes.
