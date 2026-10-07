"""Overheard in the Bay: edition markdown -> email-safe HTML (design v3, banners per column).
Usage: md_to_email_html.py edition.md "DATE LONG" out.html [ignored_banner_url]
Env: BANNER_BASE overrides where banner images are loaded from (default https://bay.overheardnews.com/banners)."""
import re, html, sys, os, math, datetime as _dt
md = open(sys.argv[1]).read().split('\n'); date = sys.argv[2]
DESC = os.environ.get('DESC', 'A rather dry take on Bay Area tech news')
SITE = 'https://bay.overheardnews.com'
BB = os.environ.get('BANNER_BASE', SITE + '/banners')
_m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(sys.argv[1]))
WEB = f'{SITE}/editions/{_m.group(1)}/' if _m else SITE + '/'
ARCH = SITE + '/archive/'
YEAR = _m.group(1)[:4] if _m else str(_dt.date.today().year)
INK = '#1B2430'; PAPER = '#F6F1E7'; MU = '#5C6573'; RED = '#B3261E'
FAM = {'news': ('#24344D', '#E4E9F1'), 'money': ('#1F6B4F', '#E1EFE8'), 'machine': ('#5B3FA0', '#ECE6F6'), 'wit': ('#B34D12', '#F8E8DB')}
COLS = {  # title -> (banner file, family)
 'THE LEAD': ('01_lead', 'news'), 'THE LEDGER': ('02_ledger', 'money'), 'OPEN WEIGHTS': ('03_weights', 'money'),
 'HUMAN, YOUR LOOP IS CALLING': ('04_human', 'machine'), 'THE SCUTTLEBUTT': ('05_scuttle', 'wit'), 'LOCAL DESK': ('06_local', 'news'),
 'CORRECTIONS AND UPDATES': ('07_corr', 'news'), 'AUTOMATIC REPLIES': ('08_auto', 'machine'), 'SYNTHETIC REFLECTIONS': ('09_synth', 'machine'),
 'EMPATHY AS A SERVICE': ('10_empathy', 'machine'), 'YOUR CALL IS IMPORTANT TO US': ('11_call', 'wit'),
 'UNSUITABLE FOR GENERAL RELEASE': ('12_unsuit', 'wit'), 'THREE THINGS TO BRING UP TODAY': ('13_three', 'wit')}
SERIF = "Georgia,'Times New Roman',serif"; SANS = "Arial,Helvetica,sans-serif"

def inl(t, link='#1D4ED8'):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', rf'<a href="\2" style="color:{link}">\1</a>', t)
    return t

def moreline(l, color=MU, link='#1D4ED8'):
    lab, _, rest = l[2:].partition(':')
    return f'<p style="font:12px/1.5 {SANS};color:{color};margin:0 0 16px"><em>{html.escape(lab.strip())}:</em> {inl(rest.strip(), link)}</p>'

def para(l, size=15.5, color=INK, link='#1D4ED8', extra=''):
    return f'<p style="font:{size}px/1.55 {SERIF};color:{color};margin:0 0 14px;{extra}">{inl(l, link)}</p>'

# ---------- parse ----------
secs = []; cur = None
for l in md:
    l = l.rstrip()
    if not l.strip() or l.startswith('# ') or l.startswith(('Curated by', 'Designed for human consumption')): continue
    if l.startswith('## '):
        cur = [l[3:].strip(), []]; secs.append(cur); continue
    if cur is not None: cur[1].append(l)

def amount(line):
    best = None
    for m in re.finditer(r'\$\s?([\d][\d,]*(?:\.\d+)?)\s?(billion|million|thousand|bn|B|M|K)\b', line):
        tail = line[m.end():m.end() + 24].lower()
        mult = {'billion': 1e9, 'bn': 1e9, 'b': 1e9, 'million': 1e6, 'm': 1e6, 'thousand': 1e3, 'k': 1e3}[m.group(2).lower()]
        val = float(m.group(1).replace(',', '')) * mult
        isval = bool(re.match(r'\s*(pre-money|post-money|valuation|valued|market cap)', tail))
        if best is None or (best[1] and not isval): best = (val, isval)
        if not isval: break
    return best[0] if best else None
def money(v):
    if v >= 1e9: s = f'{v/1e9:.2f}'.rstrip('0').rstrip('.'); return f'${s}B'
    if v >= 1e6: s = f'{v/1e6:.1f}'.rstrip('0').rstrip('.'); return f'${s}M'
    return f'${v/1e3:.0f}K'
SCALES = [1e8, 2.5e8, 5e8, 1e9, 2.5e9, 5e9, 1e10, 2.5e10, 5e10, 1e11]

def render_section(title, lines):
    fam = COLS.get(title, ('', 'news'))[1]; c, tint = FAM[fam]
    out = []
    stand = ''
    if lines and lines[0].startswith('~ '):
        stand = f'<p style="font:italic 13px/1.4 {SANS};color:{"#B9ABE0" if title.startswith("HUMAN") else MU};margin:0 0 14px">{inl(lines[0][2:])}</p>'; lines = lines[1:]
    body = [l for l in lines if l.strip()]
    if title == 'THE LEAD':
        for i, l in enumerate(body):
            if l.startswith('> '): out.append(moreline(l)); continue
            t = inl(l)
            first = f'<span style="font:bold 44px/38px {SERIF};color:{c};float:left;padding:4px 8px 0 0">{html.escape(l[0])}</span>'
            body_t = inl(l[1:])
            out.append(f'<p style="font:17px/1.6 {SERIF};color:{INK};margin:0 0 14px">{first}{body_t}</p>')
    elif title == 'THE LEDGER':
        ents = [l for l in body if not l.startswith(('> ', '~ '))]
        amts = [amount(l) for l in ents]
        top = max([a for a in amts if a] + [5e8]); scale = next(s for s in SCALES if s >= top)
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{tint};border-top:3px solid {c};margin:0 0 18px"><tr><td style="padding:8px 14px;border-bottom:1px solid #B9D7C8;font:bold 10px {SANS};letter-spacing:1.5px;color:{c}">WHO</td><td align="right" style="padding:8px 14px;border-bottom:1px solid #B9D7C8;font:bold 10px {SANS};letter-spacing:1.5px;color:{c}">AMOUNT</td></tr>')
        for l, a in zip(ents, amts):
            right = ''
            if a:
                pct = max(4, min(100, round(a / scale * 100)))
                right = (f'<div style="font:bold 28px/1 {SERIF};color:{c}">{money(a)}</div>'
                         f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px"><tr><td width="{pct}%" height="8" bgcolor="{c}" style="font-size:0;line-height:0;height:8px">&nbsp;</td><td height="8" bgcolor="#C6DDD1" style="font-size:0;line-height:0;height:8px">&nbsp;</td></tr></table>'
                         f'<div style="font:10px {SANS};color:#4C7A68;margin-top:3px">of {money(scale)} scale</div>')
            out.append(f'<tr><td valign="middle" style="padding:14px;border-bottom:1px solid #CFE3D8;font:15px/1.45 {SERIF};color:{INK}">{inl(l)}</td><td valign="middle" align="right" width="130" style="padding:14px 14px 14px 0;border-bottom:1px solid #CFE3D8">{right}</td></tr>')
        out.append('</table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    elif title == 'OPEN WEIGHTS':
        cards = []
        for l in body:
            if l.startswith('> '):
                if cards: cards[-1][1] = moreline(l)
                continue
            v = re.match(r'^\*\*(UP|DOWN):\s?(.*?)\*\*\s?(.*)', l)
            if v:
                up = v.group(1) == 'UP'; col = '#1F6B4F' if up else RED; bd = '#D8E3DC' if up else '#EBCFCB'
                tag = f'<span style="font:bold 11px {SANS};letter-spacing:1.5px;color:#fff;background:{col};padding:4px 8px">&nbsp;{"&#9650; UP" if up else "&#9660; DOWN"}&nbsp;</span>'
                cards.append([f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid {bd};border-top:4px solid {col};margin:0 0 14px"><tr><td style="padding:14px 16px">'
                              f'<div style="margin:0 0 8px">{tag}&nbsp; <strong style="font:bold 17px {SERIF};color:{INK}">{inl(v.group(2))}</strong></div>'
                              f'<div style="font:15px/1.5 {SERIF};color:{INK}">{inl(v.group(3))}</div>', ''])
            else:
                out.append(para(l))
        for a, b in cards: out.append(a + (f'<div style="margin-top:8px">{b}</div>' if b else '') + '</td></tr></table>')
    elif title.startswith('THREE THINGS'):
        for l in body:
            m = re.match(r'^(\d)\.\s(.*)', l)
            if m:
                out.append(f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 14px"><tr><td width="46" height="46" align="center" valign="middle" bgcolor="{c}" style="width:46px;height:46px;border-radius:23px;background:{c};color:#fff;font:bold 24px/46px {SERIF};text-align:center">{m.group(1)}</td><td style="padding-left:14px;font:15.5px/1.55 {SERIF};color:{INK}" valign="middle">{inl(m.group(2))}</td></tr></table>')
            elif l.startswith('> '): out.append(moreline(l))
            else: out.append(para(l))
    elif title == 'HUMAN, YOUR LOOP IS CALLING':
        for l in body:
            out.append(moreline(l, '#B9ABE0', '#CFC2F2') if l.startswith('> ') else para(l, 15, '#F1ECFA', '#CFC2F2'))
    elif title == 'THE SCUTTLEBUTT':
        t = [l for l in body if not l.startswith('> ')]
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{tint};border:2px dashed {c};margin:0 0 12px"><tr><td style="padding:16px 18px"><div style="margin:0 0 10px"><span style="font:bold 11px {SANS};letter-spacing:3px;color:{c};border:2px solid {c};padding:3px 8px">UNCONFIRMED</span></div>' + ''.join(f'<div style="font:italic 15.5px/1.55 {SERIF};color:{INK};margin:0 0 10px">{inl(l)}</div>' for l in t) + '</td></tr></table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    elif title == 'CORRECTIONS AND UPDATES':
        t = [l for l in body if not l.startswith('> ')]
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:4px double {c};border-bottom:4px double {c};margin:0 0 16px"><tr><td style="padding:14px 4px"><div style="font:bold 11px {SANS};letter-spacing:2px;color:{c};margin:0 0 6px">FOR THE RECORD</div>' + ''.join(f'<div style="font:15.5px/1.55 {SERIF};color:{INK};margin:0 0 10px">{inl(l)}</div>' for l in t) + '</td></tr></table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    elif title == 'AUTOMATIC REPLIES':
        t = [l for l in body if not l.startswith('> ')]
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #BFB1E3;background:#fff;margin:0 0 16px"><tr><td style="background:{tint};border-bottom:1px solid #BFB1E3;padding:8px 14px;font:11px/1.6 {SANS};color:#4A3487;letter-spacing:.5px"><strong>STATUS</strong>&nbsp; Responding automatically</td></tr><tr><td style="padding:16px 18px">' + ''.join(f'<div style="font:15.5px/1.55 {SERIF};color:{INK};margin:0 0 10px">{inl(l)}</div>' for l in t) + '</td></tr></table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    elif title == 'SYNTHETIC REFLECTIONS':
        out.append(f'<div style="border-top:3px solid {c};padding-top:14px"></div>')
        for l in body: out.append(moreline(l) if l.startswith('> ') else para(l))
    elif title == 'EMPATHY AS A SERVICE':
        t = [l for l in body if not l.startswith('> ')]
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{tint};border:1px solid #CFC2F2;margin:0 0 18px"><tr><td style="padding:20px 26px"><div style="text-align:center;font:14px {SERIF};color:{c};letter-spacing:6px;margin:0 0 10px">&mdash;&nbsp;&#9825;&nbsp;&mdash;</div>' + ''.join(f'<div style="font:italic 16px/1.6 {SERIF};color:{INK};margin:0 0 10px">{inl(l)}</div>' for l in t) + '</td></tr></table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    elif title == 'YOUR CALL IS IMPORTANT TO US':
        for l in body:
            out.append(moreline(l) if l.startswith('> ') else f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 14px"><tr><td width="4" bgcolor="{c}" style="width:4px;background:{c}">&nbsp;</td><td style="padding-left:14px;font:15.5px/1.55 {SERIF};color:{INK}">{inl(l)}</td></tr></table>')
    elif title == 'UNSUITABLE FOR GENERAL RELEASE':
        t = [l for l in body if not l.startswith('> ')]
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {INK};background:#fff;margin:0 0 16px"><tr><td style="padding:16px 18px">' + ''.join(f'<div style="font:15.5px/1.55 {SERIF};color:{INK};margin:0 0 10px">{inl(l)}</div>' for l in t) + '</td></tr></table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    else:  # LOCAL DESK and anything else
        for l in body: out.append(moreline(l) if l.startswith('> ') else para(l))
    return stand + ''.join(out)

def section_html(title, lines):
    info = COLS.get(title)
    fam = info[1] if info else 'news'; c, tint = FAM[fam]
    dark = title == 'HUMAN, YOUR LOOP IS CALLING'
    banner = ''
    if info:
        banner = (f'<tr><td bgcolor="{c}" style="background:{c};font:bold 16px {SANS};color:#fff;letter-spacing:2px">'
                  f'<img src="{BB}/{info[0]}.png" alt="{html.escape(title)}" width="640" style="display:block;width:100%;max-width:640px;height:auto;border:0;color:#fff;font:bold 16px {SANS};text-align:center"></td></tr>')
    else:
        banner = f'<tr><td style="padding:24px 28px 0;font:bold 12px {SANS};letter-spacing:2px;color:{RED}">{html.escape(title)}</td></tr>'
    bg = '#2A1F4A' if dark else PAPER
    return banner + f'<tr><td bgcolor="{bg}" style="background:{bg};padding:20px 28px 8px">{render_section(title, lines)}</td></tr>'

rows = ''.join(section_html(t, ls) for t, ls in secs)
page = f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#E9E3D6" style="background:#E9E3D6"><tr><td align="center" style="padding:16px 8px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" bgcolor="{PAPER}" style="width:640px;max-width:100%;background:{PAPER}">
<tr><td align="center" style="padding:10px 0 10px;font:11px {SANS};color:{MU}"><a href="{WEB}" style="color:{MU}">View this on the web</a> &nbsp;|&nbsp; <a href="{ARCH}" style="color:{MU}">Past issues</a></td></tr>
<tr><td bgcolor="#0E131B" style="background:#0E131B"><img src="{BB}/00_masthead.png" alt="OVERHEARD IN THE BAY, {html.escape(DESC)}" width="640" style="display:block;width:100%;max-width:640px;height:auto;border:0;color:#fff;font:bold 22px {SERIF};text-align:center"></td></tr>
<tr><td align="center" style="padding:14px 24px;border-bottom:3px solid {INK};background:{PAPER}"><span style="font:bold 11px {SANS};letter-spacing:3px;color:{MU}">{html.escape(date.upper())}</span><span style="font:italic 13px {SERIF};color:{RED}">&nbsp;&nbsp;|&nbsp;&nbsp;Designed for human consumption by Geoff Allen</span></td></tr>
{rows}
<tr><td bgcolor="{INK}" align="center" style="background:{INK};color:#C9CED6;padding:18px 32px 22px;font:11px/1.55 {SANS}"><div style="font:italic 12px {SERIF};color:{PAPER};margin-bottom:8px">Informed, opinionated, occasionally wrong. Verify before repeating at dinner.</div>Written by Claude, an AI model made by Anthropic. All views expressed are strictly AI generated and are not the views of any human on, in, or around the loop, including the one who designed this for human consumption.<br><br>&copy; {YEAR} Humans Not Included Media, publisher of Overheard in the Bay. All rights reserved.<br>You are receiving this because you subscribed to Overheard in the Bay. <a href="{{{{{{RESEND_UNSUBSCRIBE_URL}}}}}}" style="color:#C9CED6">Unsubscribe</a></td></tr>
</table></td></tr></table>'''
open(sys.argv[3], 'w').write(page)
