"""Independent, deterministic research audit. Does not edit Gate 1 artifacts.

Run from the project root: run-research.cmd
Optical numerics: NumPy only. Pillow: layout and the actual raster resize rule.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import hashlib
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw, __version__ as pillow_version
from fourierbench.optics import (Grid, aperture, far_field, fft2c, ifft2c, pad,
    fourier_mask, filter_field, intensity_display, pattern_view)
from fourierbench.items import generate, FAMILIES
from fourierbench.render import font, wrapped

OUT = ROOT / 'reports' / 'math-research-2026-11-18'


def rms(a):
    return float(np.sqrt(np.mean(np.abs(a)**2)))


def relative_max(a, b):
    return float(np.max(np.abs(a-b)) / max(float(np.max(np.abs(a))), 1e-300))


def sheet(filename, title, panels, footer, columns=2):
    size, gap, left = 256, 32, 30
    rows = (len(panels)+columns-1)//columns
    width = left*2+columns*size+(columns-1)*gap
    canvas = Image.new('RGB', (width, 130+rows*320+100), '#f5f3ed')
    draw = ImageDraw.Draw(canvas)
    wrapped(draw, title, (left, 22), width-left*2, 25, bold=True)
    for i, (label, values) in enumerate(panels):
        x, y = left+(i%columns)*(size+gap), 110+(i//columns)*320
        wrapped(draw, label, (x,y), size, 17, bold=True)
        gray = np.round(np.clip(values,0,1)*255).astype('uint8')
        im = Image.fromarray(gray).resize((size,size), Image.Resampling.NEAREST)
        canvas.paste(im.convert('RGB'), (x,y+43))
    y = 110+rows*320
    end = wrapped(draw, footer, (left,y), width-left*2, 16)
    canvas.crop((0,0,width,end+25)).save(OUT/filename)


def homometry():
    positions = [[0,1,4,10,12,17], [0,1,8,11,13,17]]
    differences = [Counter(b-a for a,b in combinations(s,2)) for s in positions]
    assert differences[0] == differences[1]
    assert sorted(17-x for x in positions[0]) != positions[1]
    grid = Grid()
    arrays = [aperture(grid, {'kind':'array',
        'centres':[[8*(x-8.5),0] for x in s],
        'element':{'kind':'rectangle','width':3,'height':60}}) for s in positions]
    intensities = [far_field(a, grid) for a in arrays]
    err = relative_max(*intensities)
    assert err < 1e-12
    displays = [pattern_view(i,grid) for i in intensities]
    x,_ = grid.xy()
    ramp = 0.6+0.4*x/(grid.n/2)
    coded = [pattern_view(far_field(a*ramp,grid),grid) for a in arrays]
    coded_distance = rms(coded[0]-coded[1])
    assert coded_distance > 0.01
    sheet('homometry.png', 'Different six-slit apertures; identical diffraction',
          [('A: 0, 1, 4, 10, 12, 17', arrays[0]),
           ('B: 0, 1, 8, 11, 13, 17', arrays[1]),
           ('Far field of A (log)', displays[0]),
           ('Far field of B (log)', displays[1])],
          'Positions are multiplied by 8 and centred. Slits: width 3, height 60. '
          'Same source scale and same Fourier scale; the full intensities agree, not only these crops.')
    return {'positions':positions,'positive_difference_multiset':sorted(differences[0].elements()),
            'translation_or_reflection_equivalent':False,
            'max_intensity_error_over_peak':err,
            'log_display_rms':rms(displays[0]-displays[1]),
            'known_amplitude_ramp_coded_log_rms':coded_distance,
            'coded_mask':'0.6 + 0.4*x/96 at fixed laboratory coordinates; breaks this example only, not a universal guarantee.',
            'quantized_displays_identical':bool(np.array_equal(np.round(displays[0]*255),np.round(displays[1]*255)))}


def filtering():
    grid = Grid()
    a = aperture(grid, {'kind':'asymmetric'})
    masks = [fourier_mask(grid,'off_axis_hole',0.018,offset) for offset in (0.0625,-0.0625)]
    fields = [filter_field(a,m,grid,crop=False) for m in masks]
    conjugate_error = relative_max(fields[0],np.conj(fields[1]))
    intensity_error = relative_max(np.abs(fields[0])**2,np.abs(fields[1])**2)
    assert conjugate_error < 1e-12 and intensity_error < 1e-12

    # Binary Fourier masks are orthogonal projections on the FULL complex plane.
    mask = fourier_mask(grid,'pinhole',0.025)
    u = pad(a,grid.padding)
    v = ifft2c(fft2c(u)*mask)
    w = ifft2c(fft2c(u)*(1-mask))
    idem = relative_max(v,ifft2c(fft2c(v)*mask))
    energy = abs(float(np.sum(abs(v)**2)+np.sum(abs(w)**2)-np.sum(abs(u)**2)))/np.sum(abs(u)**2)
    assert idem < 1e-12 and energy < 1e-12
    pointwise = rms(abs(v)**2+abs(w)**2-abs(u)**2)

    # Separate EXACT periodic pedagogical example; this is not the finite-taper Gate 1 grid.
    pg = Grid(n=192,padding=1)
    x,y = pg.xy()
    ca,cb,cc,period = 0.5,0.23,0.23,16
    source = ca+cb*np.cos(2*np.pi*x/period)+cc*np.cos(2*np.pi*y/period)
    kinds = ['pinhole','vertical_slit','horizontal_slit','off_axis_hole','both_x_orders','blocked_centre']
    expected = [np.full_like(x,ca**2), (ca+cc*np.cos(2*np.pi*y/period))**2,
        (ca+cb*np.cos(2*np.pi*x/period))**2,np.full_like(x,cb**2/4),
        cb**2*np.cos(2*np.pi*x/period)**2,
        (cb*np.cos(2*np.pi*x/period)+cc*np.cos(2*np.pi*y/period))**2]
    outputs, errors = [], {}
    for k, target in zip(kinds,expected):
        if k == 'both_x_orders':
            m = fourier_mask(pg,'off_axis_hole',0.01,1/period)+fourier_mask(pg,'off_axis_hole',0.01,-1/period)
        else:
            m = fourier_mask(pg,k,0.01,1/period)
        result = abs(filter_field(source,m,pg))**2
        errors[k] = float(np.max(abs(result-target)))
        assert errors[k] < 1e-12
        outputs.append(result)
    labels=['DC only: constant','Vertical mask: horizontal bars',
            'Horizontal mask: vertical bars','One x order: constant',
            'Two x orders: doubled frequency','DC blocked: interference']
    sheet('coherent-filtering.png','What a Fourier mask does to a periodic grid',
          list(zip(labels,[intensity_display(i) for i in outputs])),
          'Exact periodic input: 0.5 + 0.23 cos(2 pi x/16) + 0.23 cos(2 pi y/16). '
          'Each output uses its own peak and the benchmark log mapping. '
          'The two constant panels have different physical throughput.',columns=3)
    return {'opposite_off_axis_masks':{'conjugate_field_relative_max_error':conjugate_error,
              'intensity_relative_max_error':intensity_error},
            'binary_mask_projection':{'idempotence_relative_error':idem,'complementary_energy_relative_error':float(energy),
              'pointwise_intensity_addition_rms_error':pointwise},
            'periodic_grid_formula_max_errors':errors,
            'dc_vs_one_order_own_peak_normalized_rms':rms(intensity_display(outputs[0])-intensity_display(outputs[3])),
            'dc_to_one_order_physical_intensity_ratio':ca**2/(cb**2/4)}


def babinet():
    g=Grid()
    a=aperture(g,{'kind':'circle','radius':25})
    fa=fft2c(pad(a,g.padding))*g.m
    fw=fft2c(pad(np.ones_like(a),g.padding))*g.m
    ia,ic=abs(fa)**2,abs(fw-fa)**2
    residual=ic-ia
    identity=abs(fw)**2-2*np.real(fw*np.conj(fa))
    assert relative_max(residual,identity)<1e-12
    native=np.zeros_like(ia,dtype=bool)
    native[::g.padding,::g.padding]=True
    centre=g.m//2
    native[centre,centre]=False
    nondc=np.ones_like(native)
    nondc[centre,centre]=False
    peak=float(ia.max())
    return {'shape':'circle radius 25; finite 192 by 192 illumination',
       'identity_relative_max_error':relative_max(residual,identity),
       'non_dc_native_max_difference_over_original_peak':float(abs(residual[native]).max()/peak),
       'all_padded_non_dc_max_difference_over_original_peak':float(abs(residual[nondc]).max()/peak),
       'normalization':'Both differences use the same ORIGINAL physical peak; no separate normalization.'}


def raster(panel,mode,size):
    gray=np.round(getattr(panel,mode)*255).astype('uint8')
    actual=np.asarray(Image.fromarray(gray).resize((240,240),Image.Resampling.NEAREST),dtype=float)
    step=240//size
    return np.round(actual.reshape(size,step,size,step).mean(axis=(1,3)))/255


def item_diagnostics():
    items=list(generate())
    nearest=[]
    eliminated=[]
    rows=[]
    for item in items:
        reference=next((p for p in item.inputs if p.label=='Original pattern'),None)
        if reference is not None:
            # Does not consult the question, answer, concept, or provenance to SELECT.
            distances=[rms(reference.log-p.log) for p in item.options]
            chosen=int(np.argmin(distances))
            nearest.append({'id':item.id,'family':item.family,'chosen':'ABCD'[chosen],
                'correct':bool(chosen==item.correct),'min_rms':min(distances),
                'concept':item.metadata.get('operation',item.metadata.get('concept'))})
        if item.family==1:
            foil=item.options[item.foil].linear
            cy,cx=np.array(foil.shape)//2
            if foil[cy,cx] < foil.max()-1e-12:
                eliminated.append(item.id)
        for mode in ('log','linear'):
            for size in (240,120,60,30):
                options=[raster(p,mode,size) for p in item.options]
                distances=[rms(a-b) for a,b in combinations(options,2)]
                rows.append({'id':item.id,'family':item.family,'mode':mode,'side_pixels':size,
                    'min_pairwise_rms':min(distances), 'exact_collision':min(distances)==0})
    aggregates=[]
    for mode in ('log','linear'):
        for size in (240,120,60,30):
            for family in FAMILIES:
                subset=[r for r in rows if r['mode']==mode and r['side_pixels']==size and r['family']==family]
                worst=min(subset,key=lambda r:r['min_pairwise_rms'])
                aggregates.append({'mode':mode,'side_pixels':size,'family':family,
                    'minimum_rms':worst['min_pairwise_rms'],'worst_item':worst['id'],
                    'items_below_diagnostic_0_02':sum(r['min_pairwise_rms']<0.02 for r in subset),
                    'exact_collisions':sum(r['exact_collision'] for r in subset)})
    return {'registered_reference_nearest_option':{'correct':sum(r['correct'] for r in nearest),
        'applicable':len(nearest),'records':nearest,
        'limitation':'Panel boundaries and registration are supplied; this is NOT a blind screenshot or VLM baseline.'},
        'family1_foils_violating_dc_maximum':eliminated,
        'raster_margin_summary':aggregates,'raster_margin_items':rows,
        'margin_caveat':'0.02 is descriptive, not a human or model perception threshold. '
          '240px reproduces option quantization and nearest resize; smaller sizes use area averaging followed by 8-bit requantization.'}


def scalars():
    z=1.959963984540054
    return {'linear_8bit_dark_threshold':1/(2*255),
       'log_8bit_dark_threshold':float((1000**(1/(2*255))-1)/999),
       'log_derivative_at_zero':float(999/np.log(1000)),
       'log_derivative_at_one':float(999/(1000*np.log(1000))),
       'wilson_95_half_width_at_observed_50pct':{str(n):float(z/(2*np.sqrt(n+z*z))) for n in (10,80,100)},
       'note':'Thresholds are the transition from code 0 to 1 under nearest rounding, before any resize. Wilson widths are descriptive, not a power analysis.'}


def central_curvature():
    g=Grid()
    a=aperture(g,{'kind':'slit','width':16,'height':72,'angle':25})
    xy=np.stack(g.xy()).reshape(2,-1)
    weights=a.ravel()/a.sum()
    mu=xy@weights
    centered=xy-mu[:,None]
    covariance=(centered*weights)@centered.T
    hessian=-8*np.pi**2*covariance
    def normalized_intensity(qx,qy):
        return float(abs(np.sum(weights*np.exp(-2j*np.pi*(qx*xy[0]+qy*xy[1]))))**2)
    errors=[]
    for step in (0.001,0.0005,0.00025,0.000125):
        xx=(normalized_intensity(step,0)-2+normalized_intensity(-step,0))/step**2
        yy=(normalized_intensity(0,step)-2+normalized_intensity(0,-step))/step**2
        cross=(normalized_intensity(step,step)-normalized_intensity(step,-step)
            -normalized_intensity(-step,step)+normalized_intensity(-step,-step))/(4*step**2)
        estimated=np.array([[xx,cross],[cross,yy]])
        errors.append({'frequency_step':step,'relative_frobenius_error':float(np.linalg.norm(estimated-hessian)/np.linalg.norm(hessian))})
    assert errors[-1]['relative_frobenius_error']<0.001
    assert all(errors[i+1]['relative_frobenius_error']<errors[i]['relative_frobenius_error'] for i in range(len(errors)-1))
    return {'aperture':'16 by 72 slit rotated 25 degrees; same cell averaged raster as simulator',
            'amplitude_weighted_covariance':covariance.tolist(),'predicted_intensity_hessian':hessian.tolist(),
            'direct_dtft_finite_difference_errors':errors,
            'scope':'Identity for the discrete raster measure. This checks an independent direct sum, not another FFT.'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'date':'2026-11-18','purpose':'Research alongside pending Gate 1; no model evaluation.',
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'pillow':pillow_version},
        'homometry':homometry(),'filtering':filtering(),'babinet':babinet(),
        'item_diagnostics':item_diagnostics(),'scalars':scalars(),'central_curvature':central_curvature()}
    sources=[Path(__file__),ROOT/'research'/'build_report.py',ROOT/'research'/'report.md.in',
        ROOT/'run-research.cmd',ROOT/'requirements.txt',ROOT/'fourierbench'/'optics.py',
        ROOT/'fourierbench'/'items.py',ROOT/'fourierbench'/'render.py']
    result['source_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    small={k:v for k,v in result.items() if k not in ('item_diagnostics','source_sha256')}
    diag=result['item_diagnostics']
    small['shortcut_correct_applicable']=[diag['registered_reference_nearest_option']['correct'],diag['registered_reference_nearest_option']['applicable']]
    small['dc_max_foil_eliminations']=diag['family1_foils_violating_dc_maximum']
    small['raster_summary']=diag['raster_margin_summary']
    print(json.dumps(small,indent=2))


if __name__=='__main__':
    main()
