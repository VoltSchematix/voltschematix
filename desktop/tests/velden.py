"""Keuzevakken (kiezen of zelf typen) en verborgen eigenschappen (1.0.9).

Kabeltype, kabel, voedingskabel, controleorganisme, zekering en kortsluitvermogen: klikken toont de volledige lijst,
typen mag altijd, een ongeldig getal springt terug. Eigenschappen die bij de gekozen soort niets doen, staan er niet.

Gebruik: python3 velden.py PAGINA.html FIXTURES/ [nl|fr|en]   (VS_BROWSER = chromium | firefox | webkit)"""
import sys, os, json, pathlib
from playwright.sync_api import sync_playwright
PAGE = pathlib.Path(sys.argv[1]).resolve()
FIX = pathlib.Path(sys.argv[2]).resolve()
LANG = sys.argv[3] if len(sys.argv) > 3 else 'nl'
BR = os.environ.get('VS_BROWSER', 'chromium')
URL = PAGE.as_uri()
src = (FIX / 'lindenlaan.vsx').read_text(encoding='utf-8')
INIT = "localStorage.setItem('aep_brw','1');localStorage.setItem('aep_lang','%s');localStorage.setItem('aep_settings',JSON.stringify({upd:false}))" % LANG
OPEN="""([src,nm])=>{const f=new File([src],nm);const h={kind:'file',name:nm,getFile:async()=>f,queryPermission:async()=>'granted',requestPermission:async()=>'granted',isSameEntry:async()=>false,createWritable:async()=>({write:async()=>{},close:async()=>{}})};return window.AEP_project.openHandle(h)}"""
ok=0;bad=[]
def chk(n,c,info=''):
    global ok
    if c: ok+=1
    else: bad.append(n+' '+str(info)[:200]);print('  FOUT',n,str(info)[:200])
with sync_playwright() as p:
    b=getattr(p,BR).launch();c=b.new_context(viewport={'width':1440,'height':900});c.add_init_script(INIT);pg=c.new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.goto(URL);pg.wait_for_timeout(900)
    if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
    if LANG!='nl':
        try: pg.click(f'.langsw button:has-text("{LANG.upper()}")',timeout=2000);pg.wait_for_timeout(500)
        except Exception as e: print('taal?',e)
    pg.evaluate(OPEN,[src,'lindenlaan.vsx']);pg.wait_for_timeout(1000)
    pg.click('#t-eend');pg.wait_for_timeout(500)
    S=lambda: pg.evaluate("window.AEP_sch.get()")
    pop=lambda: pg.evaluate("(()=>{const P=document.getElementById('cbp');return P&&!P.hidden?[...P.children].map(r=>r.textContent):null})()")
    def selk(): pg.locator('#sv [data-sel="k:0:0"]').first.click(force=True);pg.wait_for_timeout(300)
    selk()
    # --- kabeltype
    t0=S()['groups'][0]['kringen'][0]['kabel'].get('type','')
    chk('geen typesel meer',pg.locator('#props [data-f$="typesel"]').count()==0)
    I=pg.locator('#props input[data-f$=".type"]').first;chk('1 kabeltype-vak',pg.locator('#props input[data-f$=".type"]').count()==1)
    chk('vak toont huidig type',I.input_value()==t0,(I.input_value(),t0))
    I.click();pg.wait_for_timeout(200);L=pop();chk('klik: volledige lijst',L and len(L)==12 and 'XVB' in L and 'Flex' in L,L)
    nv={'nl':'Niet vermelden','fr':'Ne pas mentionner','en':'Do not show'}[LANG];chk('niet vermelden vertaald',L and L[0]==nv,L and L[0])
    pg.locator('#cbp div',has_text='EXVB').first.click();pg.wait_for_timeout(300)
    chk('kiezen zet type',S()['groups'][0]['kringen'][0]['kabel'].get('type')=='EXVB');chk('lijst dicht na kiezen',pop() is None)
    I=pg.locator('#props input[data-f$=".type"]').first;I.click();pg.wait_for_timeout(200);L=pop();chk('volledige lijst ook als er al EXVB staat',L and len(L)==12,L)
    cur=pg.evaluate("[...document.querySelectorAll('#cbp .cur')].map(r=>r.textContent)");chk('huidige aangeduid',cur==['EXVB'],cur)
    I.fill('');I.type('xv');pg.wait_for_timeout(200);L=pop();chk('typen vernauwt',L==['XVB','XVB-F2','EXVB'],L)
    I.fill('');I.type('Eigen-K2');pg.wait_for_timeout(200);chk('geen match: lijst dicht',pop() is None,pop());pg.keyboard.press('Tab');pg.wait_for_timeout(300)
    chk('eigen type bewaard',S()['groups'][0]['kringen'][0]['kabel'].get('type')=='Eigen-K2',S()['groups'][0]['kringen'][0]['kabel'])
    I=pg.locator('#props input[data-f$=".type"]').first;chk('eigen type in zelfde vak',I.input_value()=='Eigen-K2')
    I.click();pg.wait_for_timeout(200);pg.locator('#cbp div.nv').click();pg.wait_for_timeout(300);chk('niet vermelden wist type',not S()['groups'][0]['kringen'][0]['kabel'].get('type'),S()['groups'][0]['kringen'][0]['kabel'])
    # toetsenbord
    I=pg.locator('#props input[data-f$=".type"]').first;I.focus();pg.wait_for_timeout(150)
    if pop() is None: pg.keyboard.press('ArrowDown')
    pg.keyboard.press('ArrowDown');pg.keyboard.press('ArrowDown');pg.wait_for_timeout(100);h=pg.evaluate("(document.querySelector('#cbp .hi')||{}).textContent");pg.keyboard.press('Enter');pg.wait_for_timeout(300)
    chk('pijltjes + Enter kiest',S()['groups'][0]['kringen'][0]['kabel'].get('type')==h and h in('XVB','XVB-F2'),h)
    I=pg.locator('#props input[data-f$=".type"]').first;I.click();pg.wait_for_timeout(150);pg.keyboard.press('Escape');pg.wait_for_timeout(150);chk('Esc sluit lijst',pop() is None);chk('Esc laat selectie staan',pg.locator('#props input[data-f$=".type"]').count()==1)
    # --- kabel 5G4
    K=pg.locator('#props input[data-f$=".combo"]').first;v0=K.input_value();K.click();pg.wait_for_timeout(200);L=pop();chk('kabel: volledige lijst',L and len(L)>=8 and v0 in L,(v0,L))
    pg.locator('#cbp div',has_text='5G6').first.click();pg.wait_for_timeout(300);kb=S()['groups'][0]['kringen'][0]['kabel'];chk('kabel kiezen',kb['aders']==5 and str(kb['sectie'])=='6',kb)
    K=pg.locator('#props input[data-f$=".combo"]').first;K.fill('4G95');pg.keyboard.press('Tab');pg.wait_for_timeout(300);kb=S()['groups'][0]['kringen'][0]['kabel'];chk('kabel vrij typen',kb['aders']==4 and str(kb['sectie'])=='95',kb)
    K=pg.locator('#props input[data-f$=".combo"]').first;K.fill('onzin');pg.keyboard.press('Tab');pg.wait_for_timeout(300);kb=S()['groups'][0]['kringen'][0]['kabel'];chk('kabel onzin geweigerd',kb['aders']==4 and str(kb['sectie'])=='95',kb)
    # --- zekering kring
    def inF(): return pg.locator('#props input[data-cbn="in"]').first
    i0=S()['groups'][0]['kringen'][0]['bev']['In'];chk('zekering toont A',inF().input_value()==f'{i0} A',inF().input_value())
    inF().click();pg.wait_for_timeout(200);L=pop();chk('zekering lijst',L and '16 A' in L and '63 A' in L,L)
    pg.locator('#cbp div',has_text='32 A').first.click();pg.wait_for_timeout(300);chk('zekering kiezen',S()['groups'][0]['kringen'][0]['bev']['In']==32)
    for typ,exp in [('125',125),('80 A',80),('1,6',1.6),('2.5a',2.5),('0,5',0.5)]:
        inF().fill(typ);pg.keyboard.press('Tab');pg.wait_for_timeout(300);chk('zekering '+typ,S()['groups'][0]['kringen'][0]['bev']['In']==exp,S()['groups'][0]['kringen'][0]['bev'])
    for typ in ['abc','','-16','0','99999','1,25','12 B']:
        inF().fill(typ);pg.keyboard.press('Tab');pg.wait_for_timeout(300);chk('zekering geweigerd '+repr(typ),S()['groups'][0]['kringen'][0]['bev']['In']==0.5 and inF().input_value()=='0,5 A',(S()['groups'][0]['kringen'][0]['bev'],inF().input_value()))
    chk('melding bij weigering',len(pg.inner_text('#ed_msg'))>10,pg.inner_text('#ed_msg'))
    inF().fill('125');pg.keyboard.press('Tab');pg.wait_for_timeout(300)
    svg=pg.inner_html('#sv');chk('125A op schema','125A' in svg or '125 A' in svg)
    pg.keyboard.press('Control+z');pg.wait_for_timeout(300);chk('ongedaan werkt',S()['groups'][0]['kringen'][0]['bev']['In']==0.5,S()['groups'][0]['kringen'][0]['bev'])
    # --- kortsluitvermogen
    KI=None
    for gi in range(3):
        for ki in range(6):
            l=pg.locator(f'#sv [data-sel="k:{gi}:{ki}"]')
            if not l.count(): continue
            l.first.click(force=True);pg.wait_for_timeout(250)
            if pg.locator('#props input[data-cbn="icn"]').count(): KI=(gi,ki);break
        if KI: break
    print('  icn-kring',KI)
    class _S:
        pass
    _old=S
    def S():
        d=_old()
        if KI: d['groups'][0]['kringen'][0]=d['groups'][KI[0]]['kringen'][KI[1]]
        return d
    ic=pg.locator('#props input[data-cbn="icn"]')
    if ic.count():
        ic.first.click();pg.wait_for_timeout(200);L=pop();chk('icn lijst',L==['3000','4500','6000','10000'],L)
        pg.locator('#cbp div',has_text='6000').first.click();pg.wait_for_timeout(300);chk('icn kiezen',S()['groups'][0]['kringen'][0]['bev']['icn']==6000)
        for typ,exp in [('15000',15000),('25 kA',25000),('25k',25000)]:
            pg.locator('#props input[data-cbn="icn"]').first.fill(typ);pg.keyboard.press('Tab');pg.wait_for_timeout(300);chk('icn '+typ,S()['groups'][0]['kringen'][0]['bev']['icn']==exp,S()['groups'][0]['kringen'][0]['bev'])
        for typ in ['x','500','6000,5','999999']:
            pg.locator('#props input[data-cbn="icn"]').first.fill(typ);pg.keyboard.press('Tab');pg.wait_for_timeout(300);chk('icn geweigerd '+typ,S()['groups'][0]['kringen'][0]['bev']['icn']==25000,S()['groups'][0]['kringen'][0]['bev'])
    else: chk('icn vak aanwezig',False)
    S=_old
    # --- groep (differentieel)
    pg.locator('#sv [data-sel="g:0"]').first.click(force=True);pg.wait_for_timeout(300)
    n=pg.locator('#props input[data-cbn="in"]').count();chk('groep heeft zekering-vak',n>=1,n)
    d0=S()['groups'][0].get('diff',{}).get('In');pg.locator('#props input[data-cbn="in"]').first.click();pg.wait_for_timeout(200);L=pop();chk('diff lijst',L and '40 A' in L,L)
    pg.locator('#props input[data-cbn="in"]').first.fill('125');pg.keyboard.press('Tab');pg.wait_for_timeout(300);g=S()['groups'][0];chk('diff/groep 125',(g.get('diff') or {}).get('In')==125 or (g.get('bev') or {}).get('In')==125,(g.get('diff'),g.get('bev')))
    chk('gevoeligheid blijft keuzelijst',pg.locator('#props select[data-f$="mA"]').count()>=1)
    # --- voeding
    pg.locator('#sv [data-sel="f:0"]').first.click(force=True);pg.wait_for_timeout(300)
    F=pg.locator('#props input[data-sk="kabel"]');F.click();pg.wait_for_timeout(200);L=pop();chk('voedingskabel lijst',L and len(L)>=3,L)
    if L:
        pg.locator('#cbp div').nth(1).click();pg.wait_for_timeout(400);chk('voedingskabel kiezen',pg.locator('#props input[data-sk="kabel"]').input_value()==L[1],(pg.locator('#props input[data-sk="kabel"]').input_value(),L[1]))
    F=pg.locator('#props input[data-sk="kabel"]');F.fill('');F.type('Eigen 5x35');pg.wait_for_timeout(300);chk('voedingskabel vrij typen, focus blijft',pg.locator('#props input[data-sk="kabel"]').input_value()=='Eigen 5x35' and pg.evaluate("document.activeElement.dataset.sk")=='kabel',pg.locator('#props input[data-sk="kabel"]').input_value())
    pg.keyboard.press('Tab');pg.wait_for_timeout(200)
    # --- palet andere kabel
    pg.keyboard.press('Escape')
    n=pg.locator('#pal_kab').count()
    if not n:
        for bt in pg.locator('#p-eend .pal-cat, #p-eend [data-cat]').all():
            try:
                if bt.get_attribute('data-cat')=='kab': bt.click();break
            except Exception: pass
        pg.wait_for_timeout(300);n=pg.locator('#pal_kab').count()
    if n:
        pg.locator('#pal_kab').click();pg.wait_for_timeout(200);L=pop();chk('palet kabel lijst',L and '5G4' in L,L)
        pg.keyboard.press('Escape')
    else: print('  (palet kabel niet gevonden)')
    # --- controleorganisme
    pg.click('#t-proj');pg.wait_for_timeout(400);pg.locator('#c_naam').scroll_into_view_if_needed();pg.locator('#c_naam').click();pg.wait_for_timeout(200);L=pop();chk('controleorganisme lijst',L and len(L)>=3,L)
    if L: pg.locator('#cbp div').nth(0).click();pg.wait_for_timeout(300);chk('controleorganisme kiezen',pg.input_value('#c_naam')==L[0],pg.input_value('#c_naam'))
    pg.fill('#c_naam','Eigen Keuring vzw');pg.keyboard.press('Tab');pg.wait_for_timeout(200);chk('controleorganisme vrij',pg.input_value('#c_naam')=='Eigen Keuring vzw')
    chk('geen list-attributen meer behalve aantal',pg.evaluate("[...document.querySelectorAll('input[list]')].map(e=>e.getAttribute('list')).filter(x=>x!=='aantal_opts').length")==0)
    chk('geen paginafouten',not errs,errs)

if LANG == 'nl':
    with sync_playwright() as p:
        b=getattr(p,BR).launch();c=b.new_context(viewport={'width':1440,'height':900},has_touch=(BR!='firefox'));c.add_init_script(INIT);pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        pg.goto(URL);pg.wait_for_timeout(900)
        if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
        pg.evaluate(OPEN,[src,'lindenlaan.vsx']);pg.wait_for_timeout(1000);pg.click('#t-eend');pg.wait_for_timeout(400)
        # zet in kring 0 punt 0 vier testsymbolen
        pg.evaluate("""(()=>{const s=window.AEP_sch.get();const k=s.groups[0].kringen[0];k.punten[0].items=[{s:'lamp'},{s:'sc'},{s:'sch'},{s:'tril'}];window.AEP_sch.set(s)})()""");pg.wait_for_timeout(500)
        labs=lambda: pg.evaluate("[...document.querySelectorAll('#props [data-if]')].map(e=>e.dataset.if)")
        def setp(k,v):
            e=pg.locator(f'#props [data-if="{k}"]').first
            if e.evaluate("e=>e.tagName")=='SELECT': e.select_option(str(v))
            else: e.set_checked(bool(v))
            pg.wait_for_timeout(300)
        res=[]
        def pick(i): pg.locator(f'#sv [data-sel="i:0:0:0:{i}"]').first.click(force=True);pg.wait_for_timeout(300)
        pick(0);L=labs();res.append(('lamp punt: geen buizen, wel nood','buizen' not in L and 'nood' in L,L))
        setp('soort','tl');L=labs();res.append(('lamp tl: buizen + nood','buizen' in L and 'nood' in L,L))
        setp('buizen',3);setp('soort','led');L=labs();res.append(('lamp led: geen buizen, geen nood','buizen' not in L and 'nood' not in L,L))
        it=pg.evaluate("window.AEP_sch.get().groups[0].kringen[0].punten[0].items[0]");res.append(('waarde buizen blijft bewaard',it.get('buizen')==3,it))
        pick(1);L=labs();res.append(('sc 1 fase: geen nul','nul' not in L,L));setp('fasen',3);L=labs();res.append(('sc 3 fasen: nul','nul' in L,L))
        pick(2);L=labs();res.append(('sch enk: alles',all(k in L for k in['dim','trek','rol','verk','vertr','sig']),L));setp('type','dubwis');L=labs();res.append(('sch dubwis: enkel polen/sig/vb',not any(k in L for k in['dim','trek','rol','verk','vertr']) and 'sig' in L and 'polen' in L and 'vb' in L,L))
        pick(3);L=labs();res.append(('tril glas: actief','actief' in L,L));setp('v','mech');L=labs();res.append(('tril mech: geen actief','actief' not in L,L))
        # aanraken: tik in kabeltype
        pg.locator('#sv [data-sel="k:0:0"]').first.click(force=True);pg.wait_for_timeout(300)
        I=pg.locator('#props input[data-f$=".type"]').first;(I.tap() if BR!='firefox' else I.click());pg.wait_for_timeout(300);n=pg.evaluate("(()=>{const P=document.getElementById('cbp');return P&&!P.hidden?P.children.length:0})()");res.append(('tik opent lijst',n==12,n))
        (pg.locator('#cbp div',has_text='SVV').first.tap() if BR!='firefox' else pg.locator('#cbp div',has_text='SVV').first.click());pg.wait_for_timeout(300);res.append(('tik kiest',pg.evaluate("window.AEP_sch.get().groups[0].kringen[0].kabel.type")=='SVV',''))
        I=pg.locator('#props input[data-f$=".type"]').first;I.click();pg.wait_for_timeout(250);pass
        bb=pg.evaluate("(()=>{const P=document.getElementById('cbp').getBoundingClientRect();return [P.left,P.top,P.right,P.bottom,innerWidth,innerHeight]})()");res.append(('lijst binnen venster',bb[0]>=0 and bb[3]<=bb[5] and bb[2]<=bb[4],bb))
        pg.mouse.wheel(0,200);pg.wait_for_timeout(200)
        res.append(('geen fouten',not errs,errs))
        for n,o,i in res: chk('eigenschappen: '+n,o,i)

print(BR, LANG, 'RESULTAAT', ok, 'ok', len(bad), 'fout')
sys.exit(1 if bad else 0)
