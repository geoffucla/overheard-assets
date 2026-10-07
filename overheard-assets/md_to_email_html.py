import re,html,sys
BANNER=sys.argv[4] if len(sys.argv)>4 else ''
import os
DESC=os.environ.get('DESC','A rather dry take on Bay Area tech news')
md=open(sys.argv[1]).read().split('\n'); date=sys.argv[2]
import re as _re
SITE='https://bay.overheardnews.com'
_m=_re.search(r'(\d{4}-\d{2}-\d{2})',os.path.basename(sys.argv[1]))
WEB=f'{SITE}/editions/{_m.group(1)}/' if _m else SITE+'/'
ARCH=SITE+'/archive/'
import datetime as _dt
YEAR=(_m.group(1)[:4] if _m else str(_dt.date.today().year))
INK='#1F2933';AC='#B3261E';MU='#6B7280'
def inl(t):
    t=html.escape(t,quote=False)
    t=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',t)
    t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2" style="color:#1D4ED8">\1</a>',t)
    return t
o=[]; sec=''; inol=False; inul=False
def close():
    global inol,inul
    if inol:o.append('</ol>');inol=False
    if inul:o.append('</ul>');inul=False
for l in md:
    l=l.rstrip()
    if not l or l.startswith('# ') or l.startswith(('Curated by','Designed for human consumption')):continue
    if l.startswith('## '):
        close();sec=l[3:]
        o.append(f'<h2 style="font:bold 12px Arial,sans-serif;letter-spacing:2px;color:{AC};border-bottom:2px solid {AC};padding-bottom:4px;margin:28px 0 12px">{html.escape(sec)}</h2>');continue
    if l.startswith('> '):
        close()
        lab,_,rest=l[2:].partition(':')
        o.append(f'<p style="font:12px/1.5 Arial,sans-serif;color:{MU};margin:-8px 0 16px"><em>{html.escape(lab.strip())}:</em> {inl(rest.strip())}</p>');continue
    if l.startswith('~ '):
        close()
        o.append(f'<p style="font:italic 13px/1.4 Arial,sans-serif;color:{MU};margin:-6px 0 12px">{inl(l[2:])}</p>');continue
    m=re.match(r'^(\d)\.\s(.*)',l)
    if m:
        if not inol:o.append('<ol style="margin:0 0 0 22px;padding:0">');inol=True
        o.append(f'<li style="margin:0 0 8px">{inl(m.group(2))}</li>');continue
    close()
    if sec=='THE LEAD':
        o.append(f'<p style="background:#F7F3EE;border-left:5px solid {AC};padding:12px 14px;margin:0 0 14px;font-size:17px">{inl(l)}</p>');continue
    v=re.match(r'^\*\*(UP|DOWN):\s?(.*?)\*\*\s?(.*)',l)
    if v:
        up=v.group(1)=='UP'
        fg='#1B5E20' if up else '#B3261E'; bg='#C8E6C9' if up else '#F8D0CC'; arrow='&#9650; UP' if up else '&#9660; DOWN'
        o.append(f'<p style="margin:0 0 14px"><strong style="color:{fg};background-color:{bg};font-family:Arial,sans-serif;font-size:12px;padding:2px 6px;letter-spacing:1px">&nbsp;{arrow}&nbsp;</strong> <strong>{inl(v.group(2))}</strong> {inl(v.group(3))}</p>');continue
    o.append(f'<p style="margin:0 0 14px">{inl(l)}</p>')
close()
banner=(f'<img src="{BANNER}" alt="A data center, the Golden Gate Bridge and a robot in a fleece vest" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0;margin:0 auto 6px">' if BANNER else '')
page=f'''<div style="max-width:640px;margin:0 auto;padding:20px;font:16px/1.5 Georgia,'Times New Roman',serif;color:{INK}">
<p style="text-align:center;font:11px Arial,sans-serif;color:{MU};margin:0 0 10px"><a href="{WEB}" style="color:{MU}">View this on the web</a> &nbsp;|&nbsp; <a href="{ARCH}" style="color:{MU}">Past issues</a></p>
{banner}
<div style="text-align:center;border-top:3px solid {INK};border-bottom:1px solid {INK};padding:10px 0 12px">
<div style="font-family:Georgia,serif;font-weight:bold;font-size:25px;letter-spacing:4px;line-height:1.2"><span style="font-size:36px">O</span>VERHEARD <span style="font-size:36px">I</span>N <span style="font-size:36px">T</span>HE <span style="font-size:36px">B</span>AY</div>
<div style="font:10px Arial,sans-serif;letter-spacing:1px;color:{MU}">{date.upper()}</div>
<div style="font-style:italic;font-size:14px;color:{INK};margin-top:8px">{DESC} <span style="color:{MU}">&nbsp;|&nbsp;</span> <span style="color:{AC}">Designed for human consumption by Geoff Allen</span></div></div>
{''.join(o)}
<p style="text-align:center;font-style:italic;font-size:12px;color:{MU};border-top:1px solid {MU};padding-top:8px;margin-top:24px">Informed, opinionated, occasionally wrong. Verify before repeating at dinner.</p>
<p style="text-align:center;font-style:italic;font-size:11px;line-height:1.4;color:{MU};margin:8px 0 0">Written by Claude, an AI model made by Anthropic. All views expressed are strictly AI generated and are not the views of any human on, in, or around the loop, including the one who designed this for human consumption.</p>
<p style="text-align:center;font:11px Arial,sans-serif;color:{MU};margin-top:10px">&copy; {YEAR} Humans Not Included Media, publisher of Overheard in the Bay. All rights reserved.<br>You are receiving this because you subscribed to Overheard in the Bay. <a href="{{{{{{RESEND_UNSUBSCRIBE_URL}}}}}}" style="color:{MU}">Unsubscribe</a></p></div>'''
open(sys.argv[3],'w').write(page)
