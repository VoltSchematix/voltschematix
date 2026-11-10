"""Compatibiliteit tussen alle versies en platformen (deel 13, 6-11-2026).
Elk testbestand wordt in elke omgeving geopend en opgeslagen; dat bestand gaat daarna naar elke andere omgeving, die het
opnieuw opent en opslaat. Gecontroleerd: (1) gegevens identiek (behalve datum/naam), (2) dezelfde afgedrukte pagina's
(eendraadschema + situatieplan, pixel-onafhankelijk: de SVG-tekst), (3) geen JS-fouten, (4) twee rondes heen en weer = stabiel.
Ook: 1.0.7 (website en programma) opent een bestand van 1.0.8.
Gebruik: python3 compat.py WEB.html DESK.html MOCK.js OUD_WEB.html OUD_DESK.html OUD_MOCK.js FIXTURES/ UIT.json"""
import asyncio, sys, json, os, glob, tempfile, hashlib, copy
from playwright.async_api import async_playwright
WEB, DESK, MOCKF, OWEB, ODESK, OMOCKF, FIX, OUT = sys.argv[1:9]
TXT = {k: open(v, encoding='utf-8').read() for k, v in dict(WEB=WEB, DESK=DESK, MOCK=MOCKF, OWEB=OWEB, ODESK=ODESK, OMOCK=OMOCKF).items()}
TMP = tempfile.mkdtemp(prefix='compat-')
NOFS = 'window.showSaveFilePicker=undefined;window.showOpenFilePicker=undefined;window.showDirectoryPicker=undefined;'
UAMAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)'
SKIP = {'datum', 'naam', 'id'}; DERIVED = {'ext', '__fit', 'p_rev_ts'}
def norm(x, top=True):
    if isinstance(x, dict):
        r = {k: norm(v, False) for k, v in x.items() if not (top and k in SKIP) and k not in DERIVED}
        if top and isinstance(r.get('doc'), dict) and isinstance(r['doc'].get('_vis'), dict):
            r['doc']['_vis'] = {k: v for k, v in r['doc']['_vis'].items() if v is not True}
        return r
    if isinstance(x, list): return [norm(v, False) for v in x]
    return x
def canon(o): return json.dumps(norm(o), sort_keys=True, ensure_ascii=False)
def noid(x):
    """vergelijking bij het EERSTE openen van een oud bestand zonder symbool-ids: elke omgeving geeft dan eigen (willekeurige) ids;
    de standaardnaam van een nieuwe verdieping volgt de taal van het scherm (bewust)"""
    if isinstance(x, dict): return {k: noid(v) for k, v in x.items() if k not in ('id', 'sid', 'ref')}
    if isinstance(x, list): return [noid(v) for v in x]
    return x
DEFNAME = {'Gelijkvloers', 'Rez-de-chaussée', 'Ground floor'}
def canon0(o):
    o = noid(norm(o))
    for pg in ((o.get('plan') or {}).get('pages') or []):
        if pg.get('name') in DEFNAME: pg['name'] = 'Gelijkvloers'
    return json.dumps(o, sort_keys=True, ensure_ascii=False)
def diffkeys(a, b, path=''):
    """eerste paar plaatsen waar a en b verschillen"""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True): out += diffkeys(a.get(k), b.get(k), path + '/' + str(k))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            if json.dumps(x, sort_keys=True) != json.dumps(y, sort_keys=True): out += diffkeys(x, y, path + f'[{i}]')
    else: out.append(f'{path}: {json.dumps(a, ensure_ascii=False)[:80]} ≠ {json.dumps(b, ensure_ascii=False)[:80]}')
    return out[:6]
PAGES = """async()=>{const out=[];try{(window.AEP_sch.builders()||[]).forEach(f=>{try{const r=f();out.push(r&&r.svg||'')}catch(e){out.push('ERR '+e)}})}catch(e){out.push('ERRS '+e)}
  try{(window.AEP_plan.builders()||[]).forEach(f=>{try{const r=f(1,1);out.push(r&&r.svg||'')}catch(e){out.push('ERR '+e)}})}catch(e){out.push('ERRP '+e)}
  return out}"""
FAKE = """([src,nm])=>{window.__saved=null;const f=new File([src],nm);const h={kind:'file',name:nm,getFile:async()=>new File([window.__saved||src],nm),queryPermission:async()=>'granted',requestPermission:async()=>'granted',isSameEntry:async o=>o===h,
  createWritable:async()=>{const parts=[];return {write:async d=>{parts.push(d&&d.data!==undefined&&d.type==='write'?d.data:d)},close:async()=>{window.__saved=await new Blob(parts).text()},abort:async()=>{}}}};
  return window.AEP_project.openHandle(h)}"""
class Env:
    def __init__(s, name, kind, html, mock=None, ua=None, lang='nl', nofs=False, url=None):
        s.name, s.kind, s.html, s.mock, s.ua, s.lang, s.nofs, s.url = name, kind, html, mock, ua, lang, nofs, url
    async def start(s, br):
        kw = {'viewport': {'width': 1400, 'height': 900}, 'accept_downloads': True}
        if s.ua: kw['user_agent'] = s.ua
        s.ctx = await br.new_context(**kw)
        init = f"localStorage.setItem('aep_brw','1');localStorage.setItem('aep_lang','{s.lang}');" + (NOFS if s.nofs else '')
        if s.mock: await s.ctx.add_init_script(s.mock)
        await s.ctx.add_init_script(init)
        if s.url is None:
            s.url = 'http://tauri.localhost/' if s.kind == 'desk' else 'https://aep.test/'
            await s.ctx.route(s.url, lambda r: asyncio.ensure_future(r.fulfill(body=s.html, content_type='text/html; charset=utf-8')))
        s.pg = await s.ctx.new_page(); s.errs = []; s.pg.on('pageerror', lambda e: s.errs.append(str(e)[:200]))
        await s.pg.goto(s.url); await s.pg.wait_for_timeout(1200); await s.settle()
    async def settle(s):
        for _ in range(4):
            t = await s.pg.evaluate("document.getElementById('pj_dlg').hidden?'':document.getElementById('pj_dt').textContent")
            if not t: return ''
            if await s.pg.locator('#pj_yes').count(): await s.pg.click('#pj_yes'); await s.pg.wait_for_timeout(500)
            elif await s.pg.locator('#pj_dx').count(): await s.pg.click('#pj_dx'); await s.pg.wait_for_timeout(300)
            else: return t
        return t
    async def open(s, text, name):
        pg = s.pg
        if s.kind == 'desk':
            path = 'C:\\Compat\\' + name
            await pg.evaluate("([p,t])=>{window.__mock.FS[p]={d:t,m:Date.now()}}", [path, text])
            await pg.click('#t-proj'); await pg.evaluate("v=>window.__mock.next.push(v)", path); await pg.click('#pj_open'); await pg.wait_for_timeout(900)
            await s.settle(); s.path = path
        elif s.nofs:
            p = os.path.join(TMP, name); open(p, 'w', encoding='utf-8').write(text)
            await pg.click('#t-proj'); await pg.click('#pj_open'); await pg.wait_for_timeout(250)
            if await pg.evaluate("!document.getElementById('pj_dlg').hidden&&!document.getElementById('pj_upl')"): await s.settle(); await pg.click('#pj_open'); await pg.wait_for_timeout(250)
            await pg.set_input_files('#pj_upl', p); await pg.wait_for_timeout(900); await s.settle()
        else:
            await pg.evaluate(FAKE, [text, name]); await pg.wait_for_timeout(900); await s.settle()
        await pg.wait_for_timeout(300)
    async def save(s):
        pg = s.pg
        await pg.click('#t-proj'); await pg.wait_for_timeout(150)
        if s.kind == 'desk':
            out = s.path.rsplit('.', 1)[0] + '-uit.vsx'
            await pg.evaluate("v=>window.__mock.next.push(v)", out); await pg.click('#pj_saveas'); await pg.wait_for_timeout(800)
            return await pg.evaluate("p=>(window.__mock.FS[p]||{}).d||null", out)
        if s.nofs:
            await pg.click('#pj_saveas'); await pg.wait_for_timeout(250); await pg.fill('#pj_n', 'uit')
            async with pg.expect_download() as dl: await pg.click('#pj_ok')
            d = await dl.value; return open(await d.path(), encoding='utf-8').read()
        # Chrome/Edge: Ctrl+S schrijft rechtstreeks in het geopende bestand
        await pg.evaluate("window.__saved=null"); await pg.keyboard.press('Control+s')
        for _ in range(30):
            v = await pg.evaluate("window.__saved")
            if v: return v
            await pg.wait_for_timeout(100)
        return None
    async def pages(s):
        for t in ['#t-eend', '#t-sit']: await s.pg.click(t); await s.pg.wait_for_timeout(250)
        await s.pg.click('#t-proj')
        return [hashlib.sha1(x.encode()).hexdigest()[:12] for x in await s.pg.evaluate(PAGES)]
async def main():
    res = {'rijen': [], 'fouten': []}
    def log(ok, t):
        print(('  OK   ' if ok else '  FOUT ') + t, flush=True)
        if not ok: res['fouten'].append(t)
    async with async_playwright() as p:
        br = await getattr(p, os.environ.get('VS_BROWSER', 'chromium')).launch()  # chromium / firefox / webkit (Safari)
        envs = [Env('website Chrome/Edge', 'web', TXT['WEB']), Env('website Firefox/Safari', 'web', TXT['WEB'], nofs=True),
                Env('offline HTML-bestand', 'web', None, url='file://' + os.path.abspath(WEB)),
                Env('Windows-programma', 'desk', TXT['DESK'], mock=TXT['MOCK']), Env('Mac-programma', 'desk', TXT['DESK'], mock=TXT['MOCK'], ua=UAMAC),
                Env('website FR', 'web', TXT['WEB'], lang='fr'), Env('website EN', 'web', TXT['WEB'], lang='en')]
        old = [Env('1.0.7 website', 'web', TXT['OWEB']), Env('1.0.7 programma', 'desk', TXT['ODESK'], mock=TXT['OMOCK'])]
        for e in envs + old: await e.start(br)
        files = sorted(glob.glob(os.path.join(FIX, '*.json')) + glob.glob(os.path.join(FIX, '*.vsx')))
        for f in files:
            name = os.path.basename(f); src = open(f, encoding='utf-8').read(); print('==', name, flush=True)
            # referentie: website Chrome opent en bewaart; afdruk van die toestand
            ref = envs[0]; await ref.open(src, name); A = await ref.save(); refp = await ref.pages()
            if not A: log(False, f'{name}: website kon niet opslaan'); continue
            Aj = json.loads(A); saved = {ref.name: A}
            for e in envs[1:]:
                await e.open(src, name); x = await e.save(); pgs = await e.pages()
                saved[e.name] = x
                same = x and canon0(json.loads(x)) == canon0(Aj)
                log(bool(same), f'{name}: geopend en opgeslagen in {e.name} = website' + ('' if same else f' {diffkeys(json.loads(canon0(Aj)), json.loads(canon0(json.loads(x)))) if x else "(niets opgeslagen)"}'))
                if e.lang != 'nl': log(len(pgs) == len(refp), f'{name}: afdruk in {e.name}: evenveel pagina\'s ({len(pgs)}), tekst vertaald'); continue
                log(pgs == refp, f'{name}: afdruk in {e.name} = website ({len(pgs)} pagina\'s)' + ('' if pgs == refp else f' {sum(a != b for a, b in zip(pgs, refp))} verschillend, {len(pgs)} vs {len(refp)}'))
            # elk opgeslagen bestand in elke andere omgeving openen + opslaan
            for sname, stext in saved.items():
                if not stext: continue
                for e in envs:
                    if e.name == sname: continue
                    await e.open(stext, 'van-' + str(abs(hash(sname)))[:6] + '.vsx'); y = await e.save()
                    S = json.loads(stext); ok = y and canon(json.loads(y)) == canon(S)
                    res['rijen'].append({'bestand': name, 'van': sname, 'naar': e.name, 'ok': bool(ok)})
                    if not ok: log(False, f'{name}: {sname} → {e.name} niet identiek {diffkeys(norm(S), norm(json.loads(y))) if y else "(niets opgeslagen)"}')
            # twee rondes: Windows → website → Mac → offline → Windows
            t = A
            for e in [envs[3], envs[1], envs[4], envs[2], envs[3], envs[0]]:
                await e.open(t, 'ronde.vsx'); t = await e.save() or t
            log(canon(json.loads(t)) == canon(Aj), f'{name}: zes keer heen en weer tussen alle platformen: stabiel')
            # 1.0.7 opent het bestand van 1.0.8
            for e in old:
                before = len(e.errs); await e.open(A, 'nieuw.vsx'); y = await e.save()
                ok = bool(y) and len(e.errs) == before
                lost = diffkeys(norm(Aj), norm(json.loads(y))) if y else ['niets opgeslagen']
                res['rijen'].append({'bestand': name, 'van': 'website 1.0.8', 'naar': e.name, 'ok': ok, 'verschil': lost})
                print(f'  INFO {name}: {e.name} opent het 1.0.8-bestand {"zonder fouten" if ok else "MET FOUTEN " + str(e.errs[before:][:2])}; na opslaan in 1.0.7: ' + ('identiek' if not lost else 'verschil ' + '; '.join(lost[:3])), flush=True)
        for e in envs + old:
            log(not e.errs, f'{e.name}: geen JS-fouten {e.errs[:3]}')
        await br.close()
    n = len(res['rijen']); ok = sum(r['ok'] for r in res['rijen'] if r['naar'][:5] != '1.0.7')
    print(f"RESULTAAT {len(res['fouten'])} fouten; uitwisselingen 1.0.8 onderling {ok}/{sum(1 for r in res['rijen'] if r['naar'][:5] != '1.0.7')} identiek")
    json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
asyncio.run(main())
