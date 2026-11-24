#!/usr/bin/env python3
"""Already-covered checker for Terms Undisclosed (Bay Blend and Texas Blend).

Usage:
  dedupe_check.py index HISTDIR [--days 14]
      Print a compact index of what the recent editions covered (date, column, first
      sentence, companies/names, money figures, links). Read it BEFORE researching.
  dedupe_check.py check FILE HISTDIR [--days 14] [--ed-days 60] [--themes themes.json] [--waivers FILE] [--out FILE]
      FILE is either the story pool (work/pool.md) or the assembled edition
      (work/SCUTTLEBUTT_YYYY-MM-DD.md). It is split into blocks (pool candidates, or the
      paragraphs of each column) and every block is compared with every earlier edition in
      HISTDIR (files named SCUTTLEBUTT_YYYY-MM-DD.md). Exit code 2 when a STRONG overlap has
      not been waived, 0 otherwise.

An overlap is STRONG when a block shares a link with an earlier edition, or shares two or more
distinctive names, or one distinctive name plus a money figure. It is WEAK when it shares a
single distinctive name. Names that appear in half or more of the earlier editions (Texas,
Dallas, Nvidia and so on) are treated as common and ignored.

A STRONG overlap is cleared only by a waiver line in the waivers file, of one of two kinds:
  KEY | NEW EVENT: what happened after the earlier item (a ruling, filing, deal, number, reversal,
  resignation or decision, with its date)
  KEY | FALSE POSITIVE: why the match is a coincidence of names, naming the two different things
  THEME-NAME | FRESH ANGLE: for a recurring-angle flag only, what makes this column's take a different
  argument from the earlier one (not just a different company)
KEY is any text found in the block label or its first 200 characters, such as the company name.
The reason must start with NEW EVENT or FALSE POSITIVE and be at least eight words. More detail, a new angle,
analyst reaction or a fresh quote about old facts is not a new event. Otherwise drop the block.
"""
import sys, re, os, glob, hashlib, datetime, collections

STOP = set("""The A An And Or But Of To In On At For With By From As Is Are Was Were Be Been It Its This That These
Those He She They We You I His Her Their Our Your Not No So If Then Than There Here Has Have Had Do Does Did Will
Would Can Could May Might Must About Into Over After Before Also Just More Most Some Any All Each Every Very Which
Who Whom What When Where Why How While Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February
March April May June July August September October November December Mon Tue Wed Thu Fri Sat Sun Jan Feb Mar Apr
Jun Jul Aug Sep Sept Oct Nov Dec According Meanwhile However Still Yet Now Today Yesterday Tomorrow Last Next New
Per One Two Three Four Five Six Seven Eight Nine Ten First Second Third Another Other Both Several Many Most Such
Inc Corp Corporation Company Co Ltd LLC LP Group Holdings Technologies Technology Systems Capital Partners
Ventures Fund Funds Advisers Advisors Energy Texas Dallas Austin Houston Fort Worth San Antonio Antonio America
American United States State U.S. US AI CEO CFO CTO IPO ERCOT Senate House Congress Court Federal Reuters
Bloomberg Source Sources Link Links Read Full Story Up Down Thing Things Lead Ledger Tea Open Weights Local Desk
Corrections Updates Automatic Replies Empathy Service Call Important Unsuitable General Release Hey Id Like Say
Scuttlebutt Human Loop Calling Blend Terms Undisclosed Designed Hand Written Claude Views Expressed Humans
County City Power Bank Banks Market Markets Data Center Centers Cloud Software Health Labs Lab Solutions Services Network Networks Industries Industry Plan Report Reports Gov Sen Rep Attorney General Parks Wildlife Tribune Monthly Newswire Business Wire Wire PR Finviz Hoodline Overheard Ask Location Withheld Money Read Source Register Journal Times Post Press Report Seed Series Round Funding Venture Growth Debt Equity Acquisition Merger Grant Loan IPO Link Included Media Verify Repeating Dinner Informed Opinionated Occasionally Wrong Hello World""".split())
STOP_L = {w.lower() for w in STOP}

COLUMNS = ["THE LEAD", "THE LEDGER", "TEXAS TEA", "OPEN WEIGHTS", "HUMAN, YOUR LOOP IS CALLING",
           "HUMAN YOUR LOOP IS CALLING", "THE SCUTTLEBUTT", "LOCAL DESK", "CORRECTIONS AND UPDATES",
           "AUTOMATIC REPLIES", "HEY, I'D LIKE TO SAY", "HEY I'D LIKE TO SAY", "EMPATHY AS A SERVICE",
           "YOUR CALL IS IMPORTANT TO US", "UNSUITABLE FOR GENERAL RELEASE",
           "THREE THINGS TO BRING UP TODAY", "SYNTHETIC REFLECTIONS"]
COLSET = {c.replace("’", "'") for c in COLUMNS}
FREE_COLUMNS = ("CORRECTIONS AND UPDATES",)
EDITORIAL = ("OPEN WEIGHTS", "HUMAN, YOUR LOOP IS CALLING", "HUMAN YOUR LOOP IS CALLING", "AUTOMATIC REPLIES",
             "HEY, I'D LIKE TO SAY", "HEY I'D LIKE TO SAY", "EMPATHY AS A SERVICE", "YOUR CALL IS IMPORTANT TO US",
             "THREE THINGS TO BRING UP TODAY", "SYNTHETIC REFLECTIONS")
THEME_COLUMNS = ("HUMAN, YOUR LOOP IS CALLING", "HUMAN YOUR LOOP IS CALLING", "AUTOMATIC REPLIES", "HEY, I'D LIKE TO SAY",
                 "HEY I'D LIKE TO SAY", "EMPATHY AS A SERVICE", "YOUR CALL IS IMPORTANT TO US", "SYNTHETIC REFLECTIONS")
# Recurring editorial angles. Each theme: name, window in days, regexes (case-insensitive).
# Overridden by a themes.json file in the assets repo when --themes is given.
THEMES = [{"name": "undated-promise", "days": 45, "patterns": [
    r"\b(no|without (a|any)|never (gave|named|set)|unspecified|did not (give|name|set)|didn't (give|name|set)|has not (given|named|set)|hasn't (given|named|set)|declined to (give|name|set))\b.{0,50}(?<!closing )\b(date|deadline|timeline|timetable|time frame|timeframe|delivery date|due date)\b",
    r"\bhold(s|ing)? (\w+ ){0,3}(accountable|to (it|that|its word))\b",
    r"\bundated\b", r"\bat some point\b", r"\bin due course\b", r"\bsomeday\b"]}]  # may revisit old stories, still reported

URL_RE = re.compile(r"https?://[^\s)>\]\"']+")
NAME_RE = re.compile(r"\b(?:[A-Z][A-Za-z0-9&'’\-]*|[A-Z]{2,})(?:\s+(?:[A-Z][A-Za-z0-9&'’\-]*|[A-Z]{2,}))*")
FIG_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s?(?:trillion|billion|million|thousand|bn|mm|[BMKT])?\b", re.I)


def norm_url(u):
    u = u.rstrip(".,;:")
    u = re.sub(r"^https?://(www\.)?", "", u.lower())
    u = u.split("?")[0].split("#")[0].rstrip("/")
    return u


def norm_fig(f):
    f = re.sub(r"\s+", "", f.lower())
    f = f.replace("bn", "billion").replace("mm", "million")
    return re.sub(r"(\d)b$", r"\1billion", re.sub(r"(\d)m$", r"\1million", f))


def clean_line(s):
    s = re.sub(r"\[([^\]]*)\]\(([^)]*)\)", r"\1 \2", s)
    return s.replace("**", "").replace("__", "")


def names_in(text):
    out = set()
    for m in NAME_RE.finditer(text):
        toks = m.group(0).split()
        # trim stop words at both ends
        while toks and toks[0].lower() in STOP_L:
            toks = toks[1:]
        while toks and toks[-1].lower() in STOP_L:
            toks = toks[:-1]
        if not toks:
            continue
        if len(toks) == 1 and len(toks[0]) < 3:
            continue
        out.add(" ".join(toks).lower())
    return out


def subseqs(name):
    t = name.split()
    res = set()
    for i in range(len(t)):
        for j in range(i + 1, len(t) + 1):
            seg = t[i:j]
            if len(seg) == 1 and (seg[0] in STOP_L or len(seg[0]) < 3 or len(t) > 1):
                continue
            res.add(" ".join(seg))
    return res


def feats(text):
    names = set()
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">") and not re.match(r"^\s*\(?(source|sources|link|links|read more|the full story)\b", l, re.I))
    for n in names_in(body):
        names |= subseqs(n)
    return {
        "names": names,
        "urls": {norm_url(u) for u in URL_RE.findall(text)},
        "figs": {norm_fig(f) for f in FIG_RE.findall(text)},
    }


def split_sections(md):
    """Return list of (column, [paragraph, ...])."""
    secs, cur, buf = [], "(unsectioned)", []
    def flush():
        paras = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(buf)) if p.strip()]
        if paras:
            secs.append((cur, paras))
    for raw in md.splitlines():
        ln = raw.rstrip()
        head = re.sub(r"^#+\s*", "", ln).strip().strip("*").strip()
        up = head.upper().replace("’", "'")
        is_head = (ln.lstrip().startswith("#") and head and not up.startswith("TERMS UNDISCLOSED")) or up in COLSET
        if is_head and up in COLSET:
            flush(); buf = []; cur = up; continue
        if ln.lstrip().startswith("# ") and up.startswith("TERMS UNDISCLOSED"):
            continue
        buf.append(clean_line(ln))
    flush()
    return secs


def hist_files(hdir, days=None, today=None):
    files = sorted(glob.glob(os.path.join(hdir, "SCUTTLEBUTT_*.md")))
    out = []
    for f in files:
        m = re.search(r"SCUTTLEBUTT_(\d{4}-\d{2}-\d{2})", os.path.basename(f))
        if not m:
            continue
        d = datetime.date.fromisoformat(m.group(1))
        if days and today and (today - d).days > days:
            continue
        out.append((d, f))
    return out


def load_hist(hdir, days=None, today=None):
    eds = []
    for d, f in hist_files(hdir, days, today):
        md = open(f, encoding="utf-8", errors="replace").read()
        blocks = []
        for col, paras in split_sections(md):
            for p in paras:
                blocks.append({"col": col, "text": p, **feats(p)})
        eds.append({"date": d, "file": f, "blocks": blocks, "names": set().union(*[b["names"] for b in blocks]) if blocks else set()})
    return eds


def common_names(eds):
    n = len(eds)
    if n < 3:
        return set()
    df = collections.Counter()
    for e in eds:
        for x in e["names"]:
            df[x] += 1
    return {x for x, c in df.items() if c >= max(2, 0.5 * n)}


def first_sentence(t, n=150):
    t = re.sub(r"\s+", " ", t)
    return t[:n] + ("..." if len(t) > n else "")


def load_themes(path):
    if path and os.path.exists(path):
        try:
            import json
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            print("WARNING: could not read themes file, using built-in themes")
    return THEMES


def cmd_index(hdir, days=14):
    eds = load_hist(hdir, days, datetime.date.today())
    if not eds:
        print("NO HISTORY FILES FOUND in", hdir)
        return 0
    print("# Already covered (editions read: %d, %s to %s)\n" % (len(eds), eds[0]["date"], eds[-1]["date"]))
    for e in reversed(eds):
        print("## %s" % e["date"])
        for b in e["blocks"]:
            if len(b["text"]) < 40:
                continue
            nm = sorted([x for x in b["names"] if " " in x or len(x) > 3])[:8]
            print("- [%s] %s" % (b["col"], first_sentence(b["text"], 140)))
        print()
    return 0


def parse_waivers(path):
    w = []
    if path and os.path.exists(path):
        for ln in open(path, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if "|" not in ln or ln.startswith("#"):
                continue
            k, r = [x.strip() for x in ln.split("|", 1)]
            rl = r.lower()
            if k and len(r.split()) >= 8 and ("new event" in rl or "false positive" in rl or "fresh angle" in rl):
                w.append((k.lower(), r))
    return w


def pool_blocks(md):
    lines = md.splitlines()
    starts = [i for i, l in enumerate(lines) if re.match(r"^#{1,4}\s+\S", l) and not l.lower().startswith("# story pool")]
    blocks = []
    if len(starts) >= 5:
        for a, b in zip(starts, starts[1:] + [len(lines)]):
            t = clean_line("\n".join(lines[a:b])).strip()
            blocks.append(("POOL", t))
    else:
        for p in re.split(r"\n\s*\n", md):
            p = clean_line(p).strip()
            if len(p) > 60:
                blocks.append(("POOL", p))
    return blocks


def cmd_check(path, hdir, days, waivers, out, ed_days=60, themes_path=None):
    md = open(path, encoding="utf-8", errors="replace").read()
    # today's date from the file name, else today
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    today = datetime.date.fromisoformat(m.group(1)) if m else datetime.date.today()
    all_eds = [e for e in load_hist(hdir, max(days, ed_days), today) if e["date"] < today or not m]
    eds = [e for e in all_eds if (today - e["date"]).days <= days] if m else all_eds
    themes = load_themes(themes_path)
    if os.path.basename(path).startswith("SCUTTLEBUTT_"):
        blocks = [(col, p) for col, paras in split_sections(md) for p in paras]
    else:
        blocks = pool_blocks(md)
    common = common_names(eds)
    wl = parse_waivers(waivers)
    lines = ["# Already-covered check", "",
             "File: %s. Earlier editions compared: %d%s." % (os.path.basename(path), len(eds),
                 (" (%s to %s)" % (eds[0]["date"], eds[-1]["date"])) if eds else ""), ""]
    if len(eds) < 3:
        lines += ["WARNING: fewer than 3 earlier editions were available. The history step probably failed or is thin. Say so in the run report.", ""]
    unresolved = 0
    nstrong = nweak = nwaived = 0
    for col, text in blocks:
        if len(text) < 40 or text.lstrip().startswith("~ "):
            continue
        f = feats(text)
        names = {n for n in f["names"] if n not in common}
        hits = []
        use = all_eds if col in EDITORIAL else eds
        for e in use:
            for hb in e["blocks"]:
                su = f["urls"] & hb["urls"]
                sn = names & {n for n in hb["names"] if n not in common}
                sf = f["figs"] & hb["figs"]
                # keep only maximal shared names
                sn = {n for n in sn if not any(n != o and n in o for o in sn)}
                if su or len(sn) >= 2 or (len(sn) >= 1 and sf):
                    lvl = "STRONG"
                elif len(sn) == 1:
                    lvl = "WEAK"
                else:
                    continue
                hits.append((lvl, e["date"], hb["col"], sorted(sn), sorted(sf), sorted(su), first_sentence(hb["text"], 160)))
        label = "%s / %s" % (col, first_sentence(text, 80))
        if col in THEME_COLUMNS:
            for th in themes:
                if any(re.search(p, text, re.I | re.S) for p in th["patterns"]):
                    for e in all_eds:
                        if (today - e["date"]).days > th["days"]:
                            continue
                        for hb in e["blocks"]:
                            if hb["col"] in THEME_COLUMNS and any(re.search(p, hb["text"], re.I | re.S) for p in th["patterns"]):
                                hits.append(("THEME", e["date"], hb["col"], [th["name"]], [], [], first_sentence(hb["text"], 160)))
        if not hits:
            continue
        strong = [h for h in hits if h[0] in ("STRONG", "THEME")]
        weak = [h for h in hits if h[0] == "WEAK"]
        key_text = (label + " " + text[:200] + " " + " ".join(h[3][0] for h in hits if h[0] == "THEME")).lower()
        waived = [r for k, r in wl if k in key_text]
        if strong and col in FREE_COLUMNS:
            status = "ALLOWED COLUMN (state the NEW EVENT in the item)"
        elif strong and waived:
            status = "WAIVED: " + waived[0]; nwaived += 1
        elif strong:
            status = "UNRESOLVED. Drop it, replace it, or add a waiver line with a real NEW EVENT"; unresolved += 1
        else:
            status = "weak only, check by eye"
        if strong: nstrong += 1
        elif weak: nweak += 1
        lines.append("## %s" % label)
        lines.append("Status: %s" % status)
        for h in (strong[:5] if strong else weak[:3]):
            if h[0] == "THEME":
                lines.append("- RECURRING ANGLE '%s' already used on %s [%s] (within its window). Pick a different angle or waive with a FRESH ANGLE line keyed to the theme name." % (h[3][0], h[1], h[2]))
            else:
                lines.append("- %s overlap with %s [%s]: names=%s figures=%s links=%s" % (h[0], h[1], h[2], ", ".join(h[3]) or "-", ", ".join(h[4]) or "-", ", ".join(h[5]) or "-"))
            lines.append("  earlier text: %s" % h[6])
        lines.append("")
    lines.insert(4, "Result: %d blocks with STRONG overlap (%d waived, %d unresolved), %d with weak overlap only." % (nstrong, nwaived, unresolved, nweak))
    lines.insert(5, "")
    rep = "\n".join(lines)
    if out:
        open(out, "w", encoding="utf-8").write(rep + "\n")
    print(rep)
    return 2 if unresolved else 0


def main(argv):
    if len(argv) < 3 or argv[1] not in ("index", "check"):
        print(__doc__); return 1
    if argv[1] == "index":
        return cmd_index(argv[2], int(argv[argv.index("--days") + 1]) if "--days" in argv else 14)
    path, hdir = argv[2], argv[3]
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    return cmd_check(path, hdir, int(opt("--days", 14)), opt("--waivers"), opt("--out"), int(opt("--ed-days", 60)), opt("--themes"))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
