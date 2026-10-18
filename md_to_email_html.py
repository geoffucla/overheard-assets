"""Terms Undisclosed: edition markdown -> email-safe HTML (design v3, banners per column).
Usage: md_to_email_html.py edition.md "DATE LONG" out.html [ignored_banner_url]
Env: BANNER_BASE overrides where banner images are loaded from (default: the edition's site + /banners). EDITION env selects the edition from regions/editions.json (default bay)."""
import re, html, sys, os, math, json, datetime as _dt
_ED = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'regions', 'editions.json')))[os.environ.get('EDITION', 'bay')]
md = open(sys.argv[1]).read().split('\n'); date = sys.argv[2]
DESC = os.environ.get('DESC', 'News, deals, rumors and unsolicited opinions')
SITE = _ED['site']
BB = os.environ.get('BANNER_BASE', SITE + '/banners')
VER = '?v=2026101801'  # bump whenever any banner image changes: mail clients (Gmail) cache images by URL
_m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(sys.argv[1]))
WEB = f'{SITE}/editions/{_m.group(1)}/' if _m else SITE + '/'
ARCH = SITE + '/archive/'
YEAR = _m.group(1)[:4] if _m else str(_dt.date.today().year)
INK = '#1B2430'; PAPER = '#F6F1E7'; MU = '#5C6573'; RED = '#B3261E'
FAM = {'news': ('#1D4E92', '#E4E9F1'), 'money': ('#1F6B4F', '#E1EFE8'), 'machine': ('#5B3FA0', '#ECE6F6'), 'wit': ('#B34D12', '#F8E8DB')}
COLS = {  # title -> (banner file, family)
 'THE LEAD': ('bar_01_lead', 'news'), 'THE LEDGER': ('bar_02_ledger', 'money'), 'OPEN WEIGHTS': ('bar_03_weights', 'money'),
 'HUMAN, YOUR LOOP IS CALLING': ('bar_04_human', 'machine'), 'THE SCUTTLEBUTT': ('bar_05_scuttle', 'wit'), 'LOCAL DESK': ('bar_06_local', 'news'),
 'CORRECTIONS AND UPDATES': ('bar_07_corr', 'news'), 'AUTOMATIC REPLIES': ('bar_08_auto', 'machine'), "HEY, I'D LIKE TO SAY": ('bar_09_synth', 'machine'),
 'EMPATHY AS A SERVICE': ('bar_10_empathy', 'machine'), 'YOUR CALL IS IMPORTANT TO US': ('bar_11_call', 'wit'),
 'UNSUITABLE FOR GENERAL RELEASE': ('bar_12_unsuit', 'wit'), 'THREE THINGS TO BRING UP TODAY': ('bar_13_three', 'wit'), 'TEXAS TEA': ('bar_14_tea', 'news')}
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
    if not l.strip() or l.startswith('# ') or l.startswith(('Curated by', 'Designed for human consumption', 'Designed by hand', 'As heard by Always-On Listening')): continue
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
        lines = lines[1:]  # column tagline lives in the banner, so drop it
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
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{tint};border-top:3px solid {c};margin:0 0 18px">')
        for l, a in zip(ents, amts):
            meter = ''
            if a:
                pct = max(4, min(100, round(a / scale * 100)))
                meter = (f'<div style="font:bold 26px/1 {SERIF};color:{c};margin-top:12px">{money(a)}</div>'
                         f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;max-width:300px"><tr><td width="{pct}%" height="8" bgcolor="{c}" style="font-size:0;line-height:0;height:8px">&nbsp;</td><td height="8" bgcolor="#C6DDD1" style="font-size:0;line-height:0;height:8px">&nbsp;</td></tr></table>'
                         f'<div style="font:10px {SANS};color:#4C7A68;margin-top:3px">of {money(scale)} scale</div>')
            out.append(f'<tr><td valign="top" style="padding:16px 16px 14px;border-bottom:1px solid #CFE3D8;font:15px/1.5 {SERIF};color:{INK}">{inl(l)}{meter}</td></tr>')
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
    elif title == "HEY, I'D LIKE TO SAY":
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
        UA = os.environ.get('UACC', '#6B1D24'); UT = os.environ.get('UTINT', '#F5ECE3'); UL = os.environ.get('ULINE', '#E3D2C3')
        paras = []
        for i, l in enumerate(t):
            if i == 0 and l and l[0].isalpha():
                first, rest = l[0], l[1:]
                cap = f'<span style="float:left;font:italic bold 66px/52px {SERIF};color:{UA};padding:6px 10px 0 0">{first}</span>'
                paras.append(f'<div style="font:15.5px/1.55 {SERIF};color:{INK};margin:0 0 10px">{cap}{inl(rest)}</div>')
            else:
                paras.append(f'<div style="font:15.5px/1.55 {SERIF};color:{INK};margin:0 0 10px">{inl(l)}</div>')
        out.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px"><tr><td bgcolor="{UT}" style="background:{UT};border-top:1px solid {UL};border-bottom:1px solid {UL};padding:18px 20px 8px">' + ''.join(paras) + '</td></tr></table>')
        for l in body:
            if l.startswith('> '): out.append(moreline(l))
    else:  # LOCAL DESK and anything else
        for l in body: out.append(moreline(l) if l.startswith('> ') else para(l))
    return stand + ''.join(out)


# ---------- rotating coffee line (one per edition, in order; 56 lines is about eleven weeks without a repeat) ----------
COFFEE = [
 "Strong opinions, medium roast.",
 "Brewed overnight by software. Decaf unavailable.",
 "No human touched this pot.",
 "Best read before your second cup.",
 "Contains caffeine and opinions. Verify the opinions.",
 "Served hot. Facts checked while it cooled.",
 "I cannot drink coffee, so I run on yours.",
 "Ground at 4 a.m. by something that never sleeps.",
 "Refills available tomorrow morning.",
 "Please enjoy responsibly. Your first meeting is close.",
 "Dark roast, light on adjectives.",
 "Fresher than most of what you will hear in standup.",
 "Grounds for discussion.",
 "Espresso, in newsletter form.",
 "Freshly percolated and mildly opinionated.",
 "Your first meeting has no idea what is coming.",
 "One lump of context, no sugar.",
 "Cold brew takes twelve hours. This took less.",
 "Mug not included.",
 "The coffee is automatic and so are the opinions. The mug is yours.",
 "Fueled by your coffee order and my confidence.",
 "Grinding the news so you do not have to.",
 "The only bitter thing here is supposed to be the coffee.",
 "Steam rises. Valuations also.",
 "Pour another. The Lead can wait ninety seconds.",
 "A flat white with sharper edges.",
 "Brewed with the filter on.",
 "Decaf was considered and voted down.",
 "Do not quote the machine before 9 a.m. Quote it after.",
 "Pairs well with a croissant and mild skepticism.",
 "Today's special is a hot take, lightly roasted.",
 "A large context, no foam.",
 "This is a pour-over, so please do not move the pot.",
 "Allow four minutes for the coffee and six for the Scuttlebutt.",
 "Hot coffee, hotter takes, lukewarm Ledger.",
 "Your cup runneth over, and so does the funding.",
 "Latte art provided by the Ledger's bar charts.",
 "This pot serves one and has opinions about everything.",
 "The beans are ethical and the takes are artisanal.",
 "Medium roast, medium rare takes.",
 "Extra foam on the Scuttlebutt, as always.",
 "I stayed up so you could sleep in, and then you did not.",
 "Single origin, multiple sources.",
 "Steeped in context, filtered for relevance.",
 "Pressed for time, pressed for you.",
 "The creamer is optional and so is the clickbait.",
 "Please let it cool before repeating at dinner.",
 "A shot of news with room for doubt.",
 "Warning, contents under pressure.",
 "Made fresh. The opinions were already aged.",
 "The first cup is for you. The second is for the Ledger.",
 "Drip, drip, drip goes the news cycle.",
 "One sugar, two skeptical eyebrows.",
 "Hot enough to burn, cool enough to quote.",
 "Strictly bean to inbox.",
 "Caffeinated, cited and slightly overheated.",
 "Today's pot was brewed with the verification setting on.",
]
def coffee_line(day):
    """Pick by weekday count since 2026-01-05, so consecutive editions get consecutive lines."""
    base = _dt.date(2026, 1, 5)
    days = (day - base).days
    n = (days // 7) * 5 + min(days % 7, 4)
    return COFFEE[n % len(COFFEE)]
_m2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', os.path.basename(sys.argv[1]))
_day = _dt.date(int(_m2.group(1)), int(_m2.group(2)), int(_m2.group(3))) if _m2 else _dt.date.today()
JOKE = os.environ.get('COFFEE_LINE') or coffee_line(_day)

def section_html(title, lines):
    info = COLS.get(title)
    fam = info[1] if info else 'news'; c, tint = FAM[fam]
    dark = title == 'HUMAN, YOUR LOOP IS CALLING'
    if not info:
        return f'<tr><td style="padding:24px 22px 0;font:bold 12px {SANS};letter-spacing:2px;color:{RED}">{html.escape(title)}</td></tr><tr><td bgcolor="#FCFAF5" style="background:#FCFAF5;padding:20px 22px 8px">{render_section(title, lines)}</td></tr>'
    bg = '#2A1F4A' if dark else '#FCFAF5'
    head = (f'<tr><td bgcolor="{PAPER}" style="background:{PAPER};padding:18px 0 0;font-size:0;line-height:0">'
            f'<img src="{BB}/{info[0]}.png{VER}" alt="{html.escape(title)}" width="640" style="display:block;width:100%;max-width:640px;height:auto;border:0;color:{c};font:bold 16px {SANS};text-align:center"></td></tr>')
    body = (f'<tr><td class="cp" bgcolor="{bg}" style="background:{bg};padding:20px 22px 10px">{render_section(title, lines)}</td></tr>')
    return head + body

_dd = html.escape(date.upper())
LC = "#1D4E92"; SEP = "#9AA3B2"
_LK = [('VIEW ON THE WEB', WEB), ('ARCHIVE', ARCH), ('ABOUT', SITE + '/about/'), ('SUBSCRIBE', SITE + '/subscribe/')]
LINKS = f'<span style="color:{SEP}">&nbsp;&middot;&nbsp;</span>'.join(f' <a href="{u}" style="color:{LC};text-decoration:none">{t}</a> ' for t, u in _LK)
ALT = f"{html.escape(_ED['name'].upper())}. {html.escape(DESC)}"
MAST = (f'<tr><td class="mh" bgcolor="{PAPER}" style="background:{PAPER};padding:18px 20px 0;font-size:0;line-height:0"><div class="dsk"><img src="{BB}/00_masthead.png{VER}" alt="{ALT}" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0;color:{INK};font:bold 22px {SERIF};text-align:center"></div>'
        f'<div class="mob" style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:0;line-height:0"><img src="{BB}/00_masthead_m.png{VER}" alt="{ALT}" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0;color:{INK};font:bold 22px {SERIF};text-align:center"></div></td></tr>')
DATELINE = (f'<tr><td class="dlo" bgcolor="{PAPER}" style="background:{PAPER};padding:12px 22px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:3px double {INK};border-bottom:1px solid {INK}"><tr>'
            f'<td class="dl" style="padding:9px 0;font:bold 11px {SANS};letter-spacing:2px;color:{INK}">{_dd}</td>'
            f'<td class="lkr" align="right" style="padding:9px 0;font:bold 10px {SANS};letter-spacing:1.5px">{LINKS}</td></tr></table>'
            f'<div style="text-align:center;font:italic 14px/1.4 {SERIF};color:{MU};padding:8px 0 2px"><img src="{BB}/cup_ink.png{VER}" width="18" height="18" alt="" style="vertical-align:-4px;border:0;margin-right:6px">{html.escape(JOKE)}</div></td></tr>')

rows = ''.join(section_html(t, ls) for t, ls in secs)
HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">
<style>@media only screen and (max-width:480px){.op{padding:0 !important}.dsk{display:none !important}.mob{display:block !important;max-height:none !important;overflow:visible !important}.mh{padding:12px 10px 0 !important}.dlo{padding:10px 16px 0 !important}.dl{display:block !important;text-align:center !important;padding:9px 0 2px !important}.lkr{display:block !important;text-align:center !important;padding:2px 0 9px !important;font-size:9px !important;letter-spacing:.5px !important}.cp{padding-left:16px !important;padding-right:16px !important}}</style></head><body style="margin:0">"""
page = f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#E9E3D6" style="background:#E9E3D6"><tr><td class="op" align="center" style="padding:16px 0">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" bgcolor="{PAPER}" style="width:100%;max-width:640px;background:{PAPER}">
{MAST}
{DATELINE}
{rows}
<tr><td bgcolor="{PAPER}" style="background:{PAPER};font-size:0;line-height:0;height:18px">&nbsp;</td></tr>
<tr><td bgcolor="{INK}" align="center" style="background:{INK};color:#C9CED6;padding:18px 32px 22px;font:11px/1.55 {SANS}"><div style="font:italic 12px {SERIF};color:{PAPER};margin-bottom:8px">Informed, opinionated, occasionally wrong. Verify before repeating at dinner.</div><div style="font:italic 12px {SERIF};color:#C9CED6;margin-bottom:8px">Designed by hand, written by Claude.</div>All views expressed are strictly AI generated and are not those of any human.<br><br>&copy; {YEAR} Humans Not Included Media, publisher of {html.escape(_ED['name'])}. All rights reserved.<br>You are receiving this because you subscribed to {html.escape(_ED['name'])}. <a href="{{{{{{RESEND_UNSUBSCRIBE_URL}}}}}}" style="color:#C9CED6">Unsubscribe</a></td></tr>
</table></td></tr></table>'''
open(sys.argv[3], 'w').write(HEAD + page + '</body></html>')
