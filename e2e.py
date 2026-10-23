"""Eindtest van het echte programma voor Windows (wordt automatisch uitgevoerd bij het bouwen op GitHub).

Het programma wordt gestart via tauri-driver (WebDriver). De testversie slaat de Windows-vensters over:
welk bestand of welke map "gekozen" wordt, komt uit een wachtrij (VS_E2E_QUEUE).
Gebruik: python e2e.py PROGRAMMA.exe FIXTURES EXPECTED WERKMAP
"""
import json, os, sys, time, shutil, urllib.request, urllib.error

PJ = os.path  # paden in de werkmap (bij de test hier: Windows-paden)

SKIP = {'datum', 'naam', 'id'}
DERIVED = {'ext', '__fit', 'p_rev_ts'}


def norm(x, top=True, ids=True):
    # ids=False: willekeurige id's die het programma zelf aanmaakt bij heel oude bestanden (zonder id's) niet vergelijken
    if isinstance(x, dict):
        r = {k: norm(v, False, ids) for k, v in x.items() if not (top and k in SKIP) and k not in DERIVED and (ids or k != 'id')}
        if top and isinstance(r.get('doc'), dict) and isinstance(r['doc'].get('_vis'), dict):
            r['doc']['_vis'] = {k: v for k, v in r['doc']['_vis'].items() if v is not True}
        return r
    if isinstance(x, list):
        return [norm(v, False, ids) for v in x]
    return x


def same(a, b, ids=True):
    return json.dumps(norm(a, ids=ids), sort_keys=True, ensure_ascii=False) == json.dumps(norm(b, ids=ids), sort_keys=True, ensure_ascii=False)


# ---------------- WebDriver (rechtstreeks, zonder extra pakketten) ----------------
class Remote:
    def __init__(self, exe, queue, port=4444):
        self.exe, self.queue_file, self.base, self.sid = exe, queue, f'http://127.0.0.1:{port}', None

    def _req(self, method, path, body=None, timeout=300):
        data = None if body is None else json.dumps(body).encode()
        r = urllib.request.Request(self.base + path, data=data, method=method, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return json.loads(resp.read().decode() or '{}')

    def start(self):
        print('  ...  wachten op tauri-driver', flush=True)
        for _ in range(30):
            try:
                print('  ...  tauri-driver status:', json.dumps(self._req('GET', '/status', timeout=10).get('value')), flush=True)
                break
            except Exception as e:
                err = e
                time.sleep(2)
        else:
            raise SystemExit(f'tauri-driver antwoordt niet: {err}')
        caps = {'capabilities': {'alwaysMatch': {'browserName': 'wry', 'tauri:options': {'application': self.exe}}}}
        for i in range(3):
            print(f'  ...  programma starten (poging {i + 1})', flush=True)
            try:
                v = self._req('POST', '/session', caps, timeout=120)['value']
                if 'sessionId' not in v:
                    raise RuntimeError(json.dumps(v)[:800])
                self.sid = v['sessionId']
                break
            except urllib.error.HTTPError as e:
                print('  ...  fout:', e.code, e.read().decode(errors='replace')[:1500], flush=True)
            except Exception as e:
                print('  ...  fout:', repr(e)[:1500], flush=True)
            time.sleep(3)
        if not self.sid:
            raise SystemExit('programma kon niet gestart worden via tauri-driver')
        print('  ...  programma gestart', flush=True)
        self._req('POST', f'/session/{self.sid}/timeouts', {'script': 180000})

    def stop(self):
        if self.sid:
            try:
                self._req('DELETE', f'/session/{self.sid}')
            except Exception:
                pass
            self.sid = None
            time.sleep(2)

    def run(self, body, *args):
        script = ('const done=arguments[arguments.length-1];'
                  '(async(...a)=>{' + body + '})(...Array.from(arguments).slice(0,-1))'
                  '.then(v=>done({ok:v===undefined?null:v}),e=>done({err:String(e&&e.stack||e)}));')
        v = self._req('POST', f'/session/{self.sid}/execute/async', {'script': script, 'args': list(args)})['value']
        if isinstance(v, dict) and 'err' in v:
            raise RuntimeError(v['err'])
        return v.get('ok') if isinstance(v, dict) else v

    def queue(self, path):
        with open(self.queue_file, 'a', encoding='utf-8') as f:
            f.write(path + '\n')


class RealFS:
    def write(self, p, text):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(text)

    def read(self, p):
        return open(p, encoding='utf-8').read() if os.path.exists(p) else None

    def size(self, p):
        return os.path.getsize(p) if os.path.exists(p) else 0


# ---------------- de test zelf ----------------
HELP = """
window.__t=window.__t||{
  sleep:ms=>new Promise(r=>setTimeout(r,ms)),
  async until(f,ms=20000){const t0=Date.now();while(Date.now()-t0<ms){try{const v=f();if(v)return v}catch(e){}await new Promise(r=>setTimeout(r,150))}return null},
  $:id=>document.getElementById(id),
  dlg:()=>document.getElementById('pj_dlg').hidden?'':document.getElementById('pj_dt').textContent,
  async settle(){for(let i=0;i<3;i++){if(!this.dlg())return;const y=this.$('pj_yes')||this.$('pj_rn');if(y)y.click();else this.$('pj_dlg').hidden=true;await this.sleep(500)}}
};
"""


def test(d, fs, fix, exp, work, check):
    W = lambda *p: PJ.join(work, *p)
    d.start()
    d.run(HELP + "await __t.until(()=>window.AEP_project&&document.readyState==='complete');await __t.sleep(1500);await __t.settle();")
    check(d.run("return document.body.classList.contains('desktop')&&!!window.__TAURI__"), 'programma gestart, aansluiting op Windows actief')
    names = sorted(f[:-5] for f in os.listdir(fix) if f.endswith('.json'))
    first_out = None
    for n in names:
        src = open(os.path.join(fix, n + '.json'), encoding='utf-8').read()
        fs.write(W('in', n + '.json'), src)
        out = W('uit', n + '.vsx')
        d.queue(W('in', n + '.json'))
        d.run(HELP + "__t.$('t-proj').click();__t.$('pj_open').click();await __t.until(()=>__t.$('pj_name').textContent===a[0]||__t.dlg());await __t.settle();", n)
        d.queue(out)
        msg = d.run(HELP + "__t.$('pj_saveas').click();return await __t.until(()=>/Opgeslagen/.test(__t.$('pj_msg').textContent)&&__t.$('pj_msg').textContent)")
        got = fs.read(out)
        expd = json.loads(open(os.path.join(exp, n + '.json'), encoding='utf-8').read())
        ids = '"id"' in src  # heel oude bestanden hebben nog geen id's: die maakt het programma zelf aan
        if got and not same(json.loads(got), expd, ids):
            a, b = norm(json.loads(got)), norm(expd)
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    if isinstance(a.get(k), dict) and isinstance(b.get(k), dict):
                        print('   verschil in', k, {kk: (str(a[k].get(kk))[:60], str(b[k].get(kk))[:60]) for kk in set(a[k]) | set(b[k]) if a[k].get(kk) != b[k].get(kk)})
                    else:
                        print('   verschil in', k)
        check(got and same(json.loads(got), expd, ids), f'{n}: openen + bewaren als .vsx = identiek aan de website ({msg})')
        # opnieuw openen en gewoon opslaan: niets mag veranderen
        d.queue(out)
        d.run(HELP + "__t.$('pj_open').click();await __t.until(()=>__t.$('pj_name').textContent===a[0]);await __t.settle();await __t.sleep(1200);"
              "__t.$('k_naam').dispatchEvent(new Event('input',{bubbles:true}));await __t.sleep(300);__t.$('pj_save').click();await __t.until(()=>/Opgeslagen/.test(__t.$('pj_msg').textContent));", n)
        got2 = fs.read(out)
        check(got2 and same(json.loads(got2), json.loads(got)), f'{n}: opnieuw openen en opslaan in hetzelfde bestand: nog altijd identiek')
        first_out = first_out or out
    # PDF en Excel
    pdf, xls = W('uit', 'Dossier.pdf'), W('uit', 'Materiaal.xlsx')
    d.queue(pdf)
    d.run(HELP + "__t.$('t-exp').click();await __t.sleep(2500);__t.$('pr_pdf').click();")
    for _ in range(120):
        if fs.size(pdf) > 100000:
            break
        time.sleep(1)
    check(fs.size(pdf) > 100000, f'PDF bewaard via het Windows-venster ({fs.size(pdf)} bytes)')
    d.queue(xls)
    d.run(HELP + "__t.$('t-mat').click();await __t.sleep(800);__t.$('mt_xlsx').click();")
    for _ in range(60):
        if fs.size(xls) > 3000:
            break
        time.sleep(1)
    check(fs.size(xls) > 3000, f'Excel bewaard via het Windows-venster ({fs.size(xls)} bytes)')
    # projectmap
    mapd = W('map')
    fs.write(PJ.join(mapd, 'Alfa.vsx'), open(os.path.join(exp, names[0] + '.json'), encoding='utf-8').read())
    fs.write(PJ.join(mapd, 'Beta.json'), open(os.path.join(exp, names[0] + '.json'), encoding='utf-8').read())
    fs.write(PJ.join(mapd, 'notities.txt'), 'geen project')
    fs.write(PJ.join(mapd, 'sub', 'Diep.vsx'), '{}')
    d.queue(mapd)
    cards = d.run(HELP + "__t.$('t-mp').click();await __t.sleep(800);document.querySelector('[data-mp=\"dir\"]').click();"
                  "await __t.until(()=>document.querySelectorAll('#mp_grid .mp-card:not(.mp-new)').length>=3);await __t.sleep(800);"
                  "return [...document.querySelectorAll('#mp_grid .mp-card:not(.mp-new)')].map(c=>c.textContent)")
    txt = ' '.join(cards or [])
    check('Alfa.vsx' in txt and 'Beta.json' in txt and 'notities' not in txt and 'Diep' not in txt, 'projectmap: enkel de projectbestanden uit die map verschijnen')
    # toegang: enkel wat gekozen is
    fs.write(W('geheim.json'), '{"wachtwoord":"x"}')
    res = d.run("""const I=window.__TAURI__.core.invoke,r={};
      const t=async(n,f)=>{try{await f();r[n]='toegelaten'}catch(e){r[n]='geweigerd'}};
      await t('win.ini lezen',()=>I('vs_stat',{path:'C:\\\\Windows\\\\win.ini'}));
      await t('niet-gekozen .json lezen',()=>I('vs_read_text',{path:a[0]}));
      await t('niet-gekozen map lijsten',()=>I('vs_list',{dir:a[1]}));
      await t('.exe schrijven',()=>I('vs_write_bytes',new Uint8Array([77,90]),{headers:{'x-path':encodeURIComponent(a[2])}}));
      await t('niet-gekozen .vsx schrijven',()=>I('vs_write_bytes',new Uint8Array([123,125]),{headers:{'x-path':encodeURIComponent(a[3])}}));
      await t('bestand in projectmap lezen',()=>I('vs_read_text',{path:a[4]}));
      await t('.. in pad',()=>I('vs_read_text',{path:a[5]}));
      return r""", W('geheim.json'), work, W('uit', 'virus.exe'), W('nietgekozen.vsx'), PJ.join(mapd, 'Beta.json'), PJ.join(mapd, '..', 'geheim.json'))
    want = {k: 'geweigerd' for k in res}
    want['bestand in projectmap lezen'] = 'toegelaten'
    check(res == want, f'toegang: enkel gekozen bestanden en de projectmap ({res})')
    check(fs.read(W('uit', 'virus.exe')) is None and fs.read(W('nietgekozen.vsx')) is None, 'er is niets geschreven buiten de gekozen bestanden')
    # navigatie naar buiten wordt tegengehouden
    try:
        d.run("location.href='https://example.com/';await new Promise(r=>setTimeout(r,2500));return location.host")
    except Exception:
        pass
    time.sleep(2)
    host = d.run("return location.host")
    check(host in ('tauri.localhost', 'localhost'), f'het venster kan niet naar een andere website ({host})')
    # aanval via een vervalst project
    P = '"\'><img src=x onerror="window.__pwn=1"><svg onload="window.__pwn=1"><script>window.__pwn=1</script>'
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        return P if isinstance(o, str) and not o.startswith('data:') else o
    base = json.loads(open(os.path.join(fix, 'v060-rijk.json' if 'v060-rijk' in names else names[0] + '.json'), encoding='utf-8').read())
    fs.write(W('aanval.vsx'), json.dumps(walk(base)))
    d.queue(W('aanval.vsx'))
    r = d.run(HELP + "__t.$('t-proj').click();__t.$('pj_open').click();await __t.sleep(1500);await __t.settle();"
              "for(const t of ['t-eend','t-sit','t-mat','t-mp','t-exp']){__t.$(t).click();await __t.sleep(600)}"
              "return [window.__pwn||0,document.querySelectorAll('[onerror],[onload]').length,(window.AEP_errs||[]).length]")
    check(r[0] == 0 and r[1] == 0, f'vervalst projectbestand: geen code uitgevoerd ({r})')
    errs = d.run("return window.AEP_errs||[]")
    check(not errs, 'geen fouten in het programma' + (': ' + str(errs[:2]) if errs else ''))
    d.stop()
    # herstarten: Mijn projecten en de toegang blijven
    d.start()
    d.run(HELP + "await __t.until(()=>window.AEP_project&&document.readyState==='complete');await __t.sleep(1500);if(__t.$('pj_rn'))__t.$('pj_rn').click();await __t.settle();")
    cards = d.run(HELP + "__t.$('t-mp').click();await __t.sleep(1500);return [...document.querySelectorAll('#mp_grid .mp-card:not(.mp-new)')].map(c=>c.textContent)")
    txt = ' '.join(cards or [])
    check(PJ.basename(first_out) in txt and 'niet gevonden' not in txt, 'na herstarten: projecten nog in Mijn projecten, bestanden gevonden')
    name0 = PJ.basename(first_out)[:-4]
    ok_open = d.run(HELP + "const c=[...document.querySelectorAll('#mp_grid .mp-card')].find(c=>c.querySelector('h3')&&c.textContent.includes(a[0]+'.vsx'));"
                    "if(!c)return false;c.querySelector('[data-mp=\"open\"]').click();return !!await __t.until(()=>/Geopend/.test(__t.$('pj_msg').textContent));", name0)
    check(ok_open, 'na herstarten: project openen via Mijn projecten, zonder venster')
    d.stop()


def main():
    exe, fix, exp, work = sys.argv[1:5]
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    queue = os.environ.get('VS_E2E_QUEUE') or os.path.join(work, 'wachtrij.txt')
    open(queue, 'w').close()
    results = []

    def check(c, t):
        print(('  OK   ' if c else '  FOUT ') + t, flush=True)
        results.append(bool(c))
    d = Remote(exe, queue)
    try:
        test(d, RealFS(), fix, exp, work, check)
    finally:
        d.stop()
    print('RESULTAAT:', 'ALLES OK' if all(results) else f'{results.count(False)} FOUT(EN)')
    sys.exit(0 if results and all(results) else 1)


if __name__ == '__main__':
    main()
