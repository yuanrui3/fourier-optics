# Fourier-optics intuition benchmark

Status: Gate 1 development. No model calls, GPU use or main-run results.

## Predictions recorded before any model evaluation

1. Text-only twins will outperform image items.
2. The designated look-alike foil will be selected more often than its 25% random-choice rate.
3. Fourier-plane filtering will be the hardest family, with grid-and-slit items among the hardest.
4. Inverse matching will be harder than forward matching.

These are hypotheses, not promised outcomes. Report counterexamples and null results.

## Gate sequence

1. Validate the CPU simulator, generate 12 development examples per family, and
   obtain the owner's visual review. Gate 1 material is mutable development data.
2. After approval, complete roughly 100 base items/family (20 dev, 80 test), the
   text twins, visibility and position controls, and the evaluation harness.
   Research then-current official free model tiers, verify version identifiers,
   and attempt a 60-dev-item pilot within the zero-dollar budget. Report any
   access/key limitations honestly. Ask about GPU use and any paid model at Gate 2.
3. Freeze prompts, generator, exclusions and analysis before generating fresh
   test instances. Execute the approved run once and write reports/main.md plus
   a static results gallery. Do not interpret simulator checks as model results.

## Planned analysis

- Per-family accuracy and designated-foil selection with item-bootstrap 95% CIs.
- Paired image-minus-text, forward-minus-inverse and arm differences.
- Rotation/rescaling consistency grouped by originating item; bootstrap base
  items so correlated variants are never counted as independent observations.
- Linear-display controls, visibility-check performance and answer-position
  distributions. Report invalid outputs separately and count them as incorrect
  in the primary accuracy denominator. Do not silently drop hard items.
- Visibility filtering is a secondary, explicitly conditional analysis; raw
  accuracy remains primary. Same/different controls have 50% chance, unlike
  the four-choice physics items. Identical-option controls have no correct label.
- Freeze an exact test seed manifest only after prompt development. Current
  Gate 1 seeds are dev-only and must never enter the reported test set.
- Exclude reviewer answers, foil labels and generator metadata from model-facing
  requests. The code arm receives the same stimulus information plus Python
  execution, not privileged access to the answer-generating parameters.
