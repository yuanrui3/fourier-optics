# Fourier-optics intuition benchmark

CPU-only numerical groundwork and Gate 1 review material. No models have been
evaluated, no test items have been used, and no paid requests have been made.

Open [the Gate 1 review gallery](reports/gate1/index.html) in a browser. It is a
self-contained local HTML page with 72 development examples, six family contact
sheets, linear-display controls, and hidden reviewer answers/provenance.

## Reproduce

From this folder in PowerShell:

```powershell
.\run.cmd validate   # analytic checks and numerical invariants
.\run.cmd gate1      # validation, 72 dev examples, audit and contact sheets
.\run.cmd audit      # regenerate item records and verify saved image hashes
```

The launcher uses the installed Codex Python bundle read-only if available.
For a different interpreter, run `python -B -m fourierbench gate1` directly.
Runtime used here: Python 3.12.14,
NumPy 2.3.5 and Pillow 13.0.0; package versions are pinned in requirements.txt.
The simulator depends only on NumPy. Pillow handles image layout, not optics.
Arial font hashes are captured because font rasterization affects PNG bytes.
Nothing starts a background service or changes system configuration.

Each command recreates its reported numbers. `reports/validation.json` stores
measured values, expectations, errors and fixed tolerances. The gallery manifest
stores question text, option order, correct and foil labels, geometry, display
hashes and PNG hashes. Build provenance records source hashes and versions.

## Read next

- [Related work and overlap decision](docs/related.md)
- [Physical and display conventions](docs/conventions.md)
- [Gate 1 report](reports/gate1.md)
- [Mathematical research and audit, 18 November 2026](reports/math-research-2026-11-18/index.html) — recent primary research, derivations, and independent numerical diagnostics; reproduce with `.\run-research.cmd`.
- [Predictions and remaining work](PLAN.md)
- [Decision log](LOG.md)

Gate 1 is awaiting the owner's physics/visibility review. Full dev/test generation,
text twins, visibility and position controls, model adapters, pilot evaluation,
bootstrap analysis and the final findings report follow approval. The current
static page is a review gallery, not the Gate 3 model-results page.
