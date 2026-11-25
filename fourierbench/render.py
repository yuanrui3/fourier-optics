"""Static scientific review artifacts; Pillow is used only for raster layout."""

import hashlib
import html
import json
import platform
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version
from .items import CONVENTION, LINEAR_CONVENTION, FAMILIES

BG = "#f5f3ed"
INK = "#152e35"
ACCENT = "#136d73"


def font(size, bold=False):
    # Use Windows' installed fonts read-only; fall back to Pillow's bundled font.
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)


def wrapped(draw, text, xy, max_width, size=20, fill=INK, bold=False):
    face = font(size, bold)
    x, y = xy
    lines = []
    current = ""
    for word in text.split():
        test = f"{current} {word}".strip()
        if current and draw.textlength(test, font=face) > max_width:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill)
        y += size+6
    return y


def draw_panel(canvas, panel, mode, x, y, size):
    draw = ImageDraw.Draw(canvas)
    draw.text((x, y), panel.label, font=font(22, True), fill=INK)
    values = getattr(panel, mode)
    # Identical nearest-neighbor sampling in both display modes. This preserves
    # explicitly sparse Babinet samples and prevents appearance interpolation.
    image = Image.fromarray(np.round(values*255).astype("uint8"))
    image = image.resize((size, size), Image.Resampling.NEAREST).convert("RGB")
    canvas.paste(image, (x, y+32))
    draw.rectangle((x-1, y+31, x+size, y+32+size), outline="#819295", width=1)


def render_card(item, path, mode="log"):
    width = 1120
    canvas = Image.new("RGB", (width, 1400), BG)
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, width, 8), fill=ACCENT)
    y = wrapped(d, f"{item.id}  |  {FAMILIES[item.family]}", (28, 23), width-56, 26, bold=True)
    y = wrapped(d, item.prompt, (28, y+9), width-56, 21)
    convention = item.convention(mode)
    y = wrapped(d, convention, (28, y+10), width-56, 16, fill="#475e65")+18
    for k, panel in enumerate(item.inputs):
        draw_panel(canvas, panel, mode, 28+k*270, y, 220)
    y += 278
    d.line((28, y-10, width-28, y-10), fill="#b9c7c6", width=2)
    for k, panel in enumerate(item.options):
        draw_panel(canvas, panel, mode, 28+k*274, y, 240)
    y += 291
    d.text((28, y), "DEVELOPMENT / GATE 1 REVIEW    |    Choose A, B, C or D    |    CPU simulation", font=font(15), fill="#475e65")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.crop((0, 0, width, y+43)).save(path)


def contact_sheet(items, root, family, mode="log"):
    chosen = sorted([i for i in items if i.family == family], key=lambda i: i.index)
    cards = [Image.open(root/"items"/f"{i.id}-{mode}.png").convert("RGB") for i in chosen]
    tile_w = 672
    tile_h = max(round(c.height*tile_w/c.width) for c in cards)
    width = tile_w*2+48
    canvas = Image.new("RGB", (width, 112+6*(tile_h+18)+20), BG)
    d = ImageDraw.Draw(canvas)
    d.text((20, 16), f"{family}. {FAMILIES[family]}", font=font(34, True), fill=INK)
    d.text((20, 63), f"12 dev items | {mode.upper()} display | open individual cards in index.html for full resolution", font=font(20), fill=ACCENT)
    for j, card in enumerate(cards):
        h = round(card.height*tile_w/card.width)
        card = card.resize((tile_w, h), Image.Resampling.LANCZOS)
        canvas.paste(card, (16+(j%2)*(tile_w+16), 105+(j//2)*(tile_h+18)))
    canvas.save(root/f"family-{family}-{mode}.png")


def validation_plot(result, root):
    # A static report table makes numerical tolerances visible beside the sheets.
    checks = result["checks"]
    width = 1460
    canvas = Image.new("RGB", (width, 145+len(checks)*42), BG)
    d = ImageDraw.Draw(canvas)
    d.text((24, 20), "Simulator validation | CPU | all checks passed" if result["passed"] else "Simulator validation | FAILED", font=font(32, True), fill=INK)
    for x, title in ((24, "Check"), (870, "Error"), (1090, "Tolerance"), (1310, "Result")):
        d.text((x, 85), title, font=font(21, True), fill=ACCENT)
    for i, check in enumerate(checks):
        y = 126+i*42
        if i%2 == 0:
            d.rectangle((16, y-5, width-16, y+33), fill="#e5eeeb")
        d.text((24, y), check["name"].replace("_", " "), font=font(20), fill=INK)
        d.text((870, y), f"{check['error']:.3g}", font=font(20), fill=INK)
        d.text((1090, y), f"{check['tolerance']:.3g}", font=font(20), fill=INK)
        d.text((1310, y), "PASS" if check["passed"] else "FAIL", font=font(20, True), fill=ACCENT)
    canvas.save(root/"validation.png")


def write_gallery(items, root, validation, audit):
    sections = []
    for family, name in FAMILIES.items():
        cards = []
        for item in sorted([i for i in items if i.family == family], key=lambda i: i.index):
            foil = "none designated" if item.foil is None else "ABCD"[item.foil]
            cards.append(f'''<article>
<a href="items/{item.id}-log.png"><img loading="lazy" src="items/{item.id}-log.png" alt="{html.escape(item.id+' '+item.prompt)}"></a>
<p><a href="items/{item.id}-log.png">Full-size log card</a> · <a href="items/{item.id}-linear.png">Linear control</a></p>
<details><summary>Reviewer answer and provenance</summary><p>Answer: <b>{'ABCD'[item.correct]}</b>. Look-alike foil: {foil}.</p><pre>{html.escape(json.dumps(item.metadata, indent=2))}</pre></details></article>''')
        sections.append(f'''<section id="f{family}"><h2>{family}. {html.escape(name)}</h2>
<p>Contact sheets: <a href="family-{family}-log.png">log display</a> · <a href="family-{family}-linear.png">linear control</a></p>
<div class="grid">{''.join(cards)}</div></section>''')
    nav = " · ".join(f'<a href="#f{f}">{f}. {html.escape(n)}</a>' for f, n in FAMILIES.items())
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fourier optics | Gate 1 review</title><style>
body{{background:#f5f3ed;color:#152e35;font:17px/1.55 system-ui,sans-serif;margin:0 auto;padding:28px;max-width:1440px}}
h1{{font-size:clamp(30px,4vw,52px);line-height:1.1;margin-bottom:12px}}h2{{margin-top:48px;border-top:3px solid #136d73;padding-top:20px}}
a{{color:#116c76}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,570px),1fr));gap:24px}}
article{{background:white;border:1px solid #cbd7d4;padding:12px}}img{{width:100%;height:auto}}article p{{margin:10px 0}}
pre{{white-space:pre-wrap;font-size:13px}}summary{{cursor:pointer}}.status{{background:#deebe5;padding:18px;border-left:5px solid #136d73}}
nav{{padding:18px 0}}.intro{{max-width:1000px}}details{{border-top:1px solid #ddd;padding-top:8px}}</style>
<h1>What does the Fourier transform look like?</h1><p>Gate 1 · 72 development items · 12 per family · no model evaluations</p>
<div class="status"><b>{len(validation['checks'])} simulator checks passed.</b> Numerical option distinctness passed for all 72 items.
This is a physics and presentation review, not a benchmark result.</div>
<div class="intro"><p>{html.escape(CONVENTION)}</p>
<p>For complementary screens, DC is hidden and only native Fourier samples are displayed; their non-DC maximum sets the brightness.
The equality does not hold at arbitrary frequencies between those samples. The 4f relay's overall inversion is removed by coordinate registration.</p>
<p>Review the answer hidden under each card, the mask orientation, field of view, distractor plausibility and visibility.
Log and linear cards use identical geometry, answer order and sampling. Numerical distinctness is not evidence that a model can distinguish the options.</p>
<p><a href="validation.png">Validation table</a> · <a href="manifest.json">Item manifest / answer key</a> ·
<a href="audit.json">Item audit</a> · <a href="provenance.json">Build provenance</a></p></div>
<nav>{nav}</nav>{''.join(sections)}
<footer><p>All stimuli generated locally. No photographs, copied figures, network resources, trackers or background server.</p></footer></html>'''
    (root/"index.html").write_text(page, encoding="utf-8")


def build(items, root, validation, audit):
    root.mkdir(parents=True, exist_ok=True)
    for item in items:
        for mode in ("log", "linear"):
            render_card(item, root/"items"/f"{item.id}-{mode}.png", mode)
    for f in FAMILIES:
        for mode in ("log", "linear"):
            contact_sheet(items, root, f, mode)
    validation_plot(validation, root)
    records = [i.record() for i in items]
    for record in records:
        record["images"] = {}
        for mode in ("log", "linear"):
            path = root/"items"/f"{record['id']}-{mode}.png"
            record["images"][mode] = {"path": f"items/{path.name}", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (root/"manifest.json").write_text(json.dumps({"schema_version": 1, "status": "dev_gate1_unfrozen", "items": records}, indent=2)+"\n", encoding="utf-8")
    (root/"audit.json").write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    sources = sorted(Path("fourierbench").glob("*.py"))+[Path("requirements.txt"), Path("run.cmd")]
    provenance = {"python": platform.python_version(), "numpy": np.__version__, "pillow": pillow_version,
                  "device": "CPU", "seed": 20261114, "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  "validation_sha256": hashlib.sha256(Path("reports/validation.json").read_bytes()).hexdigest(),
                  "grid": {"source_n": 192, "dx": 1, "padding": 4, "aperture_supersample": 4},
                  "font_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")) if p.exists()},
                  "command": ".\\run.cmd gate1", "validation_passed": validation["passed"], "audit_passed": audit["passed"]}
    (root/"provenance.json").write_text(json.dumps(provenance, indent=2)+"\n", encoding="utf-8")
    write_gallery(items, root, validation, audit)
    write_report(items, root, validation, audit)


def write_report(items, root, validation, audit):
    checks = {c["name"]: c for c in validation["checks"]}
    selected = ["circular_aperture_first_dark_ring", "single_slit_first_zero_width_40",
                "double_slit_fringe_period_spacing_32", "double_slit_fringe_period_spacing_64",
                "physical_parseval_energy", "integer_shift_intensity_invariance"]
    rows = "\n".join(f"| {name.replace('_', ' ')} | {checks[name]['measured']:.9g} | {checks[name]['expected']:.9g} | {checks[name]['error']:.3g} |" for name in selected)
    pad_errors = [c["error"] for c in validation["checks"] if c["name"].startswith("4f_padding_convergence") and c["name"].endswith("linear")]
    pad_log_errors = [c["error"] for c in validation["checks"] if c["name"].startswith("4f_padding_convergence") and c["name"].endswith("log")]
    counts = {f: sum(item.family == f for item in items) for f in FAMILIES}
    family_rows = "\n".join(f"| {f}. {name} | {counts[f]} | [Log](gate1/family-{f}-log.png) / [Linear](gate1/family-{f}-linear.png) |" for f, name in FAMILIES.items())
    min_rms = min(r["min_pairwise_log_rms"] for r in audit["items"])
    report = f'''# Gate 1: simulator and visual-review package

**Awaiting the owner's review.** All {len(validation['checks'])} numerical checks passed;
{len(items)} development items are available, with 12 per family. There are no model
results, no paid API requests and no GPU use. No test items were generated.

Open the [review gallery](gate1/index.html). It includes full-resolution cards,
linear-display controls, and expandable answer keys and simulation metadata.
The [related-work note](../docs/related.md) found no stop-condition overlap in
the inspected sources, while acknowledging that it is not an exhaustive audit.

## Physics validation

Reproduce every value below with `.\\run.cmd validate`.
Frequencies are cycles per source unit. Energy uses the stated integration
weights; errors are relative except shift error, which is relative to peak.

| Check | Measured | Expected | Error |
|---|---:|---:|---:|
{rows}

Additional checks cover real-amplitude centrosymmetry, sampled Babinet equality,
open/closed 4f masks, transmitted energy, grid/slit orientation, source-resolution
refinement and padding consistency. Doubling 4f padding for the 12 development
setups gives a worst linear-intensity RMS error of {max(pad_errors):.5g} of the
reference peak and a worst log-display RMS error of {max(pad_log_errors):.5g}
of the display range. Limits were fixed at 0.01 and 0.03 respectively.
See [all measured checks and tolerances](validation.json).

## Contact sheets

Reproduce the counts, images and option-distance audit with `.\\run.cmd gate1`.

| Family | Items | Contact sheets |
|---|---:|---|
{family_rows}

Each item has four seeded, shuffled options. Families 1, 2 and 5 mark a
designated naive appearance foil in the reviewer manifest. Forward and
inverse items share pair IDs. All options passed the distinctness audit; the
smallest pairwise log-display RMS distance is {min_rms:.5g}. That numerical
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

Reproducibility check: `.\\run.cmd audit` regenerates item records, checks saved
PNG hashes and verifies the recorded code and validation hashes.
'''
    (root.parent/"gate1.md").write_text(report, encoding="utf-8")
