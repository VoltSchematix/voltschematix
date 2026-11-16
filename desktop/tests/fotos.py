"""Achtergrondfoto's op het situatieplan: bewaren van het lopende werk en maten met een komma (1.0.10).

- Veel foto's: het lopende werk (ook wat je daarna tekent) blijft bewaard bij herladen en bij "Niet-opgeslagen werk".
  Vroeger liep de kleine opslag van de browser vol en ging alles daarna stil verloren.
- De werkkopie houdt enkel een verwijzing naar de foto bij; in het geheugen en in een opgeslagen bestand zit de foto zelf.
- Kan de grote opslag niet gebruikt worden en raakt de kleine vol, dan staat er een blijvende waarschuwing.
- "Werkelijke afstand", breedte, hoogte en hoek aanvaarden komma en punt; een onwaarschijnlijke maat wordt geweigerd.

Gebruik: python3 fotos.py PAGINA.html   (VS_BROWSER = chromium | firefox | webkit)"""
import sys, os, json, struct, random, pathlib
from playwright.sync_api import sync_playwright
PAGE = pathlib.Path(sys.argv[1]).resolve().as_uri()
BR = os.environ.get('VS_BROWSER', 'chromium')
ok = 0; bad = []
def chk(n, c, info=''):
    global ok
    if c: ok += 1
    else: bad.append(n); print('  FOUT', n, str(info)[:300], flush=True)
def bmp(w, h, seed):
    """een ruisfoto (zoals een gsm-foto of scan: comprimeert slecht) met een zwart kader, als BMP"""
    rnd = random.Random(seed); row = (w * 3 + 3) // 4 * 4; px = bytearray(rnd.randbytes(row * h))
    for y in range(h):
        for x in (list(range(w)) if y in (0, 1, h - 2, h - 1) else [0, 1, w - 2, w - 1]):
            px[y * row + x * 3:y * row + x * 3 + 3] = b'\x00\x00\x00'
    return b'BM' + struct.pack('<IHHIIIIHHIIIIII', 54 + len(px), 0, 0, 54, 40, w, h, 1, 24, 0, len(px), 2835, 2835, 0, 0) + bytes(px)
FOTO = [bmp(1600, 1200, i) for i in range(3)]
def start(p, init=''):
    b = getattr(p, BR).launch(); c = b.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=True)
    if init: c.add_init_script(init)
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto(PAGE); pg.evaluate("localStorage.setItem('aep_brw','1');localStorage.setItem('aep_settings',JSON.stringify({upd:false}))")
    pg.goto('about:blank'); pg.goto(PAGE); pg.wait_for_timeout(900); esc(pg); pg.click('#t-sit'); pg.wait_for_timeout(400)
    return b, c, pg, errs
def esc(pg):
    if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
def add(pg, i):
    n = imgs(pg); pg.set_input_files('#sp_file', {'name': f'foto{i}.bmp', 'mimeType': 'image/bmp', 'buffer': FOTO[i % 3]})
    for _ in range(100):
        pg.wait_for_timeout(150)
        if imgs(pg) > n: break
    pg.keyboard.press('Escape')
types = lambda pg: pg.evaluate("window.AEP_plan.get().pages[0].els.map(e=>e.type)")
imgs = lambda pg: types(pg).count('img')
srcs = lambda pg: pg.evaluate("window.AEP_plan.get().pages[0].els.filter(e=>e.type==='img').map(e=>String(e.src).slice(0,22)+'|'+String(e.src).length)")
store = lambda pg: pg.evaluate("(()=>{const a=localStorage.getItem('aep_plan')||'';return {len:a.length,img:(a.match(/\"type\":\"img\"/g)||[]).length,muur:(a.match(/\"type\":\"muur\"/g)||[]).length,ref:(a.match(/aep-blob:/g)||[]).length,data:(a.match(/data:image/g)||[]).length}})()")
def toScr(pg, x, y): return pg.evaluate("([x,y])=>{const sv=document.querySelector('#sp_cv svg');const pt=sv.createSVGPoint();pt.x=x;pt.y=y;const q=pt.matrixTransform(sv.getScreenCTM());return [q.x,q.y]}", [x, y])
def muur(pg, y):
    pg.click('#sp_tabs [data-c="plan"]'); pg.click('#sp_list [data-t="muur"]'); a = toScr(pg, 1000, y); b = toScr(pg, 6000, y)
    pg.mouse.click(*a); pg.mouse.click(*b); pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
with sync_playwright() as p:
    # ---------- 1. veel foto's + daarna tekenen ----------
    b, c, pg, errs = start(p)
    for i in range(11): add(pg, i)
    for k in range(3): muur(pg, 2000 + k * 1500)
    pg.wait_for_timeout(1200); S = store(pg); T = types(pg)
    chk('11 foto\'s en 3 muren op het plan', T.count('img') == 11 and T.count('muur') == 3, T)
    chk('werkkopie heeft alles (11 foto\'s, 3 muren)', S['img'] == 11 and S['muur'] == 3, S)
    chk('werkkopie houdt enkel verwijzingen bij (klein)', S['ref'] == 11 and S['data'] == 0 and S['len'] < 60000, S)
    chk('geen waarschuwing "opslag vol"', pg.evaluate("document.getElementById('stf').hidden"))
    chk('in het geheugen zit de foto zelf', all(s.startswith('data:image/jpeg;base64') and int(s.split('|')[1]) > 100000 for s in srcs(pg)), srcs(pg)[:2])
    snap = pg.evaluate("JSON.stringify(window.AEP_project.snapshot())")
    chk('project om op te slaan bevat de foto\'s zelf, geen verwijzing', 'aep-blob:' not in snap and snap.count('data:image/jpeg') == 11, (len(snap), snap.count('aep-blob:')))
    # opslaan naar een bestand (download): inhoud nakijken
    pg.evaluate("delete window.showSaveFilePicker"); pg.click('#t-proj'); pg.wait_for_timeout(200)
    try:
        with pg.expect_download(timeout=15000) as dl:
            pg.click('#pj_saveas'); pg.wait_for_timeout(400)
            if pg.locator('#pj_n').count(): pg.fill('#pj_n', 'Fototest'); pg.click('#pj_ok')
        txt = pathlib.Path(dl.value.path()).read_text(encoding='utf-8')
        chk('opgeslagen bestand bevat de foto\'s zelf', 'aep-blob:' not in txt and txt.count('data:image/jpeg') == 11, (len(txt), txt.count('aep-blob:')))
    except Exception as e: chk('opslaan als bestand', False, e)
    pg.wait_for_timeout(600); esc(pg); pg.click('#t-sit'); pg.wait_for_timeout(400); muur(pg, 5600); pg.wait_for_timeout(600)   # nog iets tekenen na het opslaan
    chk('na het opslaan nog een muur getekend', types(pg).count('muur') == 4, (types(pg).count('muur'), pg.evaluate("document.getElementById('pj_dlg').hidden")))
    # herladen
    pg.reload(); pg.wait_for_timeout(1800); esc(pg); pg.click('#t-sit'); pg.wait_for_timeout(500); T = types(pg)
    chk('na herladen: 11 foto\'s en 4 muren terug', T.count('img') == 11 and T.count('muur') == 4, (T.count('img'), T.count('muur')))
    chk('na herladen: foto\'s zelf weer in het geheugen', all(s.startswith('data:image/jpeg') for s in srcs(pg)), srcs(pg)[:2])
    chk('na herladen: foto\'s getekend', pg.locator('#sp_cv svg image').count() >= 11, pg.locator('#sp_cv svg image').count())
    # ongedaan maken / opnieuw
    add(pg, 1); pg.keyboard.press('Control+z'); pg.wait_for_timeout(300); n1 = imgs(pg); pg.keyboard.press('Control+y'); pg.wait_for_timeout(300)
    chk('ongedaan maken en opnieuw met foto\'s', n1 == 11 and imgs(pg) == 12, (n1, imgs(pg)))
    pg.wait_for_timeout(600); chk('werkkopie na opnieuw: 12 verwijzingen', store(pg)['ref'] == 12 and store(pg)['data'] == 0, store(pg))
    # nieuw venster: niet-opgeslagen werk terugzetten
    pg2 = c.new_page(); pg2.goto(PAGE); pg2.wait_for_timeout(2500)
    if pg2.locator('#pj_rs').count() and pg2.locator('#pj_rs').is_visible():
        pg2.click('#pj_rs'); pg2.wait_for_timeout(2500); T = pg2.evaluate("window.AEP_plan.get().pages[0].els.map(e=>e.type)")
        chk('niet-opgeslagen werk terugzetten: 12 foto\'s en 4 muren', T.count('img') == 12 and T.count('muur') == 4, (T.count('img'), T.count('muur')))
        chk('teruggezet werk: foto\'s zelf in het geheugen', pg2.evaluate("window.AEP_plan.get().pages[0].els.filter(e=>e.type==='img').every(e=>String(e.src).startsWith('data:image/'))"))
    else: chk('niet-opgeslagen werk wordt aangeboden', False, pg2.inner_text('body')[:120])
    chk('geen scriptfouten (1)', not errs, errs[:2]); b.close()
    # ---------- 2. grote opslag niet beschikbaar: zoals vroeger, maar met een blijvende waarschuwing ----------
    b, c, pg, errs = start(p, "try{Object.defineProperty(window,'indexedDB',{get(){return {open(){throw new Error('uit')}}}})}catch(e){}")
    for i in range(11): add(pg, i)
    muur(pg, 2000); pg.wait_for_timeout(800); S = store(pg)
    chk('zonder grote opslag: foto\'s op het plan', imgs(pg) == 11, imgs(pg))
    chk('zonder grote opslag en vol: waarschuwing zichtbaar', pg.is_visible('#stf'), S)
    muur(pg, 4000); pg.wait_for_timeout(400)
    chk('waarschuwing blijft staan na verder tekenen', pg.is_visible('#stf') and len(pg.inner_text('#stf')) > 60)
    chk('knop Opslaan in de waarschuwing', pg.locator('#stf_save').is_visible())
    for i in range(12):   # foto's wissen tot het weer past
        pg.click('#sp_bgm summary'); pg.click('#sp_bgedit'); pg.wait_for_timeout(120); pg.keyboard.press('Delete'); pg.wait_for_timeout(120)
        if not imgs(pg): break
    pg.wait_for_timeout(500); chk('waarschuwing verdwijnt als het weer past', not pg.is_visible('#stf') and store(pg)['muur'] == 2, store(pg))
    chk('geen scriptfouten (2)', not errs, errs[:2]); b.close()
    # ---------- 3. maten met komma en punt ----------
    b, c, pg, errs = start(p); add(pg, 0)
    W = lambda: pg.evaluate("window.AEP_plan.get().pages[0].els.find(e=>e.type==='img')")
    def kal(val):
        pg.click('#sp_bgm summary'); pg.click('#sp_bgkal'); pg.wait_for_timeout(200); e = W()
        a = toScr(pg, e['x'] + e['w'] * 0.1, e['y'] + e['h'] * 0.5); q = toScr(pg, e['x'] + e['w'] * 0.9, e['y'] + e['h'] * 0.5)
        pg.mouse.click(*a); pg.wait_for_timeout(150); pg.mouse.click(*q); pg.wait_for_timeout(300)
        pg.click('#sp_calv'); pg.keyboard.type(val); v = pg.input_value('#sp_calv'); pg.click('#sp_props [data-a="calok"]'); pg.wait_for_timeout(250); return v
    v = kal('8,00'); chk('afstand "8,00": komma blijft staan en foto wordt 10,00 m breed', v == '8,00' and abs(W()['w'] - 10000) < 30, (v, W()['w']))
    v = kal('4.00'); chk('afstand "4.00" (punt): 5,00 m breed', abs(W()['w'] - 5000) < 20, (v, W()['w']))
    v = kal('800'); chk('afstand "800" geweigerd met uitleg, foto blijft 5,00 m', abs(W()['w'] - 5000) < 20 and 'Kijk de afstand na' in pg.inner_text('#sp_msg'), (W()['w'], pg.inner_text('#sp_msg')))
    pg.fill('#sp_calv', 'abc'); pg.click('#sp_props [data-a="calok"]'); pg.wait_for_timeout(150); chk('afstand "abc" geweigerd', abs(W()['w'] - 5000) < 20)
    pg.click('#sp_props [data-a="calno"]'); pg.click('#sp_bgm summary'); pg.click('#sp_bgedit'); pg.wait_for_timeout(250)
    f = pg.locator('#sp_props [data-e="wm"]'); chk('breedte toont een komma', f.input_value() in ('4,99', '5,00', '5,01'), f.input_value())
    f.fill('12,5'); pg.keyboard.press('Tab'); pg.wait_for_timeout(250); chk('breedte "12,5" -> 12,50 m', abs(W()['w'] - 12500) < 2, W()['w'])
    f = pg.locator('#sp_props [data-e="hm"]'); f.fill('6.25'); pg.keyboard.press('Tab'); pg.wait_for_timeout(250); chk('hoogte "6.25" -> 6,25 m', abs(W()['h'] - 6250) < 2, W()['h'])
    f = pg.locator('#sp_props input[type=text][data-e="irot"]'); f.fill('2,5'); pg.keyboard.press('Tab'); pg.wait_for_timeout(250); chk('hoek "2,5" -> 2,5°', abs((W().get('rot') or 0) - 2.5) < 0.01, W().get('rot'))
    f = pg.locator('#sp_props [data-e="wm"]'); f.fill('onzin'); pg.keyboard.press('Tab'); pg.wait_for_timeout(250); chk('breedte "onzin" geweigerd', abs(W()['h'] - 6250) < 2, W())
    chk('geen scriptfouten (3)', not errs, errs[:2]); b.close()
    # ---------- 4. een bestand met een verwijzing naar een foto die er niet is ----------
    b, c, pg, errs = start(p)
    pg.evaluate("""()=>{const pl=window.AEP_plan.get();pl.pages[0].els.push({type:'img',src:'aep-blob:bestaatniet',x:0,y:0,w:5000,h:3000,op:.5},{type:'muur',a:[0,0],b:[4000,0],d:100});window.AEP_plan.set(pl)}""")
    pg.wait_for_timeout(1500); T = types(pg)
    chk('onbekende verwijzing: foto weg, de rest blijft, geen fout', T.count('img') == 0 and T.count('muur') == 1 and not errs, (T, errs[:1]))
    chk('melding dat de foto niet teruggehaald kon worden', 'niet teruggehaald' in pg.inner_text('#sp_msg') or 'achtergrondfoto' in pg.inner_text('#sp_msg').lower(), pg.inner_text('#sp_msg'))
    b.close()
print(BR, 'RESULTAAT', ok, 'ok', len(bad), 'fout')
sys.exit(1 if bad else 0)
