"""Koppeling eendraadschema -> situatieplan (1.0.9): verwijderen, aantal verlagen en 'Niet op het situatieplan'
halen het symbool van het plan; ongedaan maken zet het terug. Verwijderen op het plan laat het schema ongemoeid.

Gebruik: python3 koppeling.py PAGINA.html FIXTURES/ [nl|fr|en]   (VS_BROWSER = chromium | firefox | webkit)"""
import sys, os, json, pathlib
from playwright.sync_api import sync_playwright
URL = pathlib.Path(sys.argv[1]).resolve().as_uri()
src = (pathlib.Path(sys.argv[2]).resolve() / 'lindenlaan.vsx').read_text(encoding='utf-8')
LANG = sys.argv[3] if len(sys.argv) > 3 else 'nl'
BR = os.environ.get('VS_BROWSER', 'chromium')
OPEN="""([src,nm])=>{const f=new File([src],nm);const h={kind:'file',name:nm,getFile:async()=>f,queryPermission:async()=>'granted',requestPermission:async()=>'granted',isSameEntry:async()=>false,createWritable:async()=>({write:async()=>{},close:async()=>{}})};return window.AEP_project.openHandle(h)}"""
ok=0;bad=[]
def chk(n,c,x=''):
    global ok
    if c: ok+=1
    else: bad.append(n);print('FOUT',n,str(x)[:300])
with sync_playwright() as p:
    b=getattr(p,BR).launch();c=b.new_context(viewport={'width':1440,'height':900});c.add_init_script("localStorage.setItem('aep_brw','1');localStorage.setItem('aep_lang','%s');localStorage.setItem('aep_settings',JSON.stringify({upd:false}))" % LANG);pg=c.new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.goto(URL);pg.wait_for_timeout(900)
    if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
    pg.evaluate(OPEN,[src,'lindenlaan.vsx']);pg.wait_for_timeout(1000)
    def PL():
        P=pg.evaluate("window.AEP_plan.get()")
        for g in P['pages']: g.pop('ext',None)   # afmetingen van het blad: worden bij het tekenen herrekend
        return P
    syms=lambda P=None:[(pi,i,e) for pi,pgx in enumerate((P or PL())['pages']) for i,e in enumerate(pgx['els']) if e['type']=='sym' and not e.get('loose')]
    Q=lambda: pg.evaluate("(()=>{const B=window.AEP_plan.builders();return B.map((f,i)=>f(i+1,B.length).svg).join('')})()")
    tab=lambda t:(pg.click('#t-'+t),pg.wait_for_timeout(600))
    P0=PL();S0=syms(P0);n0=len(S0);chk('voorbeeld heeft symbolen op het plan',n0>20,n0)
    chk('geen pg.weg in het bestand',all('weg' not in x for x in P0['pages']))
    # schema-info: item-id -> selector
    info=pg.evaluate("""()=>{const s=window.AEP_sch.get();const out=[];s.groups.forEach((g,gi)=>(g.kringen||[]).forEach((k,ki)=>(k.punten||[]).forEach((p,pi)=>(p.items||[]).forEach((it,ii)=>out.push({id:it.id,s:it.s,aantal:it.aantal||1,sel:`i:${gi}:${ki}:${pi}:${ii}`,ksel:`k:${gi}:${ki}`,gi,ki,pi,ii,n:p.items.length})))));return out}""")
    byid={x['id']:x for x in info}
    cntp={}
    for _,_,e in S0: cntp[e['id']]=cntp.get(e['id'],0)+1
    # 1. een symbool verwijderen op het schema
    cand=[x for x in info if cntp.get(x['id'])==1 and x['s'] not in('sc',) and x['n']==1]
    t=cand[0];pos0=[(pi,i,e['x'],e['y']) for pi,i,e in S0 if e['id']==t['id']][0]
    tab('eend');pg.locator(f'#sv [data-sel="{t["sel"]}"]').first.click(force=True);pg.wait_for_timeout(250);pg.keyboard.press('Delete');pg.wait_for_timeout(400)
    chk('item weg op het schema',pg.evaluate("id=>!JSON.stringify(window.AEP_sch.get()).includes('\"'+id+'\"')",t['id']))
    tab('sit');S1=syms()
    chk('1 symbool: ook weg van het plan',len(S1)==n0-1 and all(e['id']!=t['id'] for _,_,e in S1),(len(S1),n0))
    chk('1 symbool: geen vraagteken op het scherm',pg.evaluate("![...document.querySelectorAll('#sp_cv text')].some(t=>t.textContent==='?')"))
    chk('1 symbool: geen vraagteken op de afdruk','>?<' not in Q())
    chk('1 symbool: de rest staat nog op dezelfde plaats',[(e['id'],e['x'],e['y']) for _,_,e in S1]==[(e['id'],e['x'],e['y']) for _,_,e in S0 if e['id']!=t['id']])
    tab('eend');pg.keyboard.press('Control+z');pg.wait_for_timeout(400);tab('sit');S2=syms()
    chk('1 symbool: Ctrl+Z op het schema zet het terug op dezelfde plek en plaats in de lijst',[(pi,i,e['id'],e['x'],e['y']) for pi,i,e in S2]==[(pi,i,e['id'],e['x'],e['y']) for pi,i,e in S0],(len(S2),n0))
    tab('eend');pg.keyboard.press('Control+y');pg.wait_for_timeout(400);tab('sit');chk('1 symbool: Ctrl+Y haalt het weer weg',len(syms())==n0-1)
    tab('eend');pg.keyboard.press('Control+z');pg.wait_for_timeout(400);tab('sit');chk('terug volledig',json.dumps(PL(),sort_keys=True)==json.dumps(P0,sort_keys=True))
    # 2. een hele kring verwijderen
    kk={}
    for x in info:
        if cntp.get(x['id']): kk.setdefault(x['ksel'],[]).append(x['id'])
    ksel,ids=sorted(kk.items(),key=lambda a:-len(a[1]))[0];nk=sum(cntp[i] for i in ids)
    tab('eend');pg.locator(f'#sv [data-sel="{ksel}"]').first.click(force=True);pg.wait_for_timeout(250);pg.keyboard.press('Delete');pg.wait_for_timeout(300)
    if pg.locator('#pj_yes').count() and pg.locator('#pj_yes').is_visible(): pg.click('#pj_yes');pg.wait_for_timeout(300)
    gone=pg.evaluate("ids=>{const j=JSON.stringify(window.AEP_sch.get());return ids.every(i=>!j.includes('\"'+i+'\"'))}",ids)
    chk('kring weg op het schema',gone,ksel)
    tab('sit');chk(f'kring: alle {nk} symbolen weg van het plan',len(syms())==n0-nk,(len(syms()),n0,nk));chk('kring: geen vraagteken','>?<' not in Q())
    tab('eend');pg.keyboard.press('Control+z');pg.wait_for_timeout(400);tab('sit');chk('kring: Ctrl+Z zet alles terug',json.dumps(PL(),sort_keys=True)==json.dumps(P0,sort_keys=True))
    # 3. aantal verlagen en weer verhogen
    multi=[x for x in info if cntp.get(x['id'],0)>=2 and x['s']!='sc' and cntp[x['id']]==x['aantal']]
    over=[x for x in info if cntp.get(x['id'],0)>x['aantal'] and x['s']!='sc']
    if multi:
        m=multi[0];k=cntp[m['id']];posm=[(pi,i,e['x'],e['y']) for pi,i,e in S0 if e['id']==m['id']]
        setn=lambda n: pg.evaluate("""([id,n])=>{const s=window.AEP_sch.get();s.groups.forEach(g=>(g.kringen||[]).forEach(k=>(k.punten||[]).forEach(p=>(p.items||[]).forEach(it=>{if(it.id===id)it.aantal=n}))));window.AEP_sch.set(s)}""",[m['id'],n])
        setn(1);tab('sit');Sx=[(pi,i,e['x'],e['y']) for pi,i,e in syms() if e['id']==m['id']]
        chk(f'aantal {k} -> 1: nog 1 op het plan, de eerste',Sx==posm[:1],(Sx,posm))
        setn(k);tab('sit');chk('aantal terug: zelfde plaatsen terug',json.dumps(PL(),sort_keys=True)==json.dumps(P0,sort_keys=True))
    else: print('geen meervoudig symbool in het voorbeeld')
    if over:
        o=over[0];ko=cntp[o['id']];seto=lambda n: pg.evaluate("""([id,n])=>{const s=window.AEP_sch.get();s.groups.forEach(g=>(g.kringen||[]).forEach(k=>(k.punten||[]).forEach(p=>(p.items||[]).forEach(it=>{if(it.id===id)it.aantal=n}))));window.AEP_sch.set(s)}""",[o['id'],n])
        tab('sit');chk(f"te veel geplaatst in een oud bestand ({ko} keer, aantal {o['aantal']}): blijft staan",len([1 for _,_,e in syms() if e['id']==o['id']])==ko)
        if o['aantal']>1:
            seto(o['aantal']-1);tab('sit');chk('aantal verlaagd: tot het nieuwe aantal',len([1 for _,_,e in syms() if e['id']==o['id']])==o['aantal']-1)
            seto(o['aantal']);tab('sit');chk('aantal terug: alles terug zoals het stond, ook wat te veel was',json.dumps(PL(),sort_keys=True)==json.dumps(P0,sort_keys=True))
    # 4. Niet op het situatieplan (via het vinkje in het paneel)
    tab('eend');pg.locator(f'#sv [data-sel="{t["sel"]}"]').first.click(force=True);pg.wait_for_timeout(250)
    cb=pg.locator('#props input[data-f="noplan"], #props input[data-if="noplan"], #props input[type=checkbox]').filter(has=pg.locator('xpath=self::*')).all()
    lab=pg.locator('#props label.check').filter(has_text={'nl':'Niet op het situatieplan','fr':'Pas sur le plan de situation','en':'Not on the site plan'}[LANG]).first
    lab.locator('input').check();pg.wait_for_timeout(300);tab('sit')
    chk('vinkje Niet op het situatieplan: weg van het plan',all(e['id']!=t['id'] for _,_,e in syms()) and len(syms())==n0-1)
    pg.evaluate("""id=>{const s=window.AEP_sch.get();s.groups.forEach(g=>(g.kringen||[]).forEach(k=>(k.punten||[]).forEach(p=>(p.items||[]).forEach(it=>{if(it.id===id)delete it.noplan}))));window.AEP_sch.set(s)}""",t['id']);tab('sit')
    chk('vinkje weg: terug op dezelfde plek',json.dumps(PL(),sort_keys=True)==json.dumps(P0,sort_keys=True))
    # 5. wissen op het plan laat het schema ongemoeid
    sj=pg.evaluate("JSON.stringify(window.AEP_sch.get())")
    pg.evaluate("""id=>{const p=window.AEP_plan.get();p.pages.forEach(g=>{g.els=g.els.filter(e=>!(e.type==='sym'&&e.id===id))});window.AEP_plan.set(p)}""",t['id']);pg.wait_for_timeout(400)
    chk('weg van het plan: schema ongewijzigd',pg.evaluate("JSON.stringify(window.AEP_sch.get())")==sj)
    chk('weg van het plan: 1 minder geplaatst',len(syms())==n0-1)
    # 6. oud bestand met een wees (vraagteken) en met te veel plaatsingen
    P=json.loads(json.dumps(P0));P['pages'][0]['els'].append({'type':'sym','id':'bestaatniet','x':1000,'y':1000,'rot':0});e0=S0[0][2];P['pages'][0]['els'].append({**e0,'x':e0['x']+500})
    pg.evaluate("p=>window.AEP_plan.set(p)",P);pg.wait_for_timeout(500);tab('sit')
    chk('oud bestand met wees: geen vraagteken, niet in het bestand',('>?<' not in Q()) and 'bestaatniet' not in json.dumps(PL()))
    chk('oud bestand: wat al te veel op het plan stond, blijft staan (oude bestanden zien er hetzelfde uit)',len([1 for _,_,e in syms() if e['id']==e0['id']])==cntp[e0['id']]+1)
    chk('losse symbolen, muren en tekst blijven',[e for g in PL()['pages'] for e in g['els'] if e['type']!='sym' or e.get('loose')]==[e for g in P0['pages'] for e in g['els'] if e['type']!='sym' or e.get('loose')])
    chk('geen scriptfouten',not errs,errs)
print(f'RESULTAAT {ok} ok {len(bad)} fout',bad)
sys.exit(1 if bad else 0)
