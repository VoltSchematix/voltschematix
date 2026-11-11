"""Vervalste projectbestanden (11-11-2026).
Elk tekstveld van een projectbestand krijgt schadelijke inhoud (HTML, script, externe adressen). Het bestand wordt geopend
zoals een gebruiker dat doet en alle tabbladen worden doorlopen. Gecontroleerd:
 (1) er wordt niets uitgevoerd, (2) er komt geen vreemd element in de pagina, (3) er gaat geen enkele aanvraag naar buiten,
 (4) de beveiliging van de browser (CSP) moet nergens ingrijpen, (5) de tekst staat wel degelijk letterlijk op het scherm
     (anders test dit niets).
Gebruik: python3 hostile.py PAGINA.html FIXTURES/   (VS_BROWSER = chromium | firefox | webkit)"""
import sys, os, json, copy, tempfile, pathlib
from playwright.sync_api import sync_playwright
PAGE, FIX = sys.argv[1], sys.argv[2]
URL = pathlib.Path(PAGE).resolve().as_uri()
FILES = ['lindenlaan.vsx', 'v108-nieuw.json']
PAY = ['<img src=x onerror="window.__xss=(window.__xss||0)+1">',
       '"><svg onload="window.__xss=(window.__xss||0)+1"></svg>',
       '</text></svg><script>window.__xss=1</script>',
       "'onmouseover='window.__xss=1' x='",
       '<a href="https://evil.example/x">k</a><img src="https://evil.example/p.png">',
       '&lt;img src=x onerror=window.__xss=1&gt;<iframe src="https://evil.example/"></iframe>',
       '${window.__xss=1}`+window.__xss++ +`{{7*7}}',
       '</script><script>window.__xss=1</script>']
def inj(o, p, mode):
    if isinstance(o, dict): return {(k + p if mode == 'keys' else k): inj(v, p, mode) for k, v in o.items()}
    if isinstance(o, list): return [inj(v, p, mode) for v in o]
    if isinstance(o, str) and mode != 'keys':
        return o if o.startswith('data:') else (p if mode == 'replace' else o + p)
    return o
SCAN = """()=>{const q=s=>document.querySelectorAll(s).length;
 const on=[...document.querySelectorAll('*')].filter(e=>[...e.attributes].some(a=>/^on/i.test(a.name)&&/__xss/.test(a.value))).length;
 const ext=[...document.querySelectorAll('[href],[src]')].filter(e=>/evil\\.example/.test((e.getAttribute('href')||'')+(e.getAttribute('src')||'').replace(/^data:.*/,''))).length;
 return {xss:window.__xss||0,onattr:on,imgx:q('img[src="x"]'),ext:ext,iframe:q('iframe'),
  script:[...document.scripts].filter(s=>/__xss/.test(s.textContent)&&s.textContent.length<300).length}}"""
SEEN = """()=>{const R=/__xss|evil\\.example/;return R.test(document.body.innerText)||[...document.querySelectorAll('input,textarea')].some(i=>R.test(i.value))||[...document.querySelectorAll('svg text,svg tspan')].some(e=>R.test(e.textContent))}"""
tmp = tempfile.mkdtemp(prefix='hostile-'); runs = 0; bad = []; shown = 0; refused = 0
with sync_playwright() as p:
    br = getattr(p, os.environ.get('VS_BROWSER', 'chromium')).launch()
    for f in FILES:
        base = json.load(open(os.path.join(FIX, f), encoding='utf-8'))
        for pi, pay in enumerate(PAY):
            for mode in ('append', 'replace', 'keys'):
                if mode == 'keys' and pi > 1: continue
                path = os.path.join(tmp, f'{pi}-{mode}-{f}')
                json.dump(inj(copy.deepcopy(base), pay, mode), open(path, 'w', encoding='utf-8'))
                c = br.new_context(viewport={'width': 1500, 'height': 1000})
                c.add_init_script("window.showSaveFilePicker=undefined;window.showOpenFilePicker=undefined;window.showDirectoryPicker=undefined;try{localStorage.setItem('aep_brw','1')}catch(e){};window.__v=[];document.addEventListener('securitypolicyviolation',e=>window.__v.push(e.violatedDirective+'|'+(e.blockedURI||'')))")
                pg = c.new_page(); reqs = []
                pg.on('request', lambda r: reqs.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:', 'about:')) else None)
                pg.goto(URL); pg.wait_for_timeout(900)
                if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
                v0 = len(pg.evaluate("window.__v"))
                pg.click('#t-proj'); pg.click('#pj_open'); pg.wait_for_timeout(250)
                pg.set_input_files('#pj_upl', path); pg.wait_for_timeout(1100)
                if pg.locator('#pj_yes').count() and pg.locator('#pj_yes').is_visible(): pg.click('#pj_yes'); pg.wait_for_timeout(700)
                blocked = pg.evaluate("!document.getElementById('pj_dlg').hidden")
                if blocked: refused += 1; pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
                seen = False
                for t in ('proj', 'eend', 'sit', 'exp', 'help', 'proj'):
                    try:
                        pg.click('#t-' + t, timeout=3000); pg.wait_for_timeout(1500 if t == 'exp' else 350)
                        if t == 'eend':
                            for s in pg.locator('#sv [data-k],#sv [data-p],#sv [data-i]').all()[:6]:
                                try: s.click(timeout=800, force=True); pg.wait_for_timeout(100)
                                except Exception: pass
                        if t == 'sit':
                            bx = pg.locator('#p-sit svg').first.bounding_box()
                            if bx:
                                for i in range(6): pg.mouse.click(bx['x'] + bx['width'] * (.2 + .1 * i), bx['y'] + bx['height'] * .5); pg.wait_for_timeout(80)
                        seen = seen or pg.evaluate(SEEN)
                    except Exception: pass
                r = pg.evaluate(SCAN); v = pg.evaluate("window.__v")[v0:]
                runs += 1; shown += 1 if seen else 0
                if any(r.values()) or reqs or v: bad.append((f, pi, mode, r, reqs[:3], v[:3])); print('PROBLEEM', bad[-1], flush=True)
                if mode != 'keys' and not blocked and not seen: bad.append((f, pi, mode, 'tekst niet op het scherm: test ongeldig')); print('PROBLEEM', bad[-1], flush=True)
                c.close()
    br.close()
print(f'{os.environ.get("VS_BROWSER","chromium")}: {runs} vervalste bestanden, {shown} met de tekst zichtbaar op het scherm, {refused} geweigerd, {len(bad)} problemen')
sys.exit(1 if bad or not runs else 0)
