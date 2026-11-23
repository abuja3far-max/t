#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, ssl, ipaddress, random, time, uuid, threading, subprocess
import http.client, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ═════════════ الإعدادات ═════════════
WARP_SOCKS   = "socks5h://127.0.0.1:4000"
USE_WARP     = True
WARP_TRIES   = 5
IPV6_BLOCK   = "2a01:4f9:c01d:1cca::/64"
MAX_TRIES    = 10
PORT         = 8000
# ═════════════════════════════════════

BASE  = "https://outerface.venice.ai"
CHAT  = BASE + "/api/inference/chat/agents/venice"
MINT  = BASE + "/api/app/user/client_attestation/mint"
CTX   = ssl.create_default_context()
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36")

STATE = {"n": 0, "ip": "?"}
LOCK  = threading.Lock()
WARPL = threading.Lock()
NET   = ipaddress.ip_network(IPV6_BLOCK) if IPV6_BLOCK else None


def _headers(tok=None):
    h = {"User-Agent": UA, "Accept": "text/event-stream", "Accept-Encoding": "identity",
         "Origin": "https://venice.ai", "Referer": "https://venice.ai/",
         "x-venice-locale": "en", "x-venice-version": "interface@20261023.172051+9e9fe40",
         "x-venice-middleface-version": "0.1.1161",
         "x-venice-request-timestamp-ms": str(int(time.time() * 1000)),
         "x-venice-distinct-id": str(uuid.uuid4()),
         "sec-ch-ua": '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
         "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": "Linux"}
    if tok:
        h["x-venice-client-attestation"] = tok
    return h


def _opener(px=None):
    hs = [urllib.request.HTTPSHandler(context=CTX)]
    if px:
        hs.append(urllib.request.ProxyHandler({"http": px, "https": px}))
    return urllib.request.build_opener(*hs)


def call(url, body, px=None, src=None, timeout=90, tok=None):
    h = _headers(tok)
    h["Content-Type"] = "application/json"
    data = json.dumps(body).encode()
    if px:
        r = _opener(px).open(urllib.request.Request(url, data=data, headers=h), timeout=timeout)
        return r, r
    u = urllib.parse.urlsplit(url)
    conn = http.client.HTTPSConnection(u.netloc, timeout=timeout,
                                       source_address=(src, 0) if src else None, context=CTX)
    path = u.path + ("?" + u.query if u.query else "")
    conn.request("POST", path, body=data, headers=h)
    return conn, conn.getresponse()


def mint(px=None, src=None):
    env = {"nativeIntegrityOk": True, "reactStateHash": uuid.uuid4().hex,
           "sentryVersion": "10.50.0", "unexpectedGlobalsCount": 0, "webdriver": False}
    try:
        c, r = call(MINT, {"count": 1, "env": env}, px=px, src=src, timeout=20)
        t = json.loads(r.read()).get("token")
        try:
            c.close()
        except Exception:
            pass
        return t
    except Exception:
        return None


# ── WARP ─────────────────────────────────────────────
def warp_ip():
    try:
        r = _opener(WARP_SOCKS).open(urllib.request.Request(
            "https://api.ipify.org", headers={"User-Agent": UA}), timeout=12)
        return r.read(64).decode().strip() or "?"
    except Exception:
        return "?"


def warp_sh(*a):
    try:
        subprocess.run(["warp-cli", "--accept-tos", *a], timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def warp_new():
    with WARPL:
        old = STATE["ip"]
        for _ in range(3):
            warp_sh("registration", "delete")
            time.sleep(1)
            warp_sh("registration", "new")
            time.sleep(1)
            warp_sh("connect")
            for _ in range(18):
                time.sleep(1)
                ip = warp_ip()
                if ip != "?" and ip != old:
                    STATE["ip"] = ip
                    print("[warp] %s → %s" % (old, ip))
                    return ip
            old = ip
    return None


def next_v6():
    if not NET:
        return None
    return str(NET.network_address + random.randrange(0x1000, (1 << 64) - 2))


def _msg(role, text):
    if role == "assistant":
        return {"content": [{"text": text, "type": "output_text"}], "id": "agent-node:llm:0",
                "role": "assistant", "status": "completed", "type": "message"}
    return {"content": [{"annotations": [], "text": text, "type": "output_text"}],
            "id": str(uuid.uuid4())[:22], "role": "user", "status": "completed", "type": "message"}


HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>المساعد الذكي</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#F1F4F0;--panel:rgba(255,255,255,.55);--ink:#16282A;--mute:#5B6E6E;--user:#0F5C5A;--user-ink:#F2F8F7;--line:rgba(22,40,42,.12);--accent:#E0A020;--card:rgba(255,255,255,.85);--code:#13211F;--g1:#6FD3C4;--g2:#F2C66B}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1514;--panel:rgba(20,32,31,.6);--ink:#E6EEEC;--mute:#8FA3A0;--user:#1D8A85;--line:rgba(230,238,236,.1);--card:rgba(26,40,39,.85);--code:#0A1110;--g1:#1B6F69;--g2:#8A6A1E;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0D1514;--panel:rgba(20,32,31,.6);--ink:#E6EEEC;--mute:#8FA3A0;--user:#1D8A85;--line:rgba(230,238,236,.1);--card:rgba(26,40,39,.85);--code:#0A1110;--g1:#1B6F69;--g2:#8A6A1E;color-scheme:dark}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font:400 16px/1.9 "IBM Plex Sans Arabic",Tahoma,sans-serif;overflow:hidden;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
button,textarea{font:inherit;color:inherit}
.bg{position:fixed;inset:0;z-index:-1;overflow:hidden}
.bg i{position:absolute;width:55vmax;height:55vmax;border-radius:50%;filter:blur(90px);opacity:.45;animation:drift 22s ease-in-out infinite alternate}
.bg i:nth-child(1){background:var(--g1);top:-20vmax;inset-inline-start:-10vmax}
.bg i:nth-child(2){background:var(--g2);bottom:-25vmax;inset-inline-end:-10vmax;animation-duration:28s;animation-delay:-8s}
@keyframes drift{to{transform:translate(12vmax,8vmax) scale(1.2)}}
.app{display:flex;height:100%}
aside{width:290px;background:var(--panel);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border-inline-end:1px solid var(--line);display:flex;flex-direction:column;padding:16px;gap:12px;transition:transform .35s cubic-bezier(.2,.8,.2,1)}
.brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:18px}
.orb{width:28px;height:28px;border-radius:50%;flex:none;background:conic-gradient(from 0deg,var(--g1),var(--g2),var(--user),var(--g1));animation:spin 8s linear infinite;box-shadow:0 0 0 3px var(--card)}
.orb.fast{animation-duration:1.2s;box-shadow:0 0 0 3px var(--card),0 0 22px var(--g1)}
@keyframes spin{to{transform:rotate(360deg)}}
.new{background:var(--ink);color:var(--bg);border:0;border-radius:12px;padding:11px;cursor:pointer;font-weight:600;transition:transform .15s}
.new:active{transform:scale(.97)}
.list{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:2px}
.item{background:none;border:0;text-align:start;padding:9px 12px;border-radius:10px;cursor:pointer;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:background .2s,color .2s}
.item:hover{background:var(--card)}
.item.on{background:var(--card);color:var(--ink);font-weight:500}
.tools{display:flex;gap:8px}
.tools button{flex:1;background:none;border:1px solid var(--line);border-radius:10px;padding:7px;cursor:pointer;color:var(--mute);font-size:14px}
main{flex:1;display:flex;flex-direction:column;min-width:0}
header{display:none;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid var(--line)}
header button{background:none;border:0;font-size:22px;cursor:pointer}
#log{flex:1;overflow-y:auto;padding:28px 16px;scroll-behavior:smooth}
.col{max-width:740px;margin:0 auto;display:flex;flex-direction:column;gap:26px}
.row{display:flex;gap:12px;align-items:flex-start}
.row.u{justify-content:flex-start}
.m.u{background:var(--user);color:var(--user-ink);padding:8px 18px;border-radius:18px 18px 4px 18px;max-width:85%;white-space:pre-wrap}
.m.a{flex:1;min-width:0;white-space:pre-wrap;overflow-wrap:anywhere}
.row .orb{margin-top:6px}
.row.in{animation:rise .55s cubic-bezier(.2,.8,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(18px) scale(.98);filter:blur(6px)}}
.w{animation:fade .5s ease-out both}
@keyframes fade{from{opacity:0;filter:blur(5px)}}
.dots{display:inline-flex;gap:5px;padding-top:12px}
.dots b{width:7px;height:7px;border-radius:50%;background:var(--mute);animation:dot 1s ease-in-out infinite}
.dots b:nth-child(2){animation-delay:.15s}.dots b:nth-child(3){animation-delay:.3s}
@keyframes dot{0%,100%{transform:translateY(0);opacity:.4}50%{transform:translateY(-6px);opacity:1}}
.m code{background:var(--line);padding:1px 6px;border-radius:6px;font-size:.9em}
.code{position:relative;background:var(--code);color:#DDE9E6;border-radius:12px;margin:10px 0;overflow:hidden;white-space:normal}
.code pre{margin:0;padding:16px;overflow-x:auto;font:13.5px/1.7 ui-monospace,Menlo,monospace;white-space:pre;text-align:left}
.cp{position:absolute;top:8px;inset-inline-end:8px;background:rgba(255,255,255,.12);border:0;border-radius:8px;padding:2px 10px;font-size:12px;color:#fff;cursor:pointer}
.empty{margin:14vh auto 0;text-align:center}
.empty>*{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}
.empty .orb{width:64px;height:64px;margin:0 auto 18px;animation:spin 8s linear infinite,rise .8s both}
.empty h1{font-size:30px;font-weight:600;margin:0;animation-delay:.12s}
.empty p{color:var(--mute);margin:6px 0 0;animation-delay:.24s}
.sugg{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px;animation-delay:.36s}
.sugg button{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:7px 16px;cursor:pointer;font-size:14px;transition:transform .2s,border-color .2s}
.sugg button:hover{transform:translateY(-3px);border-color:var(--accent)}
form{padding:10px 16px 16px}
.box{max-width:740px;margin:0 auto;display:flex;gap:8px;align-items:flex-end;background:var(--card);backdrop-filter:blur(14px);border:1px solid var(--line);border-radius:20px;padding:8px 8px 8px 12px;box-shadow:0 8px 30px rgba(0,0,0,.06);transition:box-shadow .3s,border-color .3s}
.box:focus-within{border-color:var(--accent);box-shadow:0 8px 40px rgba(224,160,32,.22)}
textarea{flex:1;border:0;background:none;resize:none;outline:0;max-height:170px;line-height:1.7;padding:7px 8px}
.send{background:var(--user);color:var(--user-ink);border:0;border-radius:14px;width:42px;height:42px;cursor:pointer;font-size:18px;transition:transform .15s,opacity .2s}
.send:active{transform:scale(.9)}
.send:disabled{opacity:.35}
.note{max-width:740px;margin:6px auto 0;text-align:center;color:var(--mute);font-size:12px}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.think{margin:0 0 10px;border-inline-start:2px solid var(--accent);background:rgba(224,160,32,.07);border-radius:4px 10px 10px 4px;overflow:hidden}
.think>summary{list-style:none;cursor:pointer;padding:7px 12px;font-size:13.5px;color:var(--mute);white-space:normal}
.think>summary::-webkit-details-marker{display:none}
.think>summary::before{content:"▸";display:inline-block;margin-inline-end:6px}
.think[open]>summary::before{content:"▾"}
.tb{padding:8px 14px 10px;font-size:14px;color:var(--mute);max-height:300px;overflow:auto;border-top:1px solid var(--line)}
@media(max-width:760px){
aside{position:fixed;inset-block:0;inset-inline-start:0;z-index:5;transform:translateX(100%);padding-top:calc(16px + env(safe-area-inset-top,0px))}
aside.open{transform:none}header{display:flex}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<div class="bg"><i></i><i></i></div>
<div class="app">
<aside id="side">
<div class="brand"><span class="orb"></span>المساعد الذكي</div>
<button class="new" id="new">محادثة جديدة</button>
<div class="list" id="list"></div>
<div class="tools"><button id="theme">الوضع</button><button id="clear">مسح الكل</button></div>
</aside>
<main>
<header><button id="menu" aria-label="القائمة">☰</button><strong id="ttl">محادثة جديدة</strong></header>
<div id="log"><div class="col" id="col"></div></div>
<form id="f">
<div class="box"><textarea id="t" rows="1" placeholder="اكتب رسالتك..." aria-label="الرسالة"></textarea><button class="send" id="s" type="submit" aria-label="إرسال">↑</button></div>
<p class="note">Enter للإرسال، Shift+Enter لسطر جديد</p>
</form>
</main>
</div>
<script>
const API="/api/chat";
const $=id=>document.getElementById(id), log=$("log");
let chats=[],cur=null,busy=false,ac=null,stick=true;
try{chats=JSON.parse(localStorage.getItem("chats")||"[]")}catch(e){}
const save=()=>{try{localStorage.setItem("chats",JSON.stringify(chats))}catch(e){}};
const get=()=>chats.find(c=>c.id===cur);
const esc=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;");
function md(t){return t.split("```").map((p,i)=>i%2?'<div class="code"><button class="cp" type="button">نسخ</button><pre dir="ltr">'+esc(p.replace(/^[\w+-]*\n/,""))+'</pre></div>':esc(p).replace(/`([^`\n]+)`/g,"<code>$1</code>").replace(/\*\*([^*\n]+)\*\*/g,"<b>$1</b>")).join("")}
log.addEventListener("scroll",()=>{stick=log.scrollHeight-log.scrollTop-log.clientHeight<80});
const follow=()=>{if(stick){log.style.scrollBehavior="auto";log.scrollTop=log.scrollHeight}};
document.addEventListener("click",e=>{if(e.target.classList.contains("cp")){try{navigator.clipboard.writeText(e.target.nextSibling.textContent);e.target.textContent="تم النسخ";setTimeout(()=>e.target.textContent="نسخ",1500)}catch(x){}}});

function row(m,anim){
  const r=document.createElement("div");r.className="row "+(m.r==="user"?"u":"")+(anim?" in":"");
  const d=document.createElement("div");d.className="m "+(m.r==="user"?"u":"a");
  if(m.r==="user"){d.textContent=m.t}
  else{
    r.innerHTML='<span class="orb"></span>';
    const th=document.createElement("details");th.className="think";th.open=true;
    th.innerHTML='<summary>التفكير</summary><div class="tb"></div>';
    const an=document.createElement("div");an.className="ans";
    an.innerHTML=m.t?md(m.t):'<span class="dots"><b></b><b></b><b></b></span>';
    d.append(th,an);
    m.th=th;m.tb=th.querySelector(".tb");m.ans=an;
    if(m.think){th.querySelector(".tb").textContent=m.think;th.open=false}else{th.hidden=true}
  }
  r.append(d);m.row=r;m.el=d;return r}

function render(animFrom=-1){
  $("list").innerHTML="";
  chats.forEach(c=>{const b=document.createElement("button");b.className="item"+(c.id===cur?" on":"");b.textContent=c.title;b.onclick=()=>{if(busy)return;cur=c.id;$("side").classList.remove("open");render()};$("list").append(b)});
  const c=get(),col=$("col");col.innerHTML="";$("ttl").textContent=c?c.title:"محادثة جديدة";
  if(!c||!c.msgs.length){
    col.innerHTML='<div class="empty"><span class="orb"></span><h1>كيف أقدر أساعدك اليوم؟</h1><p>اسألني أي شي، أو اختار اقتراح.</p><div class="sugg"></div></div>';
    ["لخّص لي نص طويل","اشرح لي فكرة بشكل بسيط","ساعدني أكتب رسالة رسمية","اكتب لي كود بسيط"].forEach(s=>{const b=document.createElement("button");b.type="button";b.textContent=s;b.onclick=()=>{$("t").value=s;send()};col.querySelector(".sugg").append(b)});return}
  c.msgs.forEach((m,i)=>col.append(row(m,animFrom>=0&&i>=animFrom)));
  stick=true;follow()}

async function send(){
  const v=$("t").value.trim();if(!v)return;
  if(busy){stopGen();return}
  const c=get()||(()=>{const n={id:Date.now()+"",title:"محادثة جديدة",msgs:[]};chats.unshift(n);cur=n.id;return n})();
  if(!c.msgs.length)c.title=v.slice(0,40);
  const a={r:"assistant",t:"",think:null};
  c.msgs.push({r:"user",t:v},a);
  $("t").value="";$("t").style.height="auto";
  const start=c.msgs.length-2;render(start);
  busy=true;$("s").textContent="■";a.row.querySelector(".orb").classList.add("fast");
  ac=new AbortController();
  const q=[];let head=0,ended=false,first=true,gotAns=false,partial="",errTxt="";
  const feed=async()=>{
    const history=c.msgs.slice(0,-1).map(m=>({role:m.r,content:m.t}));
    for(let k=0;k<3;k++){
      let r=null;
      try{
        r=await fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages:history}),signal:ac.signal});
      }catch(e){
        if(e.name==="AbortError"){ended=true;return}
        await new Promise(z=>setTimeout(z,1200));continue;
      }
      if(r.ok&&r.body){
        const rd=r.body.getReader(),dec=new TextDecoder();
        for(;;){
          const{done,value}=await rd.read();if(done)break;
          partial+=dec.decode(value,{stream:true});
          let i;
          while((i=partial.indexOf("\n"))>=0){
            const line=partial.slice(0,i);partial=partial.slice(i+1);
            if(!line.trim())continue;
            let o;try{o=JSON.parse(line)}catch(x){continue}
            if(o.t==="r"||o.t==="x"){
              if(o.t==="x")gotAns=true;
              const kk=o.t==="r"?0:1;
              for(const ch of o.d)q.push([kk,ch]);
            }
          }
        }
        ended=true;return;
      }
      errTxt=await r.text().catch(()=>"");
      await new Promise(z=>setTimeout(z,1200));
    }
    for(const ch of ("تعذر الاتصال: "+errTxt.slice(0,150)).split(/(?<= )/)){if(ac.signal.aborted)return;for(const cc of ch)q.push([1,cc])}
    ended=true;
  };
  feed();
  await new Promise(res=>{
    const pump=()=>{
      if(ac.signal.aborted){res();return}
      if(head<q.length){
        const k=q[head][0];
        const max=Math.max(2,Math.ceil((q.length-head)/12));
        let s="";
        while(head<q.length&&q[head][0]===k&&s.length<max)s+=q[head++][1];
        if(s){
          if(first){a.ans.innerHTML="";first=false}
          const el=document.createElement("span");el.className="w";el.textContent=s;
          if(k===0){if(a.think===null)a.think="";a.th.hidden=false;a.th.open=true;a.tb.append(el);a.think+=s}
          else{a.ans.append(el);a.t+=s}
          follow();
        }
      }
      if(head<q.length||!ended)requestAnimationFrame(pump);else res()};
    requestAnimationFrame(pump)});
  if(!gotAns&&a.think){
    const nodes=[...a.tb.childNodes];
    a.ans.innerHTML="";nodes.forEach(n=>a.ans.append(n));
    a.t=a.think;a.think=null;a.th.hidden=true;a.tb.innerHTML="";
  }
  a.ans.innerHTML=a.t?md(a.t):"";
  if(a.think!==null){a.tb.innerHTML=md(a.think);a.th.open=false;if(!a.think.trim())a.th.hidden=true}
  a.row.querySelector(".orb").classList.remove("fast");
  if(!a.t&&a.think===null)a.row.remove();
  busy=false;$("s").textContent="↑";save();follow();
}
function stopGen(){if(ac)ac.abort()}
$("f").onsubmit=e=>{e.preventDefault();busy&&!$("t").value.trim()?stopGen():send()};
$("t").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();if(!busy)send()}});
$("t").addEventListener("input",e=>{e.target.style.height="auto";e.target.style.height=e.target.scrollHeight+"px"});
$("new").onclick=()=>{if(busy)return;cur=null;$("side").classList.remove("open");render()};
$("menu").onclick=()=>$("side").classList.toggle("open");
$("clear").onclick=()=>{if(busy)return;chats=[];cur=null;save();render()};
$("theme").onclick=()=>{const r=document.documentElement,d=r.dataset.theme==="dark"||(!r.dataset.theme&&matchMedia("(prefers-color-scheme:dark)").matches);r.dataset.theme=d?"light":"dark"};
cur=chats[0]?chats[0].id:null;render();
</script>
</body>
</html>
"""


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", HTML)
        elif self.path == "/api/status":
            self._send(200, "application/json", json.dumps(
                {"messages": STATE["n"], "warp_ip": STATE["ip"]}, ensure_ascii=False))
        else:
            self._send(404, "text/plain", "no")

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, "text/plain", "no")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            msgs = json.loads(self.rfile.read(n)).get("messages") or []
            if not msgs:
                raise ValueError("no messages")
        except Exception as e:
            self._send(400, "application/json", json.dumps({"error": str(e)}))
            return

        with LOCK:
            STATE["n"] += 1
        payload = {"input": {"messages": [
            _msg(m.get("role", "user"), str(m.get("content", ""))) for m in msgs]}}

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()

        def emit(kind, text):
            b = (json.dumps({"t": kind, "d": text}, ensure_ascii=False) + "\n").encode()
            self.wfile.write(b"%X\r\n" % len(b) + b + b"\r\n")
            self.wfile.flush()

        emitted = False
        for attempt in range(MAX_TRIES):
            if USE_WARP and attempt < WARP_TRIES:
                if STATE["ip"] == "?" or attempt > 0:
                    if warp_new() is None and STATE["ip"] == "?":
                        continue
                px, src, label = WARP_SOCKS, None, "warp:" + STATE["ip"]
            else:
                src = next_v6()
                px, label = None, str(src)

            tok = mint(px=px, src=src)
            if not tok:
                print("[retry] %s (توكن)" % label)
                time.sleep(0.8)
                continue

            conn = None
            try:
                conn, resp = call(CHAT, payload, px=px, src=src, timeout=90, tok=tok)
            except Exception as e:
                print("[retry] %s (%s)" % (label, e))
                time.sleep(0.8)
                continue
            if resp.status != 200:
                print("[retry] %s (HTTP %s)" % (label, resp.status))
                try:
                    conn.close()
                except Exception:
                    pass
                time.sleep(0.8)
                continue

            print("[ok] %s" % label)
            ev, kinds = "", {}
            try:
                while True:
                    raw = resp.readline()
                    if not raw:
                        break
                    line = raw.decode("utf-8", "replace").rstrip("\r\n")
                    if line.startswith("event:"):
                        ev = line[6:].strip()
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except Exception:
                        continue
                    typ = obj.get("type") or ev
                    if typ.endswith("output_item.added") or typ.endswith("output_item.done"):
                        it = obj.get("item") or {}
                        idx = obj.get("output_index", it.get("output_index"))
                        if idx is not None and it.get("type"):
                            kinds[idx] = it["type"]
                    if not typ.endswith(".delta"):
                        continue
                    d = obj.get("delta")
                    if not isinstance(d, str) or not d:
                        continue
                    ty = kinds.get(obj.get("output_index"), "")
                    emit("r" if ("reasoning" in typ or ty == "reasoning") else "x", d)
                    emitted = True
            except Exception as e:
                print("[stream] %s" % e)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            if emitted:
                break

        if not emitted:
            emit("x", "تعذر الاتصال، جرّب مرة ثانية.")
        try:
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except Exception:
            pass


if __name__ == "__main__":
    print("http://0.0.0.0:%d" % PORT)
    STATE["ip"] = warp_ip()
    print("warp ip: %s" % STATE["ip"])
    if STATE["ip"] == "?":
        warp_sh("connect")
        time.sleep(4)
        STATE["ip"] = warp_ip()
        print("warp ip بعد المحاولة: %s" % STATE["ip"])
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()