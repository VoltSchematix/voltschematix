"""Doorkijk op het situatieplan (1.0.10): het tekenvlak wordt een gat in het venster, enkel in het programma voor Windows.

- Knop enkel in het Windows-programma; niet in de website, het HTML-bestand of het Mac-programma.
- Enkel het tekenvlak wordt doorzichtig; de rest van het venster niet; op andere tabbladen en op de afdruk nooit.
- Beeld vastzetten: zoomen en schuiven doen niets, tekenen kan nog. Venster bovenaan houden wordt aan Windows gevraagd.
- Niets ervan komt in het project.
De doorzichtigheid zelf wordt gemeten op een schermafbeelding zonder achtergrond (enkel in Chromium, als Pillow aanwezig is).

Gebruik: python3 doorkijk.py index.html desktop/dist/index.html   (VS_BROWSER = chromium | firefox | webkit)"""
import re, sys, os, pathlib, tempfile
from playwright.sync_api import sync_playwright
try: from PIL import Image
except Exception: Image = None
BR = os.environ.get('VS_BROWSER', 'chromium')
TMP = tempfile.mkdtemp()
STUB=re.search(r'STUB = """(.*?)"""',(pathlib.Path(__file__).parent/'update.py').read_text(encoding='utf-8'),re.S).group(1)
STUB+="\nwindow.__TAURI__.window={getCurrentWindow:()=>({setAlwaysOnTop:v=>{(window.__aot=window.__aot||[]).push(v);return Promise.resolve()},onCloseRequested:()=>Promise.resolve(()=>{}),close:()=>Promise.resolve(),destroy:()=>Promise.resolve()})};"
Wb=pathlib.Path(sys.argv[1]).resolve().as_uri();D=pathlib.Path(sys.argv[2]).resolve().as_uri()
PIX=Image is not None and BR=='chromium'
res=[]
def chk(n,c,i=''):
    res.append((n,bool(c)))
    if not c: print('  FOUT',n,str(i)[:300],flush=True)
with sync_playwright() as p:
    b=getattr(p,BR).launch()
    def open_(url,stub=True,ua=None):
        c=b.new_context(viewport={'width':1440,'height':900},**({'user_agent':ua} if ua else {}))
        if stub: c.add_init_script(STUB)
        pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]));pg.goto(url);pg.wait_for_timeout(900)
        if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
        if pg.is_visible('#upq'): pg.click('#upq_no')
        pg.click('#t-sit');pg.wait_for_timeout(500);return pg,errs
    # niet in de website / het HTML-bestand / op de Mac
    pg,_=open_(Wb,stub=False);chk('HTML-bestand: geen knop Doorkijk',not pg.is_visible('#sp_dkm'))
    pg,_=open_(D,ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)');chk('Mac-programma: geen knop Doorkijk',not pg.is_visible('#sp_dkm'),pg.evaluate("window.AEP_dk.staat()"))
    # Windows-programma
    # het programma voor Windows meldt zich als Windows (de testbrowser WebKit meldt zich anders als Mac)
    pg,errs=open_(D,ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0');chk('Windows-programma: knop Doorkijk zichtbaar',pg.is_visible('#sp_dkm'))
    # iets tekenen
    def toScr(x,y): return pg.evaluate("([x,y])=>{const sv=document.querySelector('#sp_cv svg');const pt=sv.createSVGPoint();pt.x=x;pt.y=y;const q=pt.matrixTransform(sv.getScreenCTM());return [q.x,q.y]}",[x,y])
    pg.click('#sp_list [data-t="muur"]')
    for a,q in [((1500,1500),(8000,1500)),((8000,1500),(8000,6000)),((8000,6000),(1500,6000)),((1500,6000),(1500,1500))]:
        pg.mouse.click(*toScr(*a));pg.mouse.click(*toScr(*q));pg.keyboard.press('Escape');pg.click('#sp_list [data-t="muur"]')
    pg.keyboard.press('Escape')
    def alpha(path):
        im=Image.open(path).convert('RGBA');r=pg.evaluate("(()=>{const r=document.getElementById('sp_cv').getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]})()")
        A=im.split()[3];ins=A.crop((int(r[0])+6,int(r[1])+6,int(r[2])-22,int(r[3])-22));out=[A.getpixel((20,20)),A.getpixel((200,400)),A.getpixel((700,140)),A.getpixel((700,890)),A.getpixel((1430,60))]
        hist=ins.histogram();n=sum(hist);return {'buiten':out,'binnen_min':min(i for i,v in enumerate(hist) if v),'binnen_doorzichtig_%':round(100*sum(hist[:250])/n),'binnen_vol_doorzichtig_%':round(100*hist[0]/n)},im,r
    if PIX: pg.screenshot(path=TMP+'/dk0.png',omit_background=True);a0,_,_=alpha(TMP+'/dk0.png');chk('uit: nergens doorzichtig',a0['binnen_min']==255 and all(v==255 for v in a0['buiten']),a0)
    pg.click('#sp_dkm summary');pg.wait_for_timeout(150)
    pg.locator('#sp_dk').fill('100');pg.wait_for_timeout(600);pg.keyboard.press('Escape');pg.mouse.click(700,500);pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('sp_dkm').open=false");pg.wait_for_timeout(200)
    if PIX: pg.screenshot(path=TMP+'/dk100.png',omit_background=True);a1,im1,r=alpha(TMP+'/dk100.png');chk('100 %: tekenvlak doorzichtig, de rest van het venster niet',a1['binnen_doorzichtig_%']>90 and a1['binnen_vol_doorzichtig_%']>30 and all(v==255 for v in a1['buiten']),a1)
    st=pg.evaluate("window.AEP_dk.staat()");chk('toestand aan',st['aan'] and st['dk']==1,st)
    # muren blijven zichtbaar: er zijn ondoorzichtige pixels binnen
    if PIX: chk('de tekening zelf blijft zichtbaar',a1['binnen_doorzichtig_%']<100,a1)
    pg.evaluate("document.getElementById('sp_dkm').open=true");pg.locator('#sp_dk').fill('60');pg.wait_for_timeout(500);pg.evaluate("document.getElementById('sp_dkm').open=false");pg.wait_for_timeout(200)
    if PIX: pg.screenshot(path=TMP+'/dk60.png',omit_background=True);a2,im2,_=alpha(TMP+'/dk60.png');chk('60 %: tekenvlak half doorzichtig',a2['binnen_vol_doorzichtig_%']<5 and a2['binnen_doorzichtig_%']>80,a2)
    # ander tabblad: venster weer normaal
    pg.click('#t-eend');pg.wait_for_timeout(700)
    if PIX: pg.screenshot(path=TMP+'/dk_eend.png',omit_background=True);A=Image.open(TMP+'/dk_eend.png').convert('RGBA').split()[3];chk('eendraadschema: nergens doorzichtig',A.getextrema()==(255,255),A.getextrema())
    chk('body.dk weg op een ander tabblad',not pg.evaluate("document.body.classList.contains('dk')"))
    pg.click('#t-exp');pg.wait_for_timeout(1500);n=pg.evaluate("window.AEP_plan.builders().map(f=>f(1,1).svg).join('').includes('fill-opacity=\"0.4')");chk('afdruk: blad niet doorzichtig',not n)
    pg.click('#t-sit');pg.wait_for_timeout(700);chk('terug op het situatieplan: weer aan',pg.evaluate("document.body.classList.contains('dk')"))
    # beeld vastzetten
    pg.evaluate("document.getElementById('sp_dkm').open=true");pg.check('#sp_dklock');pg.evaluate("document.getElementById('sp_dkm').open=false")
    vb=lambda: pg.evaluate("(()=>{const sv=document.getElementById('sp_sv'),cv=document.getElementById('sp_cv');return [sv.getAttribute('width'),cv.scrollLeft,cv.scrollTop]})()")
    v0=vb();pg.click('#sp_zi');pg.click('#sp_zo');pg.click('#sp_fit');pg.mouse.move(800,500);pg.keyboard.down('Control');pg.mouse.wheel(0,-400);pg.keyboard.up('Control');pg.mouse.wheel(0,300);pg.mouse.wheel(300,0);pg.wait_for_timeout(500)
    chk('vastgezet: zoomen en schuiven doen niets',vb()==v0,(v0,vb()))
    n0=len(pg.evaluate("window.AEP_plan.get().pages[0].els"));pg.click('#sp_list [data-t="muur"]');pg.mouse.click(*toScr(3000,3000));pg.mouse.click(*toScr(6000,3000));pg.keyboard.press('Escape');pg.wait_for_timeout(200)
    chk('vastgezet: tekenen kan nog',len(pg.evaluate("window.AEP_plan.get().pages[0].els"))==n0+1)
    pg.evaluate("document.getElementById('sp_dkm').open=true");pg.uncheck('#sp_dklock');pg.click('#sp_zi');pg.wait_for_timeout(200);chk('losgemaakt: zoomen werkt weer',vb()!=v0,(v0,vb()));pg.click('#sp_fit')
    # bovenaan houden
    pg.evaluate("document.getElementById('sp_dkm').open=true");pg.wait_for_timeout(150);pg.check('#sp_dktop');pg.wait_for_timeout(150);chk('bovenaan houden gevraagd aan Windows',pg.evaluate("window.__aot")==[True],pg.evaluate("window.__aot"))
    pg.locator('#sp_dk').fill('0');pg.wait_for_timeout(400);chk('doorkijk uit: bovenaan houden ook uit',pg.evaluate("window.__aot")==[True,False] and not pg.is_checked('#sp_dktop'),pg.evaluate("window.__aot"))
    pg.evaluate("document.getElementById('sp_dkm').open=false")
    if PIX: pg.screenshot(path=TMP+'/dk_uit.png',omit_background=True);A=Image.open(TMP+'/dk_uit.png').convert('RGBA').split()[3];chk('doorkijk uit: venster weer helemaal dicht',A.getextrema()==(255,255),A.getextrema())
    # niets in het project
    snap=pg.evaluate("JSON.stringify(window.AEP_project.snapshot())");chk('niets van doorkijk in het project','dk' not in [k for k in re.findall(r'"([a-zA-Z_]+)":',snap)] and 'fill-opacity' not in snap)
    chk('geen scriptfouten',not errs,errs[:3])
    b.close()
print(BR,'RESULTAAT',sum(1 for _,c in res if c),'ok',sum(1 for _,c in res if not c),'fout','' if PIX else '(zonder pixelmeting)')
sys.exit(1 if any(not c for _,c in res) else 0)
