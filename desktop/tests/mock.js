(()=>{const FS=JSON.parse(localStorage.getItem('__mockfs')||'{}');const save=()=>{try{const o={};for(const k in FS)if((FS[k].d||'').length<400000)o[k]=FS[k];localStorage.setItem('__mockfs',JSON.stringify(o))}catch(e){}};
 const A0=JSON.parse(localStorage.getItem('__mockallow')||'{"f":[],"d":[]}');const ALLOW={f:new Set(A0.f),d:new Set(A0.d)};const saveA=()=>localStorage.setItem('__mockallow',JSON.stringify({f:[...ALLOW.f],d:[...ALLOW.d]}));
 window.__mock={FS,next:[],calls:[],launch:null,asks:[],closed:false,opened:[]};
 const pop=()=>window.__mock.next.shift();
 const dec=new TextDecoder();
 window.__TAURI__={core:{invoke:async(cmd,args,opt)=>{window.__mock.calls.push(cmd);
   const ok=p=>{p=String(p).toLowerCase();if(ALLOW.f.has(p))return true;const i=p.lastIndexOf('\\');return /\.(vsx|json)$/.test(p)&&ALLOW.d.has(p.slice(0,i))};
   if(cmd==='vs_stat'||cmd==='vs_read_text'){if(!ok(args.path))throw 'geen toegang tot dit bestand'}
   if(cmd==='vs_write_bytes'&&(!ok(decodeURIComponent(opt.headers['x-path']))||!/\.(vsx|json|pdf)$/i.test(decodeURIComponent(opt.headers['x-path']))))throw 'geen toegang tot dit bestand';
   if(window.__mock.failWrite&&cmd==='vs_write_bytes')throw window.__mock.failWrite;
   if(cmd==='vs_stat'){const f=FS[args.path];if(!f)throw 'niet gevonden';return {size:f.d.length,mtime:f.m}}
   if(cmd==='vs_read_text'){const f=FS[args.path];if(!f)throw 'niet gevonden';return f.d}
   if(cmd==='vs_write_bytes'){const p=decodeURIComponent(opt.headers['x-path']);FS[p]={d:dec.decode(args),m:Date.now(),n:args.length};save();return null}
   if(cmd==='launch_file'){const l=window.__mock.launch;if(l)ALLOW.f.add(l.toLowerCase());window.__mock.launch=null;return l}
   if(cmd==='vs_pick_save'||cmd==='vs_pick_open'){window.__mock.calls.push([cmd==='vs_pick_save'?'save':'open',cmd==='vs_pick_save'?(args.dir?args.dir+'\\':'')+args.name:args&&args.dir,args&&args.kind]);let v=pop();if(!v)return null;
     if(cmd==='vs_pick_save'){const ex={pdf:['pdf']}[args.kind]||['vsx','json'];if(!new RegExp('\\.('+ex.join('|')+')$','i').test(v))v+='.'+ex[0]}
     ALLOW.f.add(v.toLowerCase());saveA();return v}
   throw 'onbekend '+cmd}},
  dialog:{save:async o=>{window.__mock.calls.push(['save',o.defaultPath]);return pop()},open:async o=>{window.__mock.calls.push(['open',o.directory]);return pop()},
   ask:async(m,o)=>{window.__mock.asks.push(m);return pop()}},
  window:{getCurrentWindow:()=>({close:async()=>{const ev={p:false,preventDefault(){this.p=true}};for(const h of (window.__mock.ch||[]))await h(ev);if(!ev.p)window.__mock.closed=true},
    destroy:async()=>{window.__mock.closed=true},onCloseRequested:async h=>{(window.__mock.ch=window.__mock.ch||[]).push(h)}})},
  opener:{openUrl:async u=>{if(!/^https:\/\/(github\.com\/VoltSchematix\/voltschematix\/|voltschematix\.github\.io\/voltschematix\/)/.test(String(u))){window.__mock.refused=(window.__mock.refused||[]).concat(u);throw 'opener: adres niet toegelaten'}window.__mock.opened.push(u)}}};
})();
