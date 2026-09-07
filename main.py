#!/usr/bin/env python3
"""
Instagram DM Viewer — HTML Generator
Converts your Instagram messages/inbox export into a pixel-accurate
Instagram-style DM viewer (single self-contained HTML file).

Folder structure expected:
  messages/
  └── inbox/
      ├── username_123456/
      │   ├── message_1.json
      │   ├── message_2.json   (if chat has multiple pages)
      │   └── photos/
      └── ...

Usage:
    python dm_viewer.py
    python dm_viewer.py --inbox messages/inbox --me YourUsername --output dms.html
"""

import json, os, sys, argparse, base64, glob, re
from datetime import datetime
from pathlib import Path


# ─── helpers ──────────────────────────────────────────────────────────────────

def fix(text):
    if not text: return text
    try: return text.encode('latin-1').decode('utf-8')
    except: return text

def fmt_ts(ts):
    if not ts: return ""
    dt = datetime.fromtimestamp(ts / 1000)
    now = datetime.now()
    if dt.date() == now.date(): return dt.strftime("Today %I:%M %p")
    if (now - dt).days < 7:    return dt.strftime("%a %I:%M %p")
    if dt.year == now.year:    return dt.strftime("%b %d, %I:%M %p")
    return dt.strftime("%b %d %Y, %I:%M %p")

def fmt_ts_short(ts):
    if not ts: return ""
    dt = datetime.fromtimestamp(ts / 1000)
    now = datetime.now()
    if dt.date() == now.date(): return dt.strftime("%I:%M %p")
    if dt.year == now.year:    return dt.strftime("%b %d")
    return dt.strftime("%b %d %Y")

def hue(s):
    h = 0
    for c in s: h = (h * 31 + ord(c)) % 360
    return h

def b64img(path):
    if not path or not os.path.isfile(path): return None
    ext = Path(path).suffix.lower().lstrip('.')
    mime = {'jpg':'jpeg','jpeg':'jpeg','png':'png','gif':'gif','webp':'webp'}.get(ext,'jpeg')
    try:
        with open(path,'rb') as f: data = base64.b64encode(f.read()).decode()
        return f"data:image/{mime};base64,{data}"
    except: return None

def b64file(path, mime):
    if not path or not os.path.isfile(path): return None
    try:
        with open(path,'rb') as f: data = base64.b64encode(f.read()).decode()
        return f"data:{mime};base64,{data}"
    except: return None

def find_file(folder, uri):
    if not uri: return None
    cands = [uri,
             os.path.normpath(os.path.join(folder, '..', '..', '..', uri)),
             os.path.join(folder, os.path.basename(uri)),
             os.path.join(folder, 'photos', os.path.basename(uri))]
    for c in cands:
        if os.path.isfile(c): return c
    return None


# ─── load conversation ────────────────────────────────────────────────────────

def load_conv(folder):
    msgs, participants, title = [], [], ""
    for jf in sorted(glob.glob(os.path.join(folder, 'message_*.json'))):
        try:
            with open(jf, 'r', encoding='utf-8') as f: data = json.load(f)
            if not title:        title        = fix(data.get('title',''))
            if not participants: participants = [fix(p.get('name','')) for p in data.get('participants',[])]
            msgs.extend(data.get('messages',[]))
        except Exception as e:
            print(f"  ⚠  {jf}: {e}")
    msgs.sort(key=lambda m: m.get('timestamp_ms',0))
    return title, participants, msgs


# ─── build one bubble ─────────────────────────────────────────────────────────

def bubble(msg, is_me, show_sender, folder):
    ts       = msg.get('timestamp_ms', 0)
    sender   = fix(msg.get('sender_name',''))
    content  = fix(msg.get('content',''))
    mtype    = msg.get('type','Generic')
    side     = 'right' if is_me else 'left'
    inner    = ''

    # text
    if content and mtype != 'Call':
        esc = content.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        esc = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', esc)
        inner += f'<div class="mt">{esc}</div>'

    # photos
    for p in msg.get('photos',[]):
        path = find_file(folder, p.get('uri',''))
        src  = b64img(path)
        if src: inner += f'<img class="mi" src="{src}" alt="photo" loading="lazy" onclick="lb(this)">'
        else:   inner += f'<div class="mm">📷 {os.path.basename(p.get("uri","photo"))}</div>'

    # videos
    for v in msg.get('videos',[]):
        path = find_file(folder, v.get('uri',''))
        src  = b64file(path,'video/mp4') if path else None
        if src: inner += f'<video class="mv" controls><source src="{src}"></video>'
        else:   inner += '<div class="mm">🎥 Video</div>'

    # audio
    for a in msg.get('audio_files',[]):
        path = find_file(folder, a.get('uri',''))
        src  = b64file(path,'audio/aac') if path else None
        if src: inner += f'<audio class="ma" controls><source src="{src}"></audio>'
        else:   inner += '<div class="mm">🎵 Audio</div>'

    # sticker
    st = msg.get('sticker')
    if st:
        path = find_file(folder, st.get('uri',''))
        src  = b64img(path)
        if src: inner += f'<img class="ms" src="{src}" alt="sticker">'

    # share / link
    share = msg.get('share')
    if share:
        link = share.get('link','')
        stxt = fix(share.get('share_text',''))
        if link: inner += f'<a class="msh" href="{link}" target="_blank" rel="noopener">🔗 {stxt or link}</a>'

    # call
    if mtype == 'Call':
        dur = msg.get('call_duration',0)
        ds  = f' · {dur//60}m {dur%60}s' if dur else ''
        inner += f'<div class="mc">📞 Video call{ds}</div>'

    if not inner:
        inner = f'<div class="mt mu">{content or "[message]"}</div>'

    reacts = msg.get('reactions',[])
    rhtml  = f'<div class="mr">{"".join(fix(r.get("reaction","")) for r in reacts)}</div>' if reacts else ''
    shtml  = f'<div class="msn">{sender}</div>' if show_sender and not is_me else ''
    day    = datetime.fromtimestamp(ts/1000).strftime('%A, %b %d %Y') if ts else ''

    return day, f'''
<div class="row {side}">
  <div class="bw">
    {shtml}
    <div class="b {side}">{inner}</div>
    {rhtml}
    <div class="bt">{fmt_ts(ts)}</div>
  </div>
</div>'''


# ─── HTML template ────────────────────────────────────────────────────────────

TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Instagram DMs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;font-family:'Inter',sans-serif;font-size:14px;background:#000;color:#fff;-webkit-font-smoothing:antialiased}
.app{display:flex;height:100vh;max-width:1100px;margin:0 auto;border-left:1px solid #262626;border-right:1px solid #262626}
/* sidebar */
.sb{width:350px;flex-shrink:0;border-right:1px solid #262626;display:flex;flex-direction:column;background:#000}
.sbh{padding:20px 20px 12px;border-bottom:1px solid #262626}
.sbt{font-size:17px;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.sbt svg{width:20px;height:20px}
.srch{background:#262626;border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;color:#a8a8a8;font-size:13px}
.srch svg{width:14px;height:14px;flex-shrink:0}
.clist{flex:1;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#363636 transparent}
.clist::-webkit-scrollbar{width:4px}.clist::-webkit-scrollbar-thumb{background:#363636;border-radius:4px}
/* conv item */
.ci{display:flex;align-items:center;gap:12px;padding:10px 20px;cursor:pointer;transition:background .15s;user-select:none}
.ci:hover,.ci.active{background:#121212}
.av{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700;color:#fff;flex-shrink:0}
.cinfo{flex:1;min-width:0}
.cn{font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px}
.cp{font-size:13px;color:#737373;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cmeta{flex-shrink:0;text-align:right}
.cts{font-size:11px;color:#737373}
/* chat */
.chat{flex:1;display:flex;flex-direction:column;min-width:0}
.chdr{padding:14px 20px;border-bottom:1px solid #262626;display:flex;align-items:center;gap:12px;background:#000;flex-shrink:0}
.chdr .av{width:38px;height:38px;font-size:13px}
.chdrn{font-size:15px;font-weight:700}
.chdrs{font-size:12px;color:#737373;margin-top:1px}
.chdra{margin-left:auto;display:flex;gap:18px;color:#737373}
.chdra svg{width:22px;height:22px;cursor:pointer;transition:color .15s}.chdra svg:hover{color:#fff}
.msgs{flex:1;overflow-y:auto;padding:20px 20px 8px;display:flex;flex-direction:column;gap:2px;scrollbar-width:thin;scrollbar-color:#363636 transparent}
.msgs::-webkit-scrollbar{width:4px}.msgs::-webkit-scrollbar-thumb{background:#363636;border-radius:4px}
/* day sep */
.ds{text-align:center;margin:14px 0 8px;color:#737373;font-size:11px;display:flex;align-items:center;gap:10px}
.ds::before,.ds::after{content:'';flex:1;height:1px;background:#262626}
/* messages */
.row{display:flex;margin:1px 0}.row.right{justify-content:flex-end}.row.left{justify-content:flex-start}
.bw{max-width:68%;display:flex;flex-direction:column}
.row.right .bw{align-items:flex-end}.row.left .bw{align-items:flex-start}
.msn{font-size:11px;color:#737373;margin-bottom:2px;margin-left:12px}
.b{border-radius:20px;padding:9px 14px;max-width:100%;word-break:break-word;line-height:1.5;font-size:14px}
.b.right{background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);border-bottom-right-radius:4px;color:#fff}
.b.left{background:#262626;border-bottom-left-radius:4px;color:#fff}
.bt{font-size:10px;color:#555;margin-top:2px;padding:0 4px}
.mr{font-size:16px;margin-top:2px;padding:0 6px}
.mt a{color:#a8d8ff;word-break:break-all}
.mi{max-width:220px;max-height:280px;border-radius:14px;object-fit:cover;display:block;cursor:zoom-in;margin:2px 0}
.mv{max-width:220px;border-radius:14px;display:block;margin:2px 0}
.ma{max-width:200px;margin:2px 0;filter:invert(1) hue-rotate(180deg)}
.ms{width:100px;height:100px;object-fit:contain;background:transparent;display:block}
.msh{display:block;padding:10px 14px;background:rgba(255,255,255,.08);border-radius:12px;color:#a8d8ff;font-size:13px;text-decoration:none;border:1px solid rgba(255,255,255,.1);margin:2px 0}
.msh:hover{background:rgba(255,255,255,.12)}
.mc{font-size:13px;color:#a8a8a8}
.mm{font-size:12px;color:#555;padding:6px 10px;background:#1a1a1a;border-radius:8px;border:1px dashed #333;margin:2px 0}
.mu{color:#737373;font-style:italic;font-size:13px}
/* input */
.ibar{padding:12px 16px;border-top:1px solid #262626;display:flex;align-items:center;gap:12px;background:#000;flex-shrink:0}
.ibar svg{width:24px;height:24px;color:#737373;flex-shrink:0;cursor:pointer}.ibar svg:hover{color:#fff}
.ifk{flex:1;background:#262626;border-radius:22px;padding:10px 16px;font-size:14px;color:#737373}
/* lightbox */
#lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.95);z-index:9999;align-items:center;justify-content:center;cursor:zoom-out}
#lb.open{display:flex}
#lb img{max-width:90vw;max-height:90vh;border-radius:8px;object-fit:contain}
/* empty */
.noconv{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;color:#737373}
.noconv svg{width:64px;height:64px;stroke:#363636}
/* responsive */
@media(max-width:768px){
  .sb{width:72px}.cn,.cp,.cts,.cmeta,.sbt span,.chdrs,.srch span{display:none}
  .ci{padding:10px;justify-content:center}.sbh{padding:12px 8px}
}
</style>
</head>
<body>
<div class="app">
  <div class="sb">
    <div class="sbh">
      <div class="sbt">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg><span>Messages</span>
      </div>
      <div class="srch">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg><span>Search</span>
      </div>
    </div>
    <div class="clist" id="clist">%%CLIST%%</div>
  </div>
  <div class="chat" id="chat">
    <div class="noconv" id="noconv">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <p>Select a conversation</p>
    </div>
    <div id="cv" style="display:none;flex-direction:column;height:100%">
      <div class="chdr" id="chdr"></div>
      <div class="msgs" id="msgs"></div>
      <div class="ibar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
        <div class="ifk">Message…</div>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
      </div>
    </div>
  </div>
</div>
<div id="lb" onclick="this.classList.remove('open')"><img id="lbi" src="" alt=""></div>
<script>
const C=%%CONVS%%;
function hue(s){let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))%360;return h}
function grad(u){const h=hue(u);return`linear-gradient(135deg,hsl(${h},65%,48%),hsl(${(h+50)%360},68%,58%))`}
function ini(n){return n.split(' ').slice(0,2).map(w=>w[0]?.toUpperCase()||'').join('')||'?'}
function lb(el){document.getElementById('lbi').src=el.src;document.getElementById('lb').classList.add('open')}
function sw(i){
  document.querySelectorAll('.ci').forEach(el=>el.classList.toggle('active',+el.dataset.i===i));
  const c=C[i];if(!c)return;
  document.getElementById('noconv').style.display='none';
  const cv=document.getElementById('cv');cv.style.display='flex';
  document.getElementById('chdr').innerHTML=`
    <div class="av" style="background:${grad(c.t)}">${ini(c.t)}</div>
    <div><div class="chdrn">${c.t}</div><div class="chdrs">${c.p.join(', ')}</div></div>
    <div class="chdra">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13 19.79 19.79 0 0 1 1.61 4.4 2 2 0 0 1 3.6 2.22h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 9.91a16 16 0 0 0 6.18 6.18l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
    </div>`;
  const area=document.getElementById('msgs');
  area.innerHTML=c.h;
  area.scrollTop=area.scrollHeight;
  area.querySelectorAll('.mi').forEach(img=>img.onclick=()=>lb(img));
}
if(C.length)sw(0);
</script>
</body>
</html>"""


# ─── builder ──────────────────────────────────────────────────────────────────

def build(inbox_path, me_name, output_path):
    if not os.path.isdir(inbox_path):
        print(f"\033[1;31m  ✗ Inbox not found: {inbox_path}\033[0m"); sys.exit(1)

    folders = sorted([
        os.path.join(inbox_path, d) for d in os.listdir(inbox_path)
        if os.path.isdir(os.path.join(inbox_path, d))
    ])
    if not folders:
        print(f"\033[1;31m  ✗ No conversations found\033[0m"); sys.exit(1)

    print(f"\n  Found {len(folders)} conversation(s).\n")

    clist_html = []
    convs = []

    for i, folder in enumerate(folders):
        title, participants, msgs = load_conv(folder)
        if not msgs: continue

        is_group = len(participants) > 2
        last = msgs[-1]
        lc = fix(last.get('content',''))
        if not lc:
            if last.get('photos'):      lc = '📷 Photo'
            elif last.get('videos'):    lc = '🎥 Video'
            elif last.get('audio_files'): lc = '🎵 Audio'
            elif last.get('share'):     lc = '🔗 Link'
            else:                       lc = '…'
        lt = last.get('timestamp_ms',0)
        prev = lc[:38]+'…' if len(lc)>38 else lc

        h = hue(title)
        ini_str = ''.join(w[0].upper() for w in title.split()[:2]) or '?'
        ts_str  = fmt_ts_short(lt)
        act = ' active' if i == 0 else ''
        clist_html.append(
            f'<div class="ci{act}" data-i="{i}" onclick="sw({i})">'
            f'<div class="av" style="background:linear-gradient(135deg,hsl({h},65%,48%),hsl({(h+50)%360},68%,58%))">{ini_str}</div>'
            f'<div class="cinfo"><div class="cn">{title}</div><div class="cp">{prev}</div></div>'
            f'<div class="cmeta"><div class="cts">{ts_str}</div></div>'
            f'</div>'
        )

        # Build messages
        bubbles = []
        last_day = None
        prev_sender = None
        for msg in msgs:
            ts = msg.get('timestamp_ms',0)
            sender = fix(msg.get('sender_name',''))
            is_me  = (sender.lower() == me_name.lower()) if me_name else False
            if ts:
                day = datetime.fromtimestamp(ts/1000).strftime('%A, %b %d %Y')
                if day != last_day:
                    bubbles.append(f'<div class="ds">{day}</div>')
                    last_day = day
            show_sender = is_group and sender != prev_sender and not is_me
            _, bhtml = bubble(msg, is_me, show_sender, folder)
            bubbles.append(bhtml)
            prev_sender = sender

        msgs_html = '\n'.join(bubbles)
        disp_p = [p for p in participants if p.lower() != me_name.lower()] if me_name else participants

        convs.append({'t': title, 'p': disp_p, 'h': msgs_html})
        print(f"  [{i+1}/{len(folders)}] {title} — {len(msgs)} messages")

    final = TMPL.replace('%%CLIST%%', '\n'.join(clist_html))
    final = final.replace('%%CONVS%%', json.dumps(convs, ensure_ascii=False))

    with open(output_path, 'w', encoding='utf-8') as f: f.write(final)
    size = os.path.getsize(output_path) / (1024*1024)
    print(f"\n  ✅  Saved → \033[1;36m{output_path}\033[0m  ({size:.1f} MB)")
    print(f"  Open in any browser — fully offline.\n")


# ─── entry ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Convert Instagram DM export to HTML viewer.')
    p.add_argument('--inbox',  default=os.path.join('messages','inbox'),
                   help='Path to inbox folder (default: messages/inbox)')
    p.add_argument('--me',     default='',
                   help='Your username — your messages appear on the right')
    p.add_argument('--output', default='instagram_dms.html',
                   help='Output HTML file (default: instagram_dms.html)')
    args = p.parse_args()

    inbox = args.inbox
    for c in [inbox, 'inbox', os.path.join('messages','inbox')]:
        if os.path.isdir(c): inbox = c; break

    print(f"\n  📁  Inbox  : {inbox}")
    print(f"  👤  Me     : {args.me or '(not set — all messages appear on left)'}")
    print(f"  💾  Output : {args.output}")
    build(inbox, args.me, args.output)

if __name__ == '__main__':
    main()
