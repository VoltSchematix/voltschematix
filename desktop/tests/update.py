"""Melding "update beschikbaar" (1.0.9).

- Op de website: nooit een vraag, nooit een aanvraag.
- HTML-bestand op de schijf en de pagina van het programma voor Windows/Mac: eerst de vraag; zonder Ja geen enkele aanvraag;
  met Ja hoogstens een aanvraag per dag, enkel naar het ene vaste adres, zonder cookies of verwijzing.
- Het antwoord telt enkel als het precies een hoger versienummer is; al de rest (code, tekst, te lang, doorverwijzing,
  fout, traag, geen internet) geeft geen melding en komt nergens op het scherm.
- De beveiliging van de browser (CSP) laat enkel dat ene adres door.

Gebruik: python3 update.py index.html desktop/dist/index.html   (VS_BROWSER = chromium | firefox | webkit)"""
import sys, os, json, time, re, pathlib, threading, functools, http.server
from playwright.sync_api import sync_playwright
WEB = str(pathlib.Path(sys.argv[1]).resolve()); DESK = str(pathlib.Path(sys.argv[2]).resolve())
BR = os.environ.get('VS_BROWSER', 'chromium')
# de eigen versie staat in de pagina zelf
VER = re.search(r'<small>v(\d+\.\d+\.\d+)</small>', open(WEB, encoding='utf-8').read()).group(1)
# de website nabootsen: dezelfde pagina over http
class _Stil(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
_srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(_Stil, directory=os.path.dirname(WEB)))
threading.Thread(target=_srv.serve_forever, daemon=True).start()
ONLINE = 'http://127.0.0.1:%d/%s' % (_srv.server_address[1], os.path.basename(WEB))
ADR='https://voltschematix.github.io/voltschematix/versie.txt';SITE='https://voltschematix.github.io/voltschematix/'
nv=lambda d:'.'.join(str(int(x)+(1 if i==2 else 0)+d*0) for i,x in enumerate(VER.split('.')))
NEW=nv(0)
ok=0;bad=[]
def chk(n,c,info=''):
    global ok
    if c: ok+=1
    else: bad.append(n);print('  FOUT',n,str(info)[:300])
def run(p,kind,lang='nl'):
    b=getattr(p,BR).launch()
    def ctx(resp=None,store=None,width=1440):
        c=b.new_context(viewport={'width':width,'height':900})
        pre={'aep_brw':'1','aep_lang':lang}
        if store is not None: pre['aep_settings']=json.dumps(store)
        reqs=[]
        def h(route):
            r=route.request;reqs.append({'url':r.url,'method':r.method,'headers':r.headers})
            if resp is None: route.abort()
            elif callable(resp): resp(route)
            else: route.fulfill(status=200,headers={'access-control-allow-origin':'*','content-type':'text/plain'},body=resp)
        c.route(lambda u: (u.startswith('https://') or u.startswith('http://')) and '127.0.0.1' not in u.split('/')[2], h)
        pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        url=pathlib.Path(WEB).as_uri() if kind=='file' else (ONLINE if kind=='online' else pathlib.Path(DESK).as_uri())
        # eerst de instellingen klaarzetten (zonder init-script: dat laat Chromium bij file:// soms de opslag verliezen), dan pas echt starten
        hold={'on':True};c.route(lambda u: hold['on'] and u.startswith('https://'), lambda r: r.abort())
        pg.goto(url);pg.evaluate("o=>{localStorage.clear();sessionStorage.clear();for(const k in o)localStorage.setItem(k,o[k])}",pre);hold['on']=False;reqs.clear()
        pg.goto('about:blank');pg.goto(url);pg.wait_for_timeout(700)
        if pg.evaluate("!document.getElementById('pj_dlg').hidden"): pg.keyboard.press('Escape')
        return c,pg,reqs,errs
    hdr=lambda pg: pg.evaluate("(()=>{const h=document.getElementById('hdr_upd');return {vis:getComputedStyle(h).display!=='none',neu:h.classList.contains('bu-new'),t:h.querySelector('.bu-t').textContent,tvis:getComputedStyle(h.querySelector('.bu-t')).display!=='none',b:document.querySelector('#hdr_upd_b span:last-child').textContent,href:document.getElementById('hdr_upd_b').href}})()")
    S=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('aep_settings')||'{}')")
    T={'nl':('Versie %s beschikbaar','Downloaden','Controleer online'),'fr':('Version %s disponible','Télécharger','Vérifier en ligne'),'en':('Version %s available','Download','Check online')}[lang]
    P=kind+' '+lang+': '
    if kind=='online':
        c,pg,reqs,errs=ctx(NEW);pg.wait_for_timeout(2500)
        chk(P+'geen vraag op de website',pg.evaluate("document.getElementById('upq').hidden"));chk(P+'geen aanvraag',reqs==[],reqs);chk(P+'geen AEP_upd',pg.evaluate("typeof window.AEP_upd")=='undefined')
        c2,pg2,reqs2,_=ctx(NEW,{'upd':True});pg2.wait_for_timeout(2500);chk(P+'ook met upd=true geen aanvraag',reqs2==[],reqs2);chk(P+'geen fouten',not errs,errs);b.close();return
    # 1. eerste start: vraag, nog geen aanvraag
    c,pg,reqs,errs=ctx(NEW);pg.wait_for_timeout(2200)
    chk(P+'vraag zichtbaar',pg.is_visible('#upq'));chk(P+'geen aanvraag voor antwoord',reqs==[],reqs)
    pg.click('#upq_no');pg.wait_for_timeout(1200);chk(P+'Nee: balk weg',not pg.is_visible('#upq'));chk(P+'Nee: upd=false',S(pg).get('upd') is False,S(pg));chk(P+'Nee: geen aanvraag',reqs==[],reqs)
    pg.reload();pg.wait_for_timeout(2500);chk(P+'Nee onthouden: geen vraag meer',not pg.is_visible('#upq'));chk(P+'Nee onthouden: geen aanvraag',reqs==[],reqs);c.close()
    # 2. Ja
    c,pg,reqs,errs=ctx(NEW);pg.wait_for_timeout(2000);pg.click('#upq_ja');pg.wait_for_timeout(1200)
    chk(P+'Ja: precies 1 aanvraag naar het vaste adres',len(reqs)==1 and reqs[0]['url']==ADR and reqs[0]['method']=='GET',reqs)
    if reqs:
        hd=reqs[0]['headers'];chk(P+'geen cookie/referer/authorization',not any(k in hd for k in('cookie','referer','authorization')),hd)
        chk(P+'geen eigen kopregels',all(k in('accept','user-agent','origin','sec-ch-ua','sec-ch-ua-mobile','sec-ch-ua-platform','sec-fetch-dest','sec-fetch-mode','sec-fetch-site','accept-language','accept-encoding','cache-control','pragma','priority') for k in hd),list(hd))
    H=hdr(pg);chk(P+'melding in de kop',H['vis'] and H['neu'] and H['t']==T[0]%NEW and H['tvis'] and H['b']==T[1],H);chk(P+'knop opent de vaste pagina',H['href']==SITE,H)
    chk(P+'onthouden',S(pg).get('updv')==NEW and S(pg).get('upd') is True,S(pg))
    pg.reload();pg.wait_for_timeout(2600);H=hdr(pg);chk(P+'na herladen: melding uit het geheugen',H['neu'] and H['t']==T[0]%NEW,H);chk(P+'zelfde dag: geen tweede aanvraag',len(reqs)==1,len(reqs))
    pg.evaluate("(()=>{const o=JSON.parse(localStorage.getItem('aep_settings'));o.updt=Date.now()-2*864e5;localStorage.setItem('aep_settings',JSON.stringify(o))})()");pg.reload();pg.wait_for_timeout(2600);chk(P+'na een dag: 1 nieuwe aanvraag',len(reqs)==2,len(reqs))
    # venster via versienummer
    pg.click('.brand small');pg.wait_for_timeout(400);chk(P+'venster met vinkje aan',pg.is_checked('#vs_updc'));pg.uncheck('#vs_updc');pg.wait_for_timeout(300)
    H=hdr(pg);chk(P+'uitzetten: melding weg',not H['neu'] and H['b']==T[2],H);chk(P+'uitzetten: upd=false, gegevens gewist',S(pg).get('upd') is False and 'updv' not in S(pg) and 'updt' not in S(pg),S(pg))
    n=len(reqs);pg.reload();pg.wait_for_timeout(2600);chk(P+'uit: geen aanvraag bij start',len(reqs)==n,len(reqs));chk(P+'uit: geen vraag opnieuw',not pg.is_visible('#upq'))
    pg.click('.brand small');pg.wait_for_timeout(300);pg.check('#vs_updc');pg.wait_for_timeout(900);chk(P+'aanzetten: meteen 1 aanvraag',len(reqs)==n+1,len(reqs));chk(P+'venster meldt nieuwe versie',NEW in pg.inner_text('#vs_upds'),pg.inner_text('#vs_upds'))
    chk(P+'geen fouten',not errs,errs);c.close()
    if lang!='nl': b.close();return
    # 3. antwoorden die niet kloppen
    def redirect(route): route.fulfill(status=302,headers={'location':'https://example.com/x','access-control-allow-origin':'*'})
    def nf(route): route.fulfill(status=404,headers={'access-control-allow-origin':'*'},body=NEW)
    def slow(route): time.sleep(7.5); route.fulfill(status=200,headers={'access-control-allow-origin':'*'},body=NEW)
    def nocors(route): route.fulfill(status=200,body=NEW)
    lower='.'.join(VER.split('.')[:2]+[str(max(0,int(VER.split('.')[2])-1))])
    cases=[('script','<script>alert(1)</script>'),('html na nummer',NEW+'\n<b>klik</b>'),('lang','9'*5000),('leeg',''),('gelijk',VER),('lager',lower),('5 cijfers','99999.1.1'),('vier delen',NEW+'.1'),('v ervoor','v'+NEW),('tekst','Nieuwe versie! Ga naar http://kwaad.example'),('json','{"v":"%s"}'%NEW),('unicode cijfers','１.０.９'),
           ('doorverwijzing',redirect),('404',nf),('geen internet',None),('traag',slow)]
    for name,resp in cases:
        c,pg,reqs,errs=ctx(resp,{'upd':True});pg.wait_for_timeout(9500 if name=='traag' else 2600);H=hdr(pg)
        chk(P+'fout antwoord ['+name+']: geen melding',not H['neu'] and H['b']==T[2],H);chk(P+'['+name+'] niets onthouden',not S(pg).get('updv'),S(pg));chk(P+'['+name+'] 1 aanvraag, geen naar elders',len(reqs)==1 and reqs[0]['url']==ADR,[r['url'] for r in reqs]);chk(P+'['+name+'] geen fouten',not errs,errs)
        chk(P+'['+name+'] nergens tekst uit het antwoord',pg.evaluate("!/kwaad|klik<|alert\\(1\\)/.test(document.body.innerText)"));c.close()
    # goed met witruimte
    c,pg,reqs,errs=ctx('  '+NEW+' \n',{'upd':True});pg.wait_for_timeout(2600);chk(P+'nummer met witruimte aanvaard',hdr(pg)['neu'],hdr(pg));c.close()
    big='.'.join([VER.split('.')[0],str(int(VER.split('.')[1])+1),'0']);c,pg,reqs,errs=ctx(big,{'upd':True});pg.wait_for_timeout(2600);chk(P+'hoger middendeel aanvaard',hdr(pg)['t']==T[0]%big,hdr(pg));c.close()
    # oude melding verdwijnt als je intussen bijgewerkt bent
    c,pg,reqs,errs=ctx(VER,{'upd':True,'updv':VER,'updt':1});pg.wait_for_timeout(2600);chk(P+'onthouden versie niet hoger: geen melding',not hdr(pg)['neu'],hdr(pg));c.close()
    c,pg,reqs,errs=ctx(NEW,{'upd':True,'updv':'<img src=x onerror=alert(1)>','updt':0});pg.wait_for_timeout(2600);chk(P+'vervalst geheugen genegeerd',hdr(pg)['t']==T[0]%NEW and pg.locator('#hdr_upd img').count()==0,hdr(pg));c.close()
    # CSP: enkel dat ene adres
    c,pg,reqs,errs=ctx(NEW,{'upd':False});pg.wait_for_timeout(1500)
    for u in ['https://voltschematix.github.io/voltschematix/versie.txt?x=1','https://voltschematix.github.io/voltschematix/andere.txt','https://voltschematix.github.io/voltschematix/versie.txt/x','https://voltschematix.github.io/','https://example.com/','https://github.com/VoltSchematix/voltschematix']:
        r=pg.evaluate("u=>fetch(u,{mode:'no-cors'}).then(()=>'ok').catch(()=>'geweigerd')",u)
        exp='ok' if u.endswith('versie.txt?x=1') else 'geweigerd'
        chk(P+'CSP '+u,r==exp,r)
    chk(P+'CSP liet enkel het versie-adres door',all(r['url'].split('?')[0]==ADR for r in reqs),[r['url'] for r in reqs]);c.close()
    # smal scherm
    for w in [1280,1000,700,400]:
        c,pg,reqs,errs=ctx(NEW,{'upd':True},width=w);pg.wait_for_timeout(2600);H=hdr(pg);ov=pg.evaluate("document.documentElement.scrollWidth-innerWidth")
        chk(P+f'breedte {w}: melding zichtbaar, geen overloop',H['neu'] and H['tvis'] and ov<=1,(H,ov))
        c.close()
    b.close()
with sync_playwright() as p:
    for kind,lang in [('online','nl'),('file','nl'),('file','fr'),('file','en'),('desk','nl'),('desk','fr')]:
        run(p,kind,lang)
print(BR, 'versie', VER, 'RESULTAAT', ok, 'ok', len(bad), 'fout')
sys.exit(1 if bad else 0)
