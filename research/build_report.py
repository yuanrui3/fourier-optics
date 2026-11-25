"""Fill the research report from audit results; render its supported Markdown offline."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import json
import os
import re
from urllib.parse import urlparse, unquote
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'/'math-research-2026-11-18'
DOC=ROOT/'docs'/'math-research-2026-11-18.md'


def report_values(data):
    h,f,b,s=data['homometry'],data['filtering'],data['babinet'],data['scalars']
    margins=data['item_diagnostics']['raster_margin_summary']
    c=data['central_curvature']['direct_dtft_finite_difference_errors']
    def minimum(mode,size,family=None):
        return min(r['minimum_rms'] for r in margins if r['mode']==mode and r['side_pixels']==size
                   and (family is None or family==r['family']))
    table=['| Family | Log 240 px | Log 30 px | Linear 240 px | Linear 30 px |',
           '| --- | --- | --- | --- | --- |']
    names=['Forward','Inverse (source options)','Transformations','Slits/gratings','4f filtering','Symmetry/complements']
    for family,name in enumerate(names,1):
        values=[minimum(mode,size,family) for mode,size in [('log',240),('log',30),('linear',240),('linear',30)]]
        table.append('| '+name+' | '+' | '.join(f'{v:.5f}' for v in values)+' |')
    return {'homometry_error':f"{h['max_intensity_error_over_peak']:.2e}",
        'mask_error':f"{f['opposite_off_axis_masks']['intensity_relative_max_error']:.2e}",
        'throughput_ratio':f"{f['dc_to_one_order_physical_intensity_ratio']:.2f}",
        'min_log':f"{minimum('log',240):.5f}",'min_linear':f"{minimum('linear',240):.5f}",
        'coded_rms':f"{h['known_amplitude_ramp_coded_log_rms']:.5f}",
        'curvature_errors':', '.join(f"{r['relative_frobenius_error']:.6f}" for r in c),
        'curvature_final':f"{c[-1]['relative_frobenius_error']:.3e}",
        'grid_formula_error':'1.0e-15',
        'projection_pointwise':f"{f['binary_mask_projection']['pointwise_intensity_addition_rms_error']:.5f}",
        'babinet_native':f"{b['non_dc_native_max_difference_over_original_peak']:g}",
        'babinet_padded':f"{b['all_padded_non_dc_max_difference_over_original_peak']:.2f}",
        'linear_floor':f"{s['linear_8bit_dark_threshold']:.3e}",
        'log_floor':f"{s['log_8bit_dark_threshold']:.3e}",
        'margin_table':'\n'.join(table),
        **{f'wilson{n}':f"{100*s['wilson_95_half_width_at_observed_50pct'][str(n)]:.1f}" for n in (10,80,100)}}


def link_url(url):
    if urlparse(url).scheme or url.startswith('#'):
        return escape(url,quote=True)
    path=(DOC.parent/url).resolve()
    assert path.is_relative_to(ROOT) and path.exists(), f'Missing local target: {url}'
    return escape(os.path.relpath(path,OUT).replace('\\','/'),quote=True)


def inline(text):
    tokens=[]
    def save(html):
        tokens.append(html)
        return f'\x00{len(tokens)-1}\x00'
    text=re.sub(r'`([^`]+)`',lambda m:save('<code>'+escape(m[1])+'</code>'),text)
    text=re.sub(r'\[([^\]]+)\]\(((?:https?://|\.\.?/)[^)]+)\)',lambda m:save(
        '<a href="'+link_url(m[2])+'">'+escape(m[1])+'</a>'),text)
    text=escape(text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    for i,token in enumerate(tokens):
        text=text.replace(f'\x00{i}\x00',token)
    return text


def render(markdown):
    lines=markdown.splitlines()
    blocks=[]
    headings=[]
    i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():
            i+=1
            continue
        if line.startswith('```'):
            content=[]
            i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                content.append(lines[i]); i+=1
            assert i<len(lines),'Unclosed code block'
            blocks.append('<pre><code>'+escape('\n'.join(content))+'</code></pre>')
            i+=1; continue
        match=re.match(r'^(#{1,3}) (.+)',line)
        if match:
            level=len(match[1]); title=match[2]
            anchor=f'section-{len(headings)}' if level==2 else 'report-title'
            if level==2:
                headings.append((anchor,title))
            blocks.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
            i+=1; continue
        match=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',line)
        if match:
            blocks.append('<figure><img src="'+link_url(match[2])+'" alt="'+escape(match[1],quote=True)+'">'
                          '<figcaption>'+escape(match[1])+'</figcaption></figure>')
            i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',cell) for cell in cells):
                    rows.append(cells)
                i+=1
            table='<div class="table"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'
            for row in rows[1:]:
                assert len(row)==len(rows[0]),'Unequal table columns'
                table+='<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>'
            blocks.append(table+'</tbody></table></div>'); continue
        if re.match(r'^\d+\. ',line):
            entries=[]
            while i<len(lines) and re.match(r'^\d+\. ',lines[i]):
                entries.append(re.sub(r'^\d+\. ','',lines[i])); i+=1
            blocks.append('<ol>'+''.join('<li>'+inline(c)+'</li>' for c in entries)+'</ol>'); continue
        paragraph=[line]
        i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|```|\||!\[|\d+\. )',lines[i]):
            paragraph.append(lines[i]); i+=1
        blocks.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '\n'.join(blocks),headings


class LocalAssets(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key not in ('href','src') or not value or urlparse(value).scheme or value.startswith('#'):
                continue
            path=(OUT/unquote(value)).resolve()
            assert path.is_relative_to(ROOT) and path.is_file(),f'Missing asset {path}'
            if tag=='img':
                with Image.open(path) as im:
                    im.verify()


def main():
    data=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    assert max(data['filtering']['periodic_grid_formula_max_errors'].values())<1e-15
    diagnostic=data['item_diagnostics']
    reference=diagnostic['registered_reference_nearest_option']
    assert (reference['correct'],reference['applicable'])==(10,30)
    assert diagnostic['family1_foils_violating_dc_maximum']==[f'dev-f1-{i:03}' for i in range(5,12)]
    margin=diagnostic['raster_margin_summary']
    assert all(r['exact_collisions']==0 for r in margin)
    for size,count in [(240,9),(30,14)]:
        assert sum(r['items_below_diagnostic_0_02'] for r in margin if r['mode']=='linear' and r['side_pixels']==size)==count
    assert sum(r['items_below_diagnostic_0_02'] for r in margin if r['mode']=='log')==0
    report=(ROOT/'research'/'report.md.in').read_text(encoding='utf-8')
    for key,value in report_values(data).items():
        report=report.replace('@@'+key+'@@',value)
    assert '@@' not in report,'Unresolved result placeholder'
    DOC.write_text(report,encoding='utf-8')
    body,headings=render(report)
    nav=''.join('<a href="#'+anchor+'">'+escape(title)+'</a>' for anchor,title in headings)
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fourier optics — mathematical research, 18 November 2026</title>
<style>
:root{color-scheme:light;--ink:#193239;--muted:#52666c;--accent:#0b6c72;--paper:#fffefb}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:#f4f3ee;font:17px/1.7 system-ui,sans-serif}
header{background:#153b43;color:#fff;padding:18px 5%;font-size:14px;letter-spacing:.035em}
header a{color:#ddf4f2;margin-left:24px}main{max-width:1040px;margin:28px auto 80px;padding:38px 52px;background:var(--paper);box-shadow:0 4px 30px #173d4110}
h1{font-size:38px;line-height:1.2;letter-spacing:-.025em;margin:0 0 26px}h2{font-size:25px;line-height:1.35;margin-top:48px;padding-top:14px;border-top:1px solid #d5dfdd;scroll-margin-top:20px}
p{margin:18px 0}a{color:var(--accent);text-underline-offset:3px}strong{font-weight:680}pre{padding:20px 24px;background:#eff5f3;border-left:4px solid #21767a;overflow-x:auto;font:15px/1.7 Consolas,monospace;white-space:pre}
code{font-family:Consolas,monospace}p code{background:#eef2ef;padding:2px 5px}.table{overflow-x:auto;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.55}th,td{padding:12px 14px;border-bottom:1px solid #d9e2df;text-align:left;vertical-align:top}th{background:#e7efec;font-weight:700}tbody tr:nth-child(even){background:#f8faf7}
figure{margin:30px auto;text-align:center}img{max-width:100%;height:auto;border:1px solid #d6dfda}figcaption{font-size:13px;color:var(--muted);margin:8px auto}li{padding:0 0 14px 6px}nav{margin:24px 0;padding:18px 22px;background:#edf3ef}nav a{display:block;font-size:14px;margin:5px 0}summary{cursor:pointer;font-weight:650}
footer{color:var(--muted);font-size:13px;margin:45px 0 0;padding-top:20px;border-top:1px solid #d5dfdd}
@media(max-width:700px){main{padding:26px 20px;margin:0}h1{font-size:29px}h2{font-size:22px}header{padding:14px 20px}header a{display:inline-block;margin-left:0;margin-right:18px}body{font-size:16px}pre{font-size:13px;padding:16px}}
@media print{body{background:white}header,nav{display:none}main{box-shadow:none;margin:0;padding:0;max-width:none}h2{break-after:avoid}figure,tr{break-inside:avoid}a{color:inherit}}
</style></head><body><header>FOURIER OPTICS · RESEARCH NOTE · 18 NOVEMBER 2026
<a href="../gate1/index.html">Gate 1 review gallery</a><a href="results.json">Numerical results</a></header><main>'''
    # Put the table of contents after the introductory paragraphs, before findings.
    first='<h2 id="section-0">'
    body=body.replace(first,'<nav><details><summary>Contents and derivations</summary>'+nav+'</details></nav>'+first,1)
    html+=body+'<footer>Local offline report. CPU simulations only. Gate 1 approval remains pending.</footer></main></body></html>'
    LocalAssets().feed(html)
    ids=re.findall(r'\bid="([^"]+)"',html)
    assert len(ids)==len(set(ids)),'Duplicate HTML anchor'
    assert all(anchor in ids for anchor in re.findall(r'href="#([^"]+)"',html))
    (OUT/'index.html').write_text(html,encoding='utf-8')
    print(f'Report built and local links/images checked: {OUT / "index.html"}')


if __name__=='__main__':
    main()
